FROM python:3.12-slim-bookworm

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5100

CMD ["python3", "main.py"]
