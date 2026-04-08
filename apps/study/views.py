from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Case, When, IntegerField, Value
from django.db.models.functions import Lower
from django.http import HttpResponseForbidden, HttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.timezone import now
from django.views.generic import ListView
import json

from apps.dictionary.models import Word
from apps.lists.models import SubtitleList
from apps.study.models import UserWordProgress
from apps.study.services.progress import update_subtitle_list_progress
from apps.study.services.word_selection import (
    ensure_user_list_progress,
    get_words_json_for_test,
)

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.db import transaction

@login_required
def finish_study(request):
    return_to = request.session.pop("study_return_to", "/")
    return redirect(return_to)


@login_required
@require_POST
def word_impression(request):
    data = json.loads(request.body)
    word_text = data.get("word")

    try:
        word = Word.objects.get(name=word_text)
    except Word.DoesNotExist:
        return JsonResponse({"status": "not_found"}, status=404)

    uwp, _ = UserWordProgress.objects.get_or_create(
        user=request.user,
        word=word,
    )

    uwp.impressions += 1
    uwp.last_reviewed_at = now()
    uwp.save(update_fields=["impressions", "last_reviewed_at"])

    return JsonResponse({"status": "ok"})


@login_required
def word_mini_cards(request, list_id):
    word_list = get_object_or_404(SubtitleList, id=list_id)

    words = word_list.words.all()

    progress_qs = UserWordProgress.objects.filter(
        user=request.user,
        word__in=words,
    )

    progress_map = {p.word_id: p for p in progress_qs}

    return render(
        request,
        "study/word_mini_cards.html",
        {
            "word_list": word_list,
            "words": words,
            "progress_map": progress_map,
        },
    )


@login_required
def update_progress(request, pk):
    subtitle_list = SubtitleList.objects.get(pk=pk)

    learned_count = update_subtitle_list_progress(
        user=request.user,
        subtitle_list=subtitle_list,
    )

    total = subtitle_list.quantity_words
    percent = int((learned_count / total) * 100) if total else 0

    return JsonResponse(
        {
            "learned": learned_count,
            "total": total,
            "percent": percent,
        }
    )


@method_decorator(require_POST, name="dispatch")
class UpdateWordStateView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        word_id = request.POST.get("word_id")
        mode = request.POST.get("mode")  # learning | learned

        if not word_id or mode not in ("learning", "learned"):
            return JsonResponse(
                {"status": "error", "message": "invalid params"},
                status=400,
            )

        word = get_object_or_404(Word, id=word_id)

        with transaction.atomic():
            progress, _ = UserWordProgress.objects.get_or_create(
                user=request.user,
                word=word,
            )

            if mode == "learning":
                progress.is_learning = not progress.is_learning
                if progress.is_learning:
                    progress.is_learned = False

            elif mode == "learned":
                progress.is_learned = not progress.is_learned
                if progress.is_learned:
                    progress.is_learning = False

            progress.save(update_fields=["is_learning", "is_learned"])

        return JsonResponse(
            {
                "status": "ok",
                "state": {
                    "is_learning": progress.is_learning,
                    "is_learned": progress.is_learned,
                },
            }
        )


def word_mini_cards_(request, list_id):
    word_list = get_object_or_404(SubtitleList, id=list_id)

    if not word_list.is_public:
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        if request.user != word_list.owner and not request.user.is_staff:
            return HttpResponseForbidden()

    words = word_list.words.all()

    known_word_ids = set()
    if request.user.is_authenticated:
        known_word_ids = set(
            UserWordProgress.objects.filter(
                user=request.user, word__subtitle_lists=word_list
            ).values_list("word_id", flat=True)
        )

    return render(
        request,
        "study/word_mini_cards.html",
        {
            "word_list": word_list,
            "words": words,
            "known_word_ids": known_word_ids,
        },
    )


# class KnownWordsView(LoginRequiredMixin, ListView):
#     template_name = "study/known_word_mini_cards.html"
#     context_object_name = "known_words"
#     paginate_by = 30
#
#     def get_queryset(self):
#         return UserWordProgress.objects.filter(
#             user=self.request.user, is_learned=True
#         ).select_related("word")
class KnownWordsView(LoginRequiredMixin, ListView):
    template_name = "study/known_word_mini_cards.html"
    context_object_name = "known_words"
    paginate_by = 30

    def get_queryset(self):
        qs = UserWordProgress.objects.filter(
            user=self.request.user, is_learned=True
        ).select_related("word")

        search = self.request.GET.get("q")

        if search:
            search_lower = search.lower()

            qs = (
                qs.annotate(
                    priority=Case(
                        When(word__name__istartswith=search_lower, then=Value(0)),
                        When(word__name__icontains=search_lower, then=Value(1)),
                        default=Value(2),
                        output_field=IntegerField(),
                    )
                )
                .filter(word__name__icontains=search_lower)
                .order_by("priority", Lower("word__name"))
            )
        else:
            qs = qs.order_by(Lower("word__name"))

        return qs


class UploadKnownWordsView(LoginRequiredMixin, View):

    BATCH_SIZE = 1000

    @transaction.atomic
    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            messages.error(request, "Файл не выбран")
            return redirect("study:known_words")

        if file.size > 5 * 1024 * 1024:
            messages.error(request, "Файл слишком большой")
            return redirect("study:known_words")

        try:
            content = file.read().decode("utf-8")
        except UnicodeDecodeError:
            messages.error(request, "Файл должен быть UTF-8")
            return redirect("study:known_words")

        word_names = [w.strip() for w in content.splitlines() if w.strip()]

        if not word_names:
            messages.warning(request, "Файл пуст")
            return redirect("study:known_words")

        # Берём только существующие слова
        word_ids = list(
            Word.objects.filter(name__in=word_names).values_list("id", flat=True)
        )

        if not word_ids:
            messages.warning(request, "Ни одно слово не найдено в словаре")
            return redirect("study:known_words")

        user = request.user

        # =========================
        # 1️⃣ BULK CREATE батчами
        # =========================
        for i in range(0, len(word_ids), self.BATCH_SIZE):

            batch_ids = word_ids[i : i + self.BATCH_SIZE]

            to_create = [
                UserWordProgress(user=user, word_id=word_id) for word_id in batch_ids
            ]

            UserWordProgress.objects.bulk_create(
                to_create, ignore_conflicts=True, batch_size=self.BATCH_SIZE
            )

        # =========================
        # 2️⃣ BULK UPDATE батчами
        # =========================
        for i in range(0, len(word_ids), self.BATCH_SIZE):

            batch_ids = word_ids[i : i + self.BATCH_SIZE]

            UserWordProgress.objects.filter(user=user, word_id__in=batch_ids).update(
                is_learned=True, is_learning=False
            )

        messages.success(request, f"Импортировано слов: {len(word_ids)}")

        return redirect("study:known_words")


class DownloadKnownWordsView(LoginRequiredMixin, View):

    def get(self, request):
        words = UserWordProgress.objects.filter(
            user=request.user, is_learned=True
        ).select_related("word")

        content = "\n".join([w.word.name for w in words])

        response = HttpResponse(content, content_type="text/plain")
        response["Content-Disposition"] = 'attachment; filename="known_words.txt"'
        return response


class KnownWordsAjaxView(LoginRequiredMixin, View):

    def get(self, request):

        qs = UserWordProgress.objects.filter(
            user=request.user, is_learned=True
        ).select_related("word")

        search = request.GET.get("q")

        if search:
            search_lower = search.lower()

            qs = (
                qs.annotate(
                    priority=Case(
                        When(word__name__istartswith=search_lower, then=Value(0)),
                        When(word__name__icontains=search_lower, then=Value(1)),
                        default=Value(2),
                        output_field=IntegerField(),
                    )
                )
                .filter(word__name__icontains=search_lower)
                .order_by("priority", Lower("word__name"))
            )
        else:
            qs = qs.order_by(Lower("word__name"))

        paginator = Paginator(qs, 30)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        html = render_to_string(
            "study/partials/known_words_list.html",
            {"known_words": page_obj},
            request=request,
        )

        return JsonResponse({"html": html, "has_next": page_obj.has_next()})


class ToggleKnownWordView(LoginRequiredMixin, View):
    @transaction.atomic
    def post(self, request):
        word_id = request.POST.get("word_id")
        list_id = request.POST.get("list_id")

        if not word_id or not list_id:
            return JsonResponse({"status": "error"}, status=400)

        try:
            word_list = SubtitleList.objects.select_for_update().get(id=list_id)
            word = Word.objects.get(id=word_id)
        except (SubtitleList.DoesNotExist, Word.DoesNotExist):
            return JsonResponse({"status": "error"}, status=404)

        # ⚠️ защита: слово должно реально принадлежать списку
        if not word_list.words.filter(id=word.id).exists():
            return JsonResponse({"status": "error"}, status=403)

        known_qs = UserWordProgress.objects.filter(user=request.user, word=word)

        if known_qs.exists():
            # ❌ убираем "выученное"
            known_qs.delete()

            known_state = False
        else:
            # ✅ добавляем "выученное"
            UserWordProgress.objects.create(user=request.user, word=word)

        return JsonResponse(
            {
                "status": "ok",
            }
        )


@login_required
def study_words_view(request, list_id):
    """
    Страница изучения слов.
    JS ожидает words_json в старом формате — мы его сохраняем.
    """

    subtitle_list = get_object_or_404(
        SubtitleList,
        id=list_id,
        is_hide=False,
    )

    # 1️⃣ Гарантируем прогресс и слова
    ensure_user_list_progress(
        user=request.user,
        subtitle_list=subtitle_list,
    )

    # 2️⃣ Получаем слова под JS
    words_json = get_words_json_for_test(
        user=request.user,
        subtitle_list=subtitle_list,
        limit=20,
    )

    return render(
        request,
        "study/study.html",
        {
            "subtitle_list": subtitle_list,
            "words_json": words_json,
        },
    )


@login_required
def study_easy_3_words_view(request, list_id):
    referer = request.META.get("HTTP_REFERER", "/")
    if not referer:
        referer = "/"
    request.session["study_return_to"] = referer

    subtitle_list = get_object_or_404(
        SubtitleList,
        id=list_id,
        is_hide=False,
    )

    # 1️⃣ Гарантируем прогресс и слова
    ensure_user_list_progress(
        user=request.user,
        subtitle_list=subtitle_list,
    )

    # 2️⃣ Получаем слова под JS
    words_json = get_words_json_for_test(
        user=request.user,
        subtitle_list=subtitle_list,
        limit=20,
        with_all_translations=False,
        with_distractors=True,
    )

    return render(
        request,
        "study/study_easy_3.html",
        {
            "subtitle_list": subtitle_list,
            "words_json": words_json,
        },
    )


@login_required
def study_puzzle_words_view(request, list_id):
    """
    Страница изучения слов.
    JS ожидает words_json в старом формате — мы его сохраняем.
    """

    subtitle_list = get_object_or_404(
        SubtitleList,
        id=list_id,
        is_hide=False,
    )

    # 1️⃣ Гарантируем прогресс и слова
    ensure_user_list_progress(
        user=request.user,
        subtitle_list=subtitle_list,
    )

    # 2️⃣ Получаем слова под JS
    words_json = get_words_json_for_test(
        user=request.user,
        subtitle_list=subtitle_list,
        limit=20,
        with_all_translations=False,
        with_distractors=False,
    )

    return render(
        request,
        "study/study_puzzle_2.html",
        {
            "subtitle_list": subtitle_list,
            "words_json": words_json,
        },
    )


@login_required
def study_easy_words_view(request, list_id):
    """
    Страница изучения слов.
    JS ожидает words_json в старом формате — мы его сохраняем.
    """

    subtitle_list = get_object_or_404(
        SubtitleList,
        id=list_id,
        is_hide=False,
    )

    # 1️⃣ Гарантируем прогресс и слова
    ensure_user_list_progress(
        user=request.user,
        subtitle_list=subtitle_list,
    )

    # 2️⃣ Получаем слова под JS
    words_json = get_words_json_for_test(
        user=request.user,
        subtitle_list=subtitle_list,
        limit=20,
        with_all_translations=False,
        with_distractors=True,
    )

    return render(
        request,
        "study/study_easy.html",
        {
            "subtitle_list": subtitle_list,
            "words_json": words_json,
        },
    )


@login_required
def study_easy_2_words_view(request, list_id):
    subtitle_list = get_object_or_404(
        SubtitleList,
        id=list_id,
        is_hide=False,
    )

    # 1️⃣ Гарантируем прогресс и слова
    ensure_user_list_progress(
        user=request.user,
        subtitle_list=subtitle_list,
    )

    # 2️⃣ Получаем слова под JS
    words_json = get_words_json_for_test(
        user=request.user,
        subtitle_list=subtitle_list,
        limit=20,
    )

    return render(
        request,
        "study/study_easy_2.html",
        {
            "subtitle_list": subtitle_list,
            "words_json": words_json,
        },
    )


@login_required
@require_POST
def submit_answer(request):
    """
    Получает результат одного клика по варианту ответа.
    НЕ сохраняет варианты ответов.
    """

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    word_name = data.get("word")
    is_correct = data.get("is_correct")

    if word_name is None or is_correct is None:
        return JsonResponse({"error": "Missing data"}, status=400)

    word = get_object_or_404(Word, name=word_name)

    progress = get_object_or_404(
        UserWordProgress,
        user=request.user,
        word=word,
    )

    # 🔄 обновляем дату просмотра всегда
    progress.last_reviewed_at = timezone.now()

    # 🎯 логика score
    if is_correct:
        if progress.score < 4:
            progress.score += 1
    else:
        progress.score = max(0, progress.score - 1)

    progress.save(
        update_fields=[
            "score",
            "last_reviewed_at",
            "updated_at",
        ]
    )

    return JsonResponse({"ok": True, "score": progress.score})


def study_cards(request, list_id):
    subtitle_list = get_object_or_404(
        SubtitleList.objects.prefetch_related("words__parts_of_speech__translations"),
        id=list_id,
    )

    words = []

    for w in subtitle_list.words.all():

        # ВСЕ переводы (для проверки)
        all_translations = []

        for pos in w.parts_of_speech.all():
            all_translations.extend(
                pos.translations.values_list("translation", flat=True)
            )

        all_translations = list(set(t.strip().lower() for t in all_translations if t))

        # ОСНОВНОЙ перевод (для показа)
        main_translation = ""

        main_pos = w.parts_of_speech.filter(is_main=True).first()
        if main_pos:
            main_tr = main_pos.translations.filter(is_main=True).first()
            if main_tr:
                main_translation = main_tr.translation
            else:
                first_tr = main_pos.translations.first()
                if first_tr:
                    main_translation = first_tr.translation

        words.append(
            {
                "word": w.name,
                "transcription": w.transcription,
                "main_translation": main_translation,
                "all_translations": all_translations,
            }
        )

    return render(
        request,
        "study/study.html",
        {
            "subtitle_list": subtitle_list,
            "words_json": json.dumps(words, ensure_ascii=False),
        },
    )
