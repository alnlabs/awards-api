FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app/app
COPY alembic.ini /app/
COPY alembic /app/alembic
COPY ./tests /app/tests
COPY pytest.ini /app/
