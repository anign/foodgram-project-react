FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip3 install --upgrade pip  --no-cache-dir

RUN pip3 install -r /app/requirements.txt --no-cache-dir

COPY . .

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000" ]