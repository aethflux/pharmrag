FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-chi-sim \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501 8000

CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--browser.gatherUsageStats", "false"]
