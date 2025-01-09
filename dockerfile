FROM python:3.11.11-slim-bookworm

COPY src/TSDAP /app
COPY requirements.txt /app/requirements.txt

WORKDIR /app

RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt

CMD ["python", "main.py"]
