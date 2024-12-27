# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    FLASK_APP=app.py

EXPOSE 5000

# Run flask directly
CMD ["flask", "run", "--host=0.0.0.0"]