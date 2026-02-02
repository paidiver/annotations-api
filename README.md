# Annotations API

Annotations API is an implementation a database and a REST API for dealing with image metadata, with a focus on annotations for underwater imagery.

## Overview

This api follows the database schema defined in the [IFDO-api repo](https://github.com/paidiver/ifdo-api). The database schema is documented in the following links:
- [DATABASE.md](https://github.com/paidiver/ifdo-api/DATABASE.md): Detailed description of the core data model for image collections and annotations.
- [Schemaspy database docs](https://paidiver.github.io/ifdo-api): Auto-generated database documentation using SchemaSpy.
- [Schema.sql](https://github.com/paidiver/ifdo-api/docs/schema.sql): SQL script to create the database schema.


## Requirements

* Docker & Docker Compose


## Project Structure

```text
.
├── api/                # Django app (API)
├── config/             # Django project config
├── docker
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── scripts
│       └── wait-for-it.sh
├── LICENSE
├── manage.py
├── README.md
├── .env.example
└── requirements.txt
```

## Quick Start

### 1. Create environment file

Defined in `.env`:

```env
POSTGRES_DB=annotationsdb
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_HOST=db
POSTGRES_PORT=5432

DJANGO_SECRET_KEY=dev-secret-key-change-me
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

Use `.env.example` for shared defaults. Copy it to `.env` and modify as needed.

```bash
cp .env.example .env
```

### 2. Build and run everything

```bash
docker compose -f docker/docker-compose.yml up --build
```

This will:

* Start PostgreSQL
* Run Django migrations
* Start the Django development server

---

### 3. Test the API

Open your browser or curl [http://localhost:8000/api/health/](http://localhost:8000/api/health/).

Response:

```json
{"status": "ok"}
```

You can also access the API schema and docs at [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/).


## Creating and running migrations

To create new migrations after modifying models:

```bash
docker compose -f docker/docker-compose.yml exec api python manage.py makemigrations
```

After creating migrations, apply them:

```bash
docker compose -f docker/docker-compose.yml exec api python manage.py migrate
```

## Running Django Without Docker

If you prefer local execution:

```bash
pip install -r requirements.txt
```

Start Postgres via Docker only:

```bash
docker compose -f docker/docker-compose.yml up -d db
```

Then update migrations:

```bash
python manage.py migrate
```

Finally, run the development server:

```bash
python manage.py runserver
```

## Acknowledgements

This project was supported by the UK Natural Environment Research Council (NERC)
through the *Tools for automating image analysis for biodiversity monitoring (AIAB)*
Funding Opportunity, reference code **UKRI052**.
