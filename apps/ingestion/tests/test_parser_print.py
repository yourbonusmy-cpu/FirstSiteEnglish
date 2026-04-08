import os
import django

# === Инициализация Django ===
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.ingestion.services.text_parser import TextParser

# === Путь к твоему файлу с субтитрами ===
srt_path = "fixtures/subtitles/mwe.srt"

with open(srt_path, "r", encoding="utf-8") as f:
    text = f.read()

parser = TextParser(text)
frequencies = parser.get_frequencies()

print("=== MWE и частоты ===")
for word, freq in frequencies.most_common():
    if len(word.split()) > 1:  # только фразы
        print(f"{word}: {freq}")

print("\n=== Все слова и фразы ===")
for word, freq in frequencies.most_common():
    print(f"{word}: {freq}")
