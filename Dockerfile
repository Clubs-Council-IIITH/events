FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11-slim

EXPOSE 80

COPY . /app

RUN pip install -r requirements.txt
