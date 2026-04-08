from better_profanity import profanity
from .services.sub_parser_nltk_1 import ConvertTextToSubtitleWords  # твой парсер
from apps.lists.models import SubtitleList, SubtitleListWord, UserSubtitleList
from django.views import View
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
import traceback
from .services.parser_subtitle_simple import ConvertTextToSubtitleWords
from apps.dictionary.models import Word
import uuid
import json
from django.http import JsonResponse
from .tasks import process_subtitle_task
from redis import Redis


from apps.lists.models import (
    SubtitleList,
    SubtitleListWord,
    UserSubtitleList,
)
from apps.dictionary.models import Word

redis_client = Redis(host="localhost", port=6379, db=0)


# ===============================
# START PROCESSING (Celery)
# ===============================
def start_subtitle_processing(request):
    if request.method == "POST":
        uploaded_file = request.FILES.get("subtitle_file")
        if not uploaded_file:
            return JsonResponse({"error": "Файл не загружен"}, status=400)

        # читаем текст из файла
        text = uploaded_file.read().decode("utf-8")

        # запускаем Celery задачу
        task = process_subtitle_task.delay(text)
        return JsonResponse({"task_id": task.id})
    return JsonResponse({"error": "Неверный метод"}, status=405)


# ===============================
# PROGRESS
# ===============================


def get_subtitle_progress(request):
    task_id = request.GET.get("task_id")
    if not task_id:
        return JsonResponse({"error": "task_id не указан"}, status=400)

    progress_key = f"subtitle:{task_id}:progress"
    meta_key = f"subtitle:{task_id}:meta"

    progress = redis_client.get(progress_key)
    progress = int(progress) if progress else 0

    meta = redis_client.hgetall(meta_key) or {}
    duration = float(meta.get("duration", 0))

    return JsonResponse(
        {
            "progress": progress,
            "duration": duration,
        }
    )


# ===============================
# RESULT (from Redis)
# ===============================
def get_subtitle_result(request):
    task_id = request.GET.get("task_id")

    result = redis_client.get(f"subtitle:{task_id}:result")

    if not result:
        return JsonResponse({"words": []})

    words = json.loads(result.decode())

    return JsonResponse({"words": words})


# ===============================
# CACHE RESULT INTO SESSION
# ===============================
def cache_subtitle_result(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    words_json = request.POST.get("words")
    if not words_json:
        return JsonResponse({"error": "No words provided"}, status=400)

    words = json.loads(words_json)

    request.session["subtitle_words_cache"] = words
    request.session["deleted_temp_ids"] = []

    return JsonResponse({"status": "ok"})


# ===============================
# PAGINATION
# ===============================
class SubtitleWordsPageView(LoginRequiredMixin, View):
    PAGE_SIZE = 50

    def get(self, request):
        page = int(request.GET.get("page", 1))

        words_cache = request.session.get("subtitle_words_cache", [])
        deleted_ids = request.session.get("deleted_temp_ids", [])

        words = [w for w in words_cache if w["temp_id"] not in deleted_ids]

        start = (page - 1) * self.PAGE_SIZE
        end = start + self.PAGE_SIZE

        return JsonResponse(
            {
                "words": words[start:end],
                "total_count": len(words),
            }
        )


# ===============================
# DELETE WORD
# ===============================
class DeleteSubtitleWordView(LoginRequiredMixin, View):
    def post(self, request):
        temp_id = request.POST.get("temp_id")
        if not temp_id:
            return JsonResponse({"error": "temp_id required"}, status=400)

        deleted = request.session.get("deleted_temp_ids", [])
        if temp_id not in deleted:
            deleted.append(temp_id)
            request.session["deleted_temp_ids"] = deleted

        return JsonResponse({"status": "ok"})


# ===============================
# SAVE LIST
# ===============================
class SaveSubtitleListView(LoginRequiredMixin, View):
    def post(self, request):
        subtitle_name = request.POST.get("subtitle_name", "").strip()
        background_color = request.POST.get("background_color", "#ffffff")
        background_image = request.FILES.get("background_image")

        words_cache = request.session.get("subtitle_words_cache", [])
        deleted_ids = request.session.get("deleted_temp_ids", [])
        words = [w for w in words_cache if w["temp_id"] not in deleted_ids]

        subtitle_list = SubtitleList.objects.create(
            name=subtitle_name,
            owner=request.user,
            background_color=background_color,
            background_image=background_image,
            quantity_words=len(words),
        )

        UserSubtitleList.objects.create(
            user=request.user,
            subtitle_list=subtitle_list,
        )

        for w in words:
            try:
                word = Word.objects.get(name=w["name"])
                SubtitleListWord.objects.create(
                    subtitle_list=subtitle_list,
                    word=word,
                    frequency=w["frequency"],
                )
            except Word.DoesNotExist:
                continue

        request.session.pop("subtitle_words_cache", None)
        request.session.pop("deleted_temp_ids", None)

        return JsonResponse(
            {
                "status": "ok",
                "redirect_url": reverse("lists:my_lists"),
            }
        )


class SubtitlePreviewView(LoginRequiredMixin, View):
    PAGE_SIZE = 50

    def post(self, request):
        try:
            file = request.FILES.get("subtitle_file")
            text = request.POST.get("subtitle_text", "").strip()

            if not file and not text:
                return JsonResponse(
                    {"error": "Не передан ни файл, ни текст"}, status=400
                )

            if file:
                try:
                    source_text = file.read().decode("utf-8")
                    subtitle_name = file.name
                except UnicodeDecodeError:
                    return JsonResponse(
                        {"error": "Файл должен быть в UTF-8"}, status=400
                    )
            else:
                source_text = text
                subtitle_name = None

            parser = ConvertTextToSubtitleWords(source_text)
            words_list = parser.to_dict()

            for idx, w in enumerate(words_list):
                w["temp_id"] = f"temp-{idx}"
                w.setdefault("transcription", "")
                w.setdefault("selected_pos", "")
                w.setdefault("selected_translation", "")
                w.setdefault("pos_list", [])
                w.setdefault("translations_for_pos", {})

            request.session["subtitle_words_cache"] = words_list
            request.session["deleted_temp_ids"] = []

            return JsonResponse(
                {
                    "subtitle_name": subtitle_name,
                    "total_count": len(words_list),
                }
            )

        except Exception as e:
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)


