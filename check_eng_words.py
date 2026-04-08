import re
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer
import enchant
from wordfreq import zipf_frequency

# --- Настройка ---
lemmatizer = WordNetLemmatizer()
dictionary = enchant.Dict("en_US")

# --- Чтение списка слов ---
with open("db_backup/lists/wrong_words.txt", "r", encoding="utf-8") as f:
    words = [line.strip() for line in f if line.strip()]


def is_english_word(word, min_zipf=0.1):
    return zipf_frequency(word, "en") >= min_zipf


# --- Этап 1: ASCII-фильтр ---
ascii_passed = [word for word in words if re.fullmatch(r"[a-zA-Z]+", word)]
ascii_failed = [word for word in words if not re.fullmatch(r"[a-zA-Z]+", word)]
#
#
# # --- Этап 2: Spell-check через enchant ---
# enchant_passed = [word for word in words if dictionary.check(word)]
# enchant_failed = [word for word in words if not dictionary.check(word)]

# zipf_passed = []
# zipf_failed = []
# for word in words:
#     if is_english_word(word):
#         zipf_passed.append(word)
#     else:
#         zipf_failed.append(word)

# --- Этап 3: Lemma + WordNet ---
# wn_passed = []
# wn_failed = []
# for word in enchant_passed:
#     lemma = lemmatizer.lemmatize(word.lower())
#     if wn.synsets(lemma):
#         wn_passed.append(word)
#     else:
#         wn_failed.append(word)

# print(words.__len__())
# print("Слова, не прошедшие ASCII-фильтр (не a-zA-Z):")
# print(ascii_failed.__len__())
# print("Слова, не прошедшие enchant (из ASCII-прошедших):")
# print(enchant_failed.__len__())
# print("Слова, не прошедшие WordNet (из enchant-прошедших):")
# print(wn_failed.__len__())

# print("\nСлова, прошедшие ASCII-фильтр (не a-zA-Z):")
# print(ascii_passed.__len__())
# print("Слова, прошедшие enchant (из ASCII-прошедших):")
# print(enchant_passed.__len__())
# print("Слова, прошедшие WordNet (из enchant-прошедших):")
# print(wn_passed.__len__())
# print(words.__len__() - wn_passed.__len__())

for item in ascii_passed:
    print(item)
print(ascii_passed.__len__())

# count wrong words : 1118
