import json
from time import sleep

import redis
from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.ingestion.services.phrasal_extractor import get_phrasal_extractor
from apps.dictionary.models import Word
from apps.lists.models import SubtitleListWord, SubtitleList

User = get_user_model()
extractor = get_phrasal_extractor()

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
PREVIEW_TTL = 3600
channel_layer = get_channel_layer()


@shared_task(bind=True)
def process_subtitle_task(self, text):
    freq_map = extractor.extract(text)
    ordered_words = []
    seen = set()

    for word in freq_map.keys():
        if word not in seen:
            seen.add(word)
            ordered_words.append(word)

    if not freq_map:
        return []

    db_words = Word.objects.filter(name__in=freq_map.keys()).only("id", "name")
    word_map = {w.name: w.id for w in db_words}
    filtered_words = [word for word in ordered_words if word in word_map]

    result = []
    total = len(filtered_words)

    for position, word in enumerate(filtered_words, start=1):
        result.append({
            "id": word_map[word],
            "name": word,
            "frequency": freq_map[word],
            "position": position,
        })

        if position % 20 == 0 or position == total:
            self.update_state(
                state="PROGRESS",
                meta={"current": position, "total": total, "percent": int(position / total * 100)}
            )

    # Сохраняем preview в Redis
    task_id = self.request.id
    r.set(f"subtitle_preview:{task_id}", json.dumps(result), ex=PREVIEW_TTL)

    return result


def send_ws(user_id: int, payload: dict):
    print("SEND WS:", payload)
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {"type": "save_progress", "data": payload},
    )


class CancelledError(Exception):
    pass


@shared_task(bind=True)
def save_subtitle_list_task(self, *, user_id: int, list_id: int, task_id: str):
    cancel_key = f"save_cancel:{task_id}"
    r.setnx(cancel_key, "0")
    r.expire(cancel_key, PREVIEW_TTL)

    preview_raw = r.get(f"subtitle_preview:{task_id}")
    if not preview_raw:
        send_ws(user_id, {"type": "error", "message": "preview expired"})
        return

    preview_words = json.loads(preview_raw)
    total = len(preview_words)

    send_ws(user_id, {"type": "start", "percent": 0, "total": total})
    subtitle_list = SubtitleList.objects.get(id=list_id)

    try:
        with transaction.atomic():
            batch = []

            for i, w in enumerate(preview_words, 1):

                if r.get(cancel_key) == "1":
                    raise CancelledError()

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

                    send_ws(user_id, {
                        "type": "progress",
                        "percent": int(i / total * 100),
                        "current": i,
                        "total": total,
                    })

            subtitle_list.quantity_words = total
            subtitle_list.quantity_words_frequencies = sum(w["frequency"] for w in preview_words)
            subtitle_list.save(update_fields=["quantity_words", "quantity_words_frequencies"])

        r.delete(f"subtitle_preview:{task_id}")
        r.delete(cancel_key)

        send_ws(user_id, {"type": "done", "list_id": subtitle_list.id, "percent": 100})
        return {"list_id": subtitle_list.id}

    except CancelledError:
        r.delete(cancel_key)
        subtitle_list.delete()
        send_ws(user_id, {"type": "error", "message": "cancelled"})
        return

    except Exception as exc:
        r.delete(cancel_key)
        subtitle_list.delete()
        send_ws(user_id, {"type": "error", "message": str(exc)})
        raise