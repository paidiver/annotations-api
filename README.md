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

The [charts](charts/api) directory contains Helm charts that can be used to deploy this app.

### Helm Chart Versioning & Release Process

Helm chart releases are automated and driven by Git tags.

To release a new Helm Chart version, create a Git tag in the format:

`vMAJOR.MINOR.PATCH[-PRERELEASE]`

Examples:
- `v1.2.3` → stable release
- `v1.3.0-alpha.1` → prerelease

The workflow triggers on tag creation.
The CI workflow:

- Reads the tag version (1.2.3 from v1.2.3)
- Patches charts/api/Chart.yaml at package time (does not commit to the repo)
- Packages the Helm chart with the correct version
- Publishes the chart via [helm/chart-releaser-action](https://github.com/helm/chart-releaser-action)

The repo itself continues to have 0.0.0-dev in Chart.yaml for development.
The release version is derived solely from the Git tag.

### Usage

[Helm](https://helm.sh) must be installed to use the charts.  Please refer to
Helm's [documentation](https://helm.sh/docs) to get started.

Once Helm has been set up correctly, add the repo as follows:

```bash
helm repo add paidiver-annotations https://paidiver.github.io/annotations-api
```

If you had already added this repo earlier, run `helm repo update` to retrieve
the latest versions of the packages.  You can then run `helm search repo
paidiver-annotations` to see the charts.

To install the api chart:

```bash
helm install my-api paidiver-annotations/api
```

To uninstall the chart:

```bash
helm uninstall my-api
```

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
WORMS_API_BASE_URL=https://marinespecies.org/rest
CACHED_WORMS_API_BASE_URL=https://marinespecies.org/rest
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

To add some descriptive name to migration file that is going to generate, use `--name` flag while running migration command. And once the migration file is created, make sure to add some descriptive docstring on top of the file as well.

```bash
docker compose -f docker/docker-compose.yml exec api python manage.py makemigrations --name migration_description
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
docker compose -f docker/docker-compose.yml run --rm api tox -e py313
```

Coverage reports are written to `coverage_reports/`.

## Fake Data Generation

For development and testing, the project includes a management command that seeds the database with realistic fake data:

```bash
docker compose -f docker/docker-compose.yml run --rm api \
  python manage.py seed_demo_data
```

### Customising the amount of data

```bash
python manage.py seed_demo_data \
  --image-annotation-sets 3 \
  --images-per-image-set 15 \
  --labels-per-annotation-set 25 \
  --annotators 12 \
  --annotations-per-image 3 \
  --annotation-labels 150
```

⚠️ IMPORTANT: Development use only. Do not run against production databases.

## Dumping All Data (JSON)

To export **all database data as JSON** for inspection or debugging, use the endpoint:

```
http://localhost:8000/api/debug/db-dump/
```

This will return a JSON object containing all records from all tables, structured by model name.


## API Examples

A collection of example API requests and responses is available in the [API Examples](docs/API_EXAMPLES.md) document.

## Acknowledgements

This project was supported by the UK Natural Environment Research Council (NERC) through the *Tools for automating image analysis for biodiversity monitoring (AIAB)* Funding Opportunity, reference code **UKRI052**.
