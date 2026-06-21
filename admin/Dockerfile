FROM python:3.11-slim

WORKDIR /app

COPY admin/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY admin/ .

RUN mkdir -p data images

CMD gunicorn app:app --bind 0.0.0.0:${PORT:-8080}