# class SubtitlePreviewView_OLD(LoginRequiredMixin, View):
#     def post(self, request):
#         file = request.FILES.get("subtitle_file")
#         text = request.POST.get("subtitle_text", "").strip()
#
#         source_text = None
#         subtitle_name = None
#
#         if file:
#             try:
#                 source_text = file.read().decode("utf-8")
#                 subtitle_name = file.name
#             except UnicodeDecodeError:
#                 return JsonResponse(
#                     {"error": "Не удалось прочитать файл. Используйте UTF-8"},
#                     status=400,
#                 )
#         elif text:
#             source_text = text
#
#         else:
#             return JsonResponse({"error": "Не передан ни файл, ни текст"}, status=400)
#
#         if not source_text.strip():
#             return JsonResponse({"error": "Пустой текст для обработки"}, status=400)
#
#         try:
#             parser = ConvertTextToSubtitleWords(source_text)
#             words_list = parser.to_dict()
#         except Exception as e:
#             return JsonResponse({"error": f"Ошибка обработки: {str(e)}"}, status=500)
#
#         return JsonResponse({"subtitle_name": subtitle_name, "words": words_list})

# class SaveSubtitleListView(LoginRequiredMixin, View):
#     MAX_IMAGE_SIZE = 2 * 1024 * 1024
#     ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png", "image/webp"]
#
#     def post(self, request):
#         data = request.POST
#         subtitle_name = data.get("subtitle_name")
#         background_color = request.POST.get("background_color", "#ffffff")
#         background_image = request.FILES.get("background_image")
#
#         if background_image:
#             if background_image.content_type not in self.ALLOWED_CONTENT_TYPES:
#                 return JsonResponse(
#                     {
#                         "status": "error",
#                         "message": "Недопустимый формат файла. Разрешены: jpg, png, webp.",
#                     },
#                     status=400,
#                 )
#
#             if background_image and background_image.size > self.MAX_IMAGE_SIZE:
#                 return JsonResponse(
#                     {
#                         "status": "error",
#                         "message": "Файл слишком большой. Максимальный размер — 2 МБ.",
#                     },
#                     status=400,
#                 )
#
#         if profanity.contains_profanity(subtitle_name):
#             return JsonResponse(
#                 {
#                     "status": "error",
#                     "message": "В названии списка недопустима ненормативная лексика",
#                 },
#                 status=400,
#             )
#
#         words_data = request.POST.getlist("words")
#
#         subtitle_list = SubtitleList.objects.create(
#             name=subtitle_name,
#             owner=request.user,
#             background_color=background_color,
#             background_image=background_image,
#             quantity_words=len(words_data),
#         )
#
#         UserSubtitleList.objects.create(user=request.user, subtitle_list=subtitle_list)
#
#         for w_str in words_data:
#             try:
#                 w = json.loads(w_str)
#                 word = Word.objects.get(name=w["name"])
#                 SubtitleListWord.objects.create(
#                     subtitle_list=subtitle_list, word=word, frequency=w["frequency"]
#                 )
#             except (json.JSONDecodeError, Word.DoesNotExist, KeyError):
#                 continue
#
#         return JsonResponse({"status": "ok", "redirect_url": reverse("lists:my_lists")})
