FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8030
HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8030/healthz', timeout=3)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8030"]
