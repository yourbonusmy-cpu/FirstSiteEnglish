FROM python:3.13-slim

# Системные зависимости для компиляции и работы PostgreSQL
RUN apt-get update && \
    apt-get install -y gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем зависимости и ставим их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .
RUN python -m spacy download en_core_web_sm

# Скачиваем NLTK ресурсы
RUN python -m nltk.downloader -d /usr/share/nltk_data \
    stopwords \
    punkt \
    wordnet \
    omw-1.4 \
    averaged_perceptron_tagger \
    averaged_perceptron_tagger_eng

# Указываем NLTK_DATA переменную окружения
ENV NLTK_DATA=/usr/share/nltk_data
