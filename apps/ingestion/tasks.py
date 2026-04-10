import json
import os
import time

import redis
from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.db import transaction

from apps.dictionary.models import Word
from apps.lists.models import SubtitleListWord, SubtitleList
from apps.ingestion.services.phrasal_extractor import get_phrasal_extractor

extractor = get_phrasal_extractor()

r = redis.from_url(os.environ.get("REDIS_URL"))
channel_layer = get_channel_layer()
PREVIEW_TTL = 3600


def send_ws(user_id: int, payload: dict):
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "ingestion_event",  # ✅ ИСПРАВЛЕНО
            "data": payload,
        },
    )


# ================= PROCESS =================
@shared_task(bind=True)
def process_subtitle_task(self, text, user_id):
    freq_map = extractor.extract(text)

    words = list(freq_map.keys())
    db_words = Word.objects.filter(name__in=words)

    word_map = {w.name: w.id for w in db_words}
    filtered = [w for w in words if w in word_map]

    total = len(filtered)

    send_ws(user_id, {"type": "start", "percent": 0})

    preview = []

    for i, word in enumerate(filtered, 1):
        preview.append({
            "id": word_map[word],
            "name": word,
            "frequency": freq_map[word],
            "position": i,
        })

        if i % 20 == 0 or i == total:
            send_ws(user_id, {
                "type": "progress",
                "percent": int(i / total * 100)
            })

    # сохраняем preview
    task_id = self.request.id
    r.set(f"subtitle_preview:{task_id}", json.dumps(preview), ex=PREVIEW_TTL)

    send_ws(user_id, {"type": "words_chunk", "words": preview})
    send_ws(user_id, {"type": "done"})


@shared_task(bind=True)
def save_subtitle_list_task(self, *, user_id: int, list_id: int, task_id: str):

    preview_raw = r.get(f"subtitle_preview:{task_id}")
    if not preview_raw:
        send_ws(user_id, {"type": "save_error", "message": "preview expired"})

        return

    preview_words = json.loads(preview_raw)
    total = len(preview_words)

    subtitle_list = SubtitleList.objects.get(id=list_id)
    send_ws(user_id, {
        "type": "save_start",
        "percent": 0,
        "total": total,
        "name": subtitle_list.name
    })


    with transaction.atomic():
        batch = []

        for i, w in enumerate(preview_words, 1):

            batch.append(
                SubtitleListWord(
                    subtitle_list=subtitle_list,
                    word_id=w["id"],
                    frequency=w["frequency"],
                    position=w["position"],
                )
            )

            if len(batch) >= 50 or i == total:
                SubtitleListWord.objects.bulk_create(batch)
                batch.clear()

                percent = int(i / total * 100)
                send_ws(user_id, {
                    "type": "save_progress",
                    "percent": percent,
                })

                self.update_state(
                    state="PROGRESS",
                    meta={"percent": percent}
                )

        subtitle_list.quantity_words = total
        subtitle_list.status = "done"
        subtitle_list.save()

    r.delete(f"subtitle_preview:{task_id}")

    send_ws(user_id, {
        "type": "save_done",
        "percent": 100
    })

