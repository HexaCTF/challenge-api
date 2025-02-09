FROM python:3.10-slim-bullseye

RUN sed -i 's|http://deb.debian.org|http://ftp.debian.org|' /etc/apt/sources.list

RUN apt update && apt install -y \
    python3-dev \
    libmariadb3 \
    libmariadb-dev \
    build-essential \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .


ENV MARIADB_CONFIG=/usr/bin/mariadb_config

EXPOSE 5001

CMD ["python", "app.py"]