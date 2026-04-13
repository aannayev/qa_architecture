FROM python:3.12-slim AS runtime
WORKDIR /app

RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir "fastapi>=0.115" "uvicorn[standard]>=0.32"

COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
