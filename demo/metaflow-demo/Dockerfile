FROM python:3.10-slim-bullseye

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY flow.py .
COPY config.yaml .

ENTRYPOINT ["python", "flow.py"]
