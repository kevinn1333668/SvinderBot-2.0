FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# зависимости отдельным слоем — кэшируется, пока requirements.txt не менялся
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# исходники и миграции
COPY src ./src
COPY main.py .
COPY alembic ./alembic
COPY alembic.ini .

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

RUN mkdir -p /app/logs
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

CMD ["./entrypoint.sh"]