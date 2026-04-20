FROM python:3.12-slim

WORKDIR /app
COPY apps/demo-api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/demo-api /app
COPY apps/demo-web /app/apps/demo-web
COPY apps/public-docs /app/apps/public-docs
COPY data /app/data

ENV PORT=8000
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
