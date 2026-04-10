# ingestion/views.py
import json

from better_profanity import profanity
from celery.result import AsyncResult
from django.db import transaction
from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from apps.dictionary.models import Word
from apps.lists.models import SubtitleList, SubtitleListWord
from apps.ingestion.services.phrasal_extractor import get_phrasal_extractor
from apps.ingestion.tasks import process_subtitle_task, save_subtitle_list_task

import redis

# Redis client
# r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
import os

r = redis.from_url(os.environ.get("REDIS_URL"))
PREVIEW_TTL = 3600

extractor = get_phrasal_extractor()


def save_cancel(request):
    task_id = request.POST.get("task_id")
    if task_id:
        r.set(f"save_cancel:{task_id}", "1", ex=3600)
    return JsonResponse({"status": "cancelled"})


class SubtitleAddView(TemplateView):
    template_name = "ingestion/subtitle_add_fix.html"


@method_decorator(csrf_exempt, name="dispatch")
class SubtitleStartView(View):
    def post(self, request):
        raw_file = request.FILES.get("subtitle_file")
        raw_text = request.POST.get("subtitle_text", "")

        if raw_file:
            text = raw_file.read().decode("utf-8", errors="ignore")
        else:
            text = raw_text

        task = process_subtitle_task.delay(text, request.user.id)

        return JsonResponse({
            "status": "ok",
            "task_id": task.id
        })


@method_decorator(csrf_exempt, name="dispatch")
class SubtitleDeleteWordView(View):
    def post(self, request):
        task_id = request.POST.get("task_id")
        word_id = request.POST.get("word_id")

        if not task_id or not word_id:
            return JsonResponse({"status": "error"}, status=400)

        key = f"subtitle_preview:{task_id}"
        raw = r.get(key)

        if not raw:
            return JsonResponse({"status": "error"}, status=404)

        words = json.loads(raw)

        words = [w for w in words if str(w["id"]) != str(word_id)]

        r.setex(key, PREVIEW_TTL, json.dumps(words))

        return JsonResponse({
            "status": "ok",
            "total": len(words)
        })


@method_decorator(csrf_exempt, name="dispatch")
class SubtitleSaveView(View):
    MAX_IMAGE_SIZE = 2 * 1024 * 1024
    ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png", "image/webp"]

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"status": "error", "message": "Unauthorized"}, status=401
            )

        name = request.POST.get("subtitle_name", "").strip()
        task_id = request.POST.get("task_id")
        background_color = request.POST.get("background_color", "#ffffff")
        background_image = request.FILES.get("background_image")

        if not name or not task_id:
            return JsonResponse({"status": "error", "message": "Недостаточно данных"})

        if background_image:
            if background_image.content_type not in self.ALLOWED_CONTENT_TYPES:
                return JsonResponse(
                    {"status": "error",
                     "message": "Недопустимый формат файла. Разрешены: jpg, png, webp."},
                    status=400,
                )
            if background_image.size > self.MAX_IMAGE_SIZE:
                return JsonResponse(
                    {"status": "error",
                     "message": "Файл слишком большой. Максимальный размер — 2 МБ."},
                    status=400,
                )

        if profanity.contains_profanity(name):
            return JsonResponse(
                {"status": "error",
                 "message": "В названии списка недопустима ненормативная лексика"},
                status=400,
            )

        with transaction.atomic():
            subtitle_list = SubtitleList.objects.create(
                name=name,
                owner=request.user,
                background_color=(background_color if not background_image else "#ffffff"),
                background_image=background_image,
                quantity_words=0,
                quantity_words_frequencies=0,
                quantity_learned_words=0,
                quantity_learned_words_frequencies=0,
            )

        # 🚀 Запускаем Celery для сохранения слов
        celery_result = save_subtitle_list_task.delay(
            user_id=request.user.id,
            list_id=subtitle_list.id,
            task_id=task_id,
        )

        return JsonResponse(
            {
                "status": "ok",
                "save_task_id": celery_result.id,
                "list_id": subtitle_list.id,
            }
        )


class SubtitleSaveProgressView(View):
    def get(self, request):
        task_id = request.GET.get("task_id")
        if not task_id:
            return JsonResponse({"progress": -1})

        res = AsyncResult(task_id)

        if res.state == "PROGRESS":
            return JsonResponse({
                "percent": res.info.get("percent", 0)
            })
        elif res.state == "SUCCESS":
            return JsonResponse({"percent": 100})
        elif res.state in {"FAILURE", "REVOKED"}:
            return JsonResponse({"percent": -1})

        return JsonResponse({"percent": 0})


@method_decorator(csrf_exempt, name="dispatch")
class SubtitleSaveCancelView(View):
    def post(self, request):
        task_id = request.POST.get("task_id")
        if not task_id:
            return JsonResponse({"status": "error"})

        r.set(f"save_cancel:{task_id}", "1", ex=3600)
        AsyncResult(task_id).revoke(terminate=True)

        return JsonResponse({"status": "ok"})