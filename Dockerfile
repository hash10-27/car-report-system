FROM python:3.11

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ara \
    libreoffice \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:10000", "web_app:app"]
