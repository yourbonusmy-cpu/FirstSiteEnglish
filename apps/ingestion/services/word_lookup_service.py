from apps.dictionary.models import Word


def lookup_existing_words(freq_map: dict[str, int]):
    names = list(freq_map.keys())

    words = Word.objects.filter(name__in=names).only("id", "name")

    result = []
    for w in words:
        result.append(
            {
                "id": w.id,
                "name": w.name,
                "frequency": freq_map[w.name],
            }
        )

    return result
