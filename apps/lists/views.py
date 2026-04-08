import json

from django.core.paginator import Paginator
from django.db.models import (
    Exists,
    OuterRef,
    Case,
    When,
    Value,
    IntegerField,
    Prefetch,
    Subquery,
    ExpressionWrapper,
    F,
)
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models.functions import Coalesce
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseForbidden

from apps.lists.models import SubtitleList, UserSubtitleList

from django.http import JsonResponse

from ..dictionary.models import Word, WordPartOfSpeech, Translation
from ..social.models import SubtitleListLike
from ..study.models import UserWordProgress

from tabulate import tabulate


@login_required
def download_words(request, list_id):
    ids = request.GET.get("ids", "")
    ids = [int(i) for i in ids.split(",") if i.isdigit()]

    subtitle_list = get_object_or_404(SubtitleList, id=list_id)

    # Получаем слова с предзагрузкой частей речи и переводов
    words = Word.objects.filter(
        id__in=ids, subtitle_lists=subtitle_list
    ).prefetch_related(
        "word_parts__part_of_speech",
        "word_parts__translations",
    )

    table = []

    for w in words:
        translation = ""
        # Сначала ищем основную часть речи
        main_word_part = w.word_parts.filter(is_main=True).first()
        if not main_word_part:
            main_word_part = w.word_parts.first()

        if main_word_part:
            # Ищем основной перевод для этой части речи
            main_tr = main_word_part.translations.filter(is_main=True).first()
            if main_tr:
                translation = main_tr.translation
            else:
                first_tr = main_word_part.translations.first()
                if first_tr:
                    translation = first_tr.translation

        table.append([w.name, w.transcription, translation])

    content = tabulate(
        table, headers=["WORD", "TRANSCRIPTION", "TRANSLATION"], tablefmt="plain"
    )

    filename = f"{subtitle_list.name}.words.txt"

    response = HttpResponse(content, content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def about(request):
    return render(request, "lists/about.html")


def gradient_text(request):
    return render(request, "lists/gradient_text.html")


def word_list_edit(request, list_id):
    return ""


def public_lists(request):
    qs = (
        SubtitleList.objects.filter(
            is_public=True,
            is_hide=False,
        )
        .select_related("owner")
        .prefetch_related("likes")
        .order_by("-modified_time")
    )

    if request.user.is_authenticated:
        qs = qs.annotate(
            is_liked=Exists(
                SubtitleListLike.objects.filter(
                    subtitle_list=OuterRef("pk"), user=request.user
                )
            )
        )
        # Получаем состояния пользователя
        user_states = UserSubtitleList.objects.filter(user=request.user)
        user_state_dict = {us.subtitle_list_id: us for us in user_states}

    else:
        qs = qs.annotate(
            is_liked=models.Value(False, output_field=models.BooleanField())
        )

    return render(
        request,
        "lists/lists.html",
        {
            "word_lists": qs,
            "is_public_page": True,
        },
    )


@login_required
def my_lists_react(request):
    return render(request, "lists/lists_api.html")


def my_lists(request):
    qs = (
        SubtitleList.objects.filter(owner=request.user)
        .select_related("owner")
        .order_by("-modified_time")
    )

    if request.user.is_authenticated:
        user_list_qs = UserSubtitleList.objects.filter(
            user=request.user,
            subtitle_list=OuterRef("pk"),
        )

        qs = qs.annotate(
            is_liked=Exists(
                SubtitleListLike.objects.filter(
                    subtitle_list=OuterRef("pk"),
                    user=request.user,
                )
            ),
            user_quantity_learned_words=Subquery(
                user_list_qs.values("quantity_learned_words")[:1],
                output_field=IntegerField(),
            ),
            progress_percent=ExpressionWrapper(
                100 * F("user_quantity_learned_words") / F("quantity_words"),
                output_field=IntegerField(),
            ),
        )

    return render(
        request,
        "lists/lists.html",
        {
            "word_lists": qs,
            "is_my_lists": True,
        },
    )


@login_required
@require_POST
def delete_list(request, list_id):
    subtitle_list = get_object_or_404(SubtitleList, id=list_id)

    # 🔐 проверка владельца
    if subtitle_list.owner != request.user:
        return JsonResponse({"error": "forbidden"}, status=403)

    subtitle_list.delete()
    return JsonResponse({"status": "ok"})


@receiver(post_delete, sender=SubtitleList)
def delete_background_image(sender, instance, **kwargs):
    if instance.background_image:
        instance.background_image.delete(save=False)


@receiver(pre_save, sender=SubtitleList)
def delete_old_image_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old = SubtitleList.objects.get(pk=instance.pk)
    except SubtitleList.DoesNotExist:
        return

    if old.background_image and old.background_image != instance.background_image:
        old.background_image.delete(save=False)


@login_required
@require_POST
def toggle_publish(request, pk):
    subtitle_list = get_object_or_404(SubtitleList, pk=pk)

    # ПРАВА ДОСТУПА
    if subtitle_list.owner != request.user and not request.user.is_staff:
        return HttpResponseForbidden()

    subtitle_list.is_public = not subtitle_list.is_public
    subtitle_list.save(update_fields=["is_public"])

    return JsonResponse({"is_public": subtitle_list.is_public})


@login_required
def word_lists(request):
    lists = SubtitleList.objects.filter(users=request.user).order_by("-modified_time")

    return render(request, "lists/word_lists.html", {"word_lists": lists})


def word_list_detail(request, list_id):
    word_list = get_object_or_404(SubtitleList, id=list_id)

    if not word_list.is_public:
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        if request.user != word_list.owner and not request.user.is_staff:
            return HttpResponseForbidden()

    progress_qs = UserWordProgress.objects.filter(
        user=request.user,
        word=OuterRef("pk"),
    )

    words_qs = (
        word_list.words.all()
        .annotate(
            position=F("subtitle_links__position"),
            is_known=Exists(progress_qs.filter(is_learned=True)),
            impressions=Coalesce(
                Subquery(progress_qs.values("impressions")[:1]),
                Value(0),
                output_field=IntegerField(),
            ),
            score=Coalesce(
                Subquery(progress_qs.values("score")[:1]),
                Value(0),
                output_field=IntegerField(),
            ),
        )
        .order_by("position")
        .prefetch_related(
            "word_parts__part_of_speech",
            "word_parts__translations",
        )
    )

    # --- серверный поиск ---
    search = request.GET.get("search")
    if search:
        words_qs = words_qs.filter(name__icontains=search)

    # --- фильтры ---
    if request.GET.get("hide_known") == "1":
        words_qs = words_qs.filter(is_known=False)

    if request.GET.get("only_known") == "1":
        words_qs = words_qs.filter(is_known=True)

    paginator = Paginator(words_qs, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # --- AJAX infinite scroll ---
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "lists/partials/word_rows.html",
            {"words": page_obj.object_list},
            request=request,
        )
        return JsonResponse(
            {
                "html": html,
                "has_next": page_obj.has_next(),
            }
        )

    return render(
        request,
        "lists/word_list_detail.html",
        {
            "word_list": word_list,
            "words": page_obj.object_list,
        },
    )


# def word_list_detail(request, list_id):
#     word_list = get_object_or_404(
#         SubtitleList.objects.prefetch_related(
#             'words__parts_of_speech__translations'
#         ),
#         id=list_id
#     )
#
#     if not word_list.is_public:
#         if not request.user.is_authenticated:
#             return HttpResponseForbidden()
#
#         if request.user != word_list.owner and not request.user.is_staff:
#             return HttpResponseForbidden()
#
#     return render(request, "lists/word_list_detail.html", {
#         "word_list": word_list
#     })


def get_translations(request, word_id):
    part_id = request.GET.get("part")
    translations = Translation.objects.filter(path_of_speech_id=part_id).values(
        "id", "translation", "is_main"
    )
    data = list(translations)
    # Переименуем ключ 'translation' в 'value' для JS
    for t in data:
        t["value"] = t.pop("translation")
    return JsonResponse(data, safe=False)
