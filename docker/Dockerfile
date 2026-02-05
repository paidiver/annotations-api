FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY . .

RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*
    
RUN pip install 'poetry~=1.8.0' && \
    poetry config virtualenvs.in-project false && \
    poetry config virtualenvs.create false && \
    poetry install --with lint,test --all-extras && \
    apt-get update && apt-get install -y postgresql-client

CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
EXPOSE 8000
