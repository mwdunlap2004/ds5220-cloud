FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN adduser --disabled-password --gecos "" --uid 10001 bot

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

USER bot

CMD ["python", "-u", "app.py"]
