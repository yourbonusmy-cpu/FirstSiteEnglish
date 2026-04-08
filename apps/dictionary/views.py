from django.db.models import Exists, OuterRef, Case, When, Value, IntegerField
from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Prefetch
from django.core.paginator import Paginator

from apps.dictionary.models import Word, WordPartOfSpeech

PAGE_SIZE = 50


def dictionary_view(request):
    return render(request, "dictionary/dictionary.html")


def dictionary_api(request):
    page = int(request.GET.get("page", 1))
    q = request.GET.get("q", "").strip()

    qs = (
        Word.objects.all()
        .prefetch_related(
            Prefetch(
                "word_parts",
                queryset=WordPartOfSpeech.objects.select_related(
                    "part_of_speech"
                ).prefetch_related("translations"),
            )
        )
        .order_by("name")
    )

    if q:
        qs = (
            qs.filter(name__icontains=q)
            .annotate(
                relevance=Case(
                    When(name__iexact=q, then=Value(0)),
                    When(name__istartswith=q, then=Value(1)),
                    When(name__icontains=q, then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField(),
                )
            )
            .order_by("relevance", "name")
        )

    paginator = Paginator(qs, PAGE_SIZE)
    page_obj = paginator.get_page(page)

    results = []

    for word in page_obj:
        results.append(
            {
                "id": word.id,
                "name": word.name,
                "transcription": word.transcription,
                "word_parts": [
                    {
                        "is_main": wp.is_main,
                        "part_of_speech": {
                            "name": wp.part_of_speech.name,
                        },
                        "translations": [
                            {
                                "translation": t.translation,
                                "is_main": t.is_main,
                            }
                            for t in wp.translations.all()
                        ],
                    }
                    for wp in word.word_parts.all()
                ],
            }
        )

    return JsonResponse(
        {
            "results": results,
            "has_next": page_obj.has_next(),
        }
    )
