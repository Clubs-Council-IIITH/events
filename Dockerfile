FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11-slim

EXPOSE 80

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /app