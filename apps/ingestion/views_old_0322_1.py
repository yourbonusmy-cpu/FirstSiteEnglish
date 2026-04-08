# ingestion/views.py
import json

from better_profanity import profanity
from celery.worker.control import revoke
from django.db import transaction
from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator

from apps.dictionary.models import Word
from apps.lists.models import SubtitleList, SubtitleListWord
from apps.ingestion.services.phrasal_extractor import get_phrasal_extractor
from apps.ingestion.tasks import process_subtitle_task, save_subtitle_list_task
from celery.result import AsyncResult
import redis

# Redis client (настрой под свой Redis)
r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
PREVIEW_TTL = 3600  # 1 час

extractor = get_phrasal_extractor()


def filter_words_in_db(words_dict: dict[str, int]) -> list[dict]:
    """
    Берём только слова, которые уже есть в БД
    """
    word_names = words_dict.keys()
    db_words = Word.objects.filter(name__in=word_names)

    result = []
    for idx, w in enumerate(db_words):
        result.append(
            {
                "id": w.id,
                "name": w.name,
                "frequency": words_dict[w.name],
            }
        )
    return result


def save_cancel(request):
    task_id = request.POST.get("task_id")
    print("CANCEL TASK ID:", task_id)
    if task_id:
        r.set(f"save_cancel:{task_id}", "1", ex=3600)
    return JsonResponse({"status": "cancelled"})


# ===========================
# Страница добавления субтитров
# ===========================
class SubtitleAddView(TemplateView):
    template_name = "ingestion/subtitle_add_fix.html"


# ===========================
# Загрузка текста / файла → запуск Celery
# ===========================
@method_decorator(csrf_exempt, name="dispatch")
class SubtitleStartView(View):
    def post(self, request):
        raw_file = request.FILES.get("subtitle_file")
        raw_text = request.POST.get("subtitle_text", "")

        if raw_file:
            text = raw_file.read().decode("utf-8", errors="ignore")
        else:
            text = raw_text

        # Запуск Celery задачи
        task = process_subtitle_task.apply_async(args=[text])
        task_id = task.id

        # Инициализируем пустой Redis preview
        r.set(f"subtitle_preview:{task_id}", json.dumps([]), ex=PREVIEW_TTL)

        return JsonResponse({"status": "ok", "task_id": task_id})


# ===========================
# Проверка прогресса
# ===========================
class SubtitleProgressView(View):
    def get(self, request):
        task_id = request.GET.get("task_id")
        if not task_id:
            return JsonResponse({"progress": -1})

        async_result = AsyncResult(task_id)
        state = async_result.state

        if state == "PROGRESS":
            percent = async_result.info.get("percent", 0)
        elif state == "SUCCESS":
            percent = 100

            words = async_result.result or []

            words_key = f"subtitle:{task_id}:words"
            order_key = f"subtitle:{task_id}:order"
            total_key = f"subtitle:{task_id}:total"

            pipe = r.pipeline()

            pipe.delete(words_key, order_key, total_key)

            for w in words:
                wid = str(w["id"])
                pipe.hset(words_key, wid, json.dumps(w))
                pipe.rpush(order_key, wid)

            pipe.set(total_key, len(words))

            pipe.expire(words_key, PREVIEW_TTL)
            pipe.expire(order_key, PREVIEW_TTL)
            pipe.expire(total_key, PREVIEW_TTL)

            pipe.execute()
        elif state == "FAILURE":
            percent = -1
        else:
            # PENDING / REVOKED / UNKNOWN
            percent = 0

        return JsonResponse({"progress": percent})


# ===========================
# Пагинация preview из Redis
# ===========================
class SubtitlePageView(View):
    PAGE_SIZE = 50

    def get(self, request):
        task_id = request.GET.get("task_id")
        if not task_id:
            return JsonResponse({"words": [], "has_next": False, "total": 0})

        page = int(request.GET.get("page", 1))

        order_key = f"subtitle:{task_id}:order"
        words_key = f"subtitle:{task_id}:words"
        total_key = f"subtitle:{task_id}:total"

        start = (page - 1) * self.PAGE_SIZE
        end = start + self.PAGE_SIZE - 1

        ids = r.lrange(order_key, start, end)

        words = []
        if ids:
            raw = r.hmget(words_key, ids)
            words = [json.loads(w) for w in raw if w]

        total = int(r.get(total_key) or 0)

        return JsonResponse({
            "words": words,
            "has_next": end + 1 < total,
            "total": total
        })





# ===========================
# Сохранение списка
# ===========================
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
                    {
                        "status": "error",
                        "message": "Недопустимый формат файла. Разрешены: jpg, png, webp.",
                    },
                    status=400,
                )

            if background_image and background_image.size > self.MAX_IMAGE_SIZE:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Файл слишком большой. Максимальный размер — 2 МБ.",
                    },
                    status=400,
                )

        if profanity.contains_profanity(name):
            return JsonResponse(
                {
                    "status": "error",
                    "message": "В названии списка недопустима ненормативная лексика",
                },
                status=400,
            )

        with transaction.atomic():

            subtitle_list = SubtitleList.objects.create(
                name=name,
                owner=request.user,
                background_color=(
                    background_color if not background_image else "#ffffff"
                ),
                background_image=background_image,
                quantity_words=0,
                quantity_words_frequencies=0,
                quantity_learned_words=0,
                quantity_learned_words_frequencies=0,
            )

        # 🚀 Запускаем Celery ТОЛЬКО для слов
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




@method_decorator(csrf_exempt, name="dispatch")
class SubtitleSaveCancelView(View):
    def post(self, request):
        task_id = request.POST.get("task_id")
        if not task_id:
            return JsonResponse({"status": "error"})

        # Ставим Redis-флаг
        r.set(f"save_cancel:{task_id}", "1", ex=3600)

        # Также можно попробовать прекратить процесс Celery
        AsyncResult(task_id).revoke(terminate=True)

        return JsonResponse({"status": "ok"})
