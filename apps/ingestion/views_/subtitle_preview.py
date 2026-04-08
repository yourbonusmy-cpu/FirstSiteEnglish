import json
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator

from apps.lists.models import SubtitleList, SubtitleListWord
from apps.dictionary.models import Word
from apps.ingestion.services.phrasal_extractor import get_phrasal_extractor

extractor = get_phrasal_extractor()


def filter_words_in_db(words_dict: dict[str, int]) -> list[dict]:
    word_names = words_dict.keys()
    db_words = Word.objects.filter(name__in=word_names)
    filtered = [
        {
            "id": w.id,
            "name": w.name,
            "frequency": words_dict[w.name],
        }
        for w in db_words
    ]
    # добавляем temp_id для JS
    for idx, w in enumerate(filtered):
        w["temp_id"] = f"temp-{idx}"
    return filtered


@method_decorator(csrf_exempt, name="dispatch")
class SubtitleStartView(View):
    def post(self, request):
        raw_file = request.FILES.get("subtitle_file")
        raw_text = request.POST.get("subtitle_text", "")
        if raw_file:
            text = raw_file.read().decode("utf-8")
        else:
            text = raw_text

        words_dict = extractor.extract(text)
        filtered_words = filter_words_in_db(words_dict)

        request.session["subtitle_preview_words"] = filtered_words
        request.session.modified = True

        return JsonResponse({"status": "ok"})


class SubtitlePageView(View):
    PAGE_SIZE = 50

    def get(self, request):
        words = request.session.get("subtitle_preview_words", [])
        page_number = int(request.GET.get("page", 1))
        paginator = Paginator(words, self.PAGE_SIZE)
        page = paginator.get_page(page_number)
        return JsonResponse(
            {
                "words": list(page.object_list),
                "has_next": page.has_next(),
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class SubtitleSaveView(View):
    def post(self, request):
        user = request.user
        name = request.POST.get("subtitle_name", "").strip()
        background_color = request.POST.get("background_color", "#ffffff")
        preview_words = request.session.get("subtitle_preview_words", [])

        if not name or not preview_words:
            return JsonResponse(
                {"status": "error", "message": "Нет слов или название не указано"}
            )

        subtitle_list = SubtitleList.objects.create(
            name=name,
            owner=user,
            background_color=background_color,
            quantity_words=len(preview_words),
            quantity_words_frequencies=sum(w["frequency"] for w in preview_words),
        )

        for w in preview_words:
            SubtitleListWord.objects.create(
                subtitle_list=subtitle_list, word_id=w["id"], frequency=w["frequency"]
            )

        # удаляем preview из сессии
        if "subtitle_preview_words" in request.session:
            del request.session["subtitle_preview_words"]
            request.session.modified = True

        return JsonResponse(
            {"status": "ok", "redirect_url": f"/lists/{subtitle_list.id}/"}
        )


@method_decorator(csrf_exempt, name="dispatch")
class SubtitleDeleteWordView(View):
    def post(self, request):
        temp_id = request.POST.get("temp_id")
        words = request.session.get("subtitle_preview_words", [])
        words = [w for w in words if w.get("temp_id") != temp_id]
        request.session["subtitle_preview_words"] = words
        request.session.modified = True
        return JsonResponse({"status": "ok"})
