FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Tailwind CSS'i derleme zamanında oluştur — container başlatılırken tekrar çalıştırılmaz
RUN python -m pytailwindcss \
    -i static/css/tailwind-input.css \
    -o static/css/tailwind.css \
    --minify

RUN mkdir -p /app/staticfiles /app/media \
    && sed -i 's/\r$//' entrypoint.sh \
    && chmod +x entrypoint.sh

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
