# Annotations API

Annotations API provides a database-backed REST API for working with image metadata, with a focus on annotations for underwater imagery.

The service is implemented using **Django** and **Django REST Framework**, with PostgreSQL/PostGIS as the backing database.

## Overview

This API follows the database schema defined in the
[IFDO API repository](https://github.com/paidiver/ifdo-api).

Relevant documentation:

* **DATABASE.md** – core data model for image collections and annotations
  [https://github.com/paidiver/ifdo-api/blob/main/DATABASE.md](https://github.com/paidiver/ifdo-api/blob/main/DATABASE.md)
* **SchemaSpy docs** – auto-generated database documentation
  [https://paidiver.github.io/ifdo-api](https://paidiver.github.io/ifdo-api)
* **schema.sql** – SQL script to create the database schema
  [https://github.com/paidiver/ifdo-api/blob/main/docs/schema.sql](https://github.com/paidiver/ifdo-api/blob/main/docs/schema.sql)

## Requirements

### Runtime

* Docker
* Docker Compose

### Local development (without Docker)

* Python ≥ 3.10
* Poetry

## Project Structure

```text
.
├── api/                # Django app (API)
├── config/             # Django project configuration
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── scripts/
│       └── wait-for-it.sh
├── manage.py
├── pyproject.toml      # Project metadata & dependencies (Poetry)
├── poetry.lock         # Locked dependency versions
├── tox.ini             # Test, lint, and format automation
├── ruff.toml           # Ruff configuration
├── README.md
├── LICENSE
└── .env.example
```

## Dependency Management

This project uses **Poetry** for dependency management and packaging.

Key points:

* Dependencies are defined in `pyproject.toml`
* Locked versions live in `poetry.lock`
* Development tools (linting, formatting, testing) are installed via Poetry groups

## Helm Charts

The [charts](charts) directory contains Helm charts that can be used to deploy this app.

### Usage

[Helm](https://helm.sh) must be installed to use the charts.  Please refer to
Helm's [documentation](https://helm.sh/docs) to get started.

Once Helm has been set up correctly, add the repo as follows:

helm repo add paidiver-annotations https://paidiver.github.io/annotations-api

If you had already added this repo earlier, run `helm repo update` to retrieve
the latest versions of the packages.  You can then run `helm search repo
paidiver-annotations` to see the charts.

To install the <chart-name> chart:

    helm install my-<chart-name> paidiver-annotations/<chart-name>

To uninstall the chart:

    helm uninstall my-<chart-name>

## Quick Start (Docker – Recommended)

### 1. Create environment file

Configuration is provided via environment variables defined in `.env`.

Start from the example file:

```bash
cp .env.example .env
```

Example contents:

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

### 2. Build and run the stack

```bash
docker compose -f docker/docker-compose.yml up --build
```

This will:

* Start PostgreSQL/PostGIS
* Run Django migrations
* Start the Django development server

### 3. Test the API

Health endpoint:

```
http://localhost:8000/api/health/
```

Expected response:

```json
{"status": "ok"}
```

API schema and documentation:

```
http://localhost:8000/api/docs/
```

## Running Locally Without Docker

### 1. Install dependencies

```bash
poetry install
```

### 2. Start only the database via Docker

```bash
docker compose -f docker/docker-compose.yml up -d db
```

### 3. Apply migrations

```bash
python manage.py migrate
```

### 4. Run the development server

```bash
python manage.py runserver
```

## Database Migrations

Create new migrations after modifying models:

```bash
docker compose -f docker/docker-compose.yml exec api python manage.py makemigrations
```

Apply migrations:

```bash
docker compose -f docker/docker-compose.yml exec api python manage.py migrate
```

## Development Workflow

### Formatting

Format code using Ruff:

```bash
tox -e format
```

### Linting

Run lint checks:

```bash
tox -e lint
```

### Tests

Run the test suite with coverage:

```bash
tox
```

or explicitly:

```bash
tox -e py310
```

Coverage reports are written to `coverage_reports/`.

## Acknowledgements

This project was supported by the UK Natural Environment Research Council (NERC) through the *Tools for automating image analysis for biodiversity monitoring (AIAB)* Funding Opportunity, reference code **UKRI052**.
