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

To add some descriptive ame to migration file that is going to generate, use `--name` flag while running migration command. And once the migration file is created, make sure to add some descriptive docstring on top of the file as well.

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

Set your API base URL once:

```bash
export API_BASE="http://localhost:8000"
```

### Create (POST)

#### AnnotationSet

`AnnotationSet` requires at least `name`. These examples also demonstrate how to create related objects via relationships:

* **Many-to-many (M2M)** (e.g. `creators`):

  * Provide full objects (e.g. `{ "name": "..." }`) → API creates them if needed
  * OR provide existing IDs via `creators_ids`

* **Foreign keys (FK)** (e.g. `project`):

  * Provide `project_id`
  * OR provide a full `project` object with required fields

```bash
curl -sS -X POST "$API_BASE/api/annotations/annotation_sets/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Benthic survey annotations (v1)",
    "version": "1.0.0",
    "image_set_ids": [
      "00000000-0000-0000-0000-000000000010"
    ],
    "creators": [
      {
        "name": "Dr. Jane Doe",
        "uri": "https://example.com/creators/jane-doe"
      }
    ],
    "project_id": "00000000-0000-0000-0000-000000000100",
    "abstract": "Annotation set for the benthic imagery collected during survey XYZ."
  }'
```

#### Annotation

* `shape` is required
* `coordinates` is required and must be a **list of lists**

```bash
curl -sS -X POST "$API_BASE/api/annotations/annotations/" \
  -H "Content-Type: application/json" \
  -d '{
    "annotation_set_id": "00000000-0000-0000-0000-000000000020",
    "image_id": "00000000-0000-0000-0000-000000000001",
    "annotation_platform": "SQUIDLE+",
    "shape": "polygon",
    "coordinates": [
      [100.5, 120.0, 180.2, 125.1, 175.0, 210.6, 98.9, 205.3, 100.5, 120.0]
    ],
    "dimension_pixels": 92.4
  }'
```

### Read (GET)

#### List all Images

```bash
curl -sS "$API_BASE/api/images/images/"
```

#### Retrieve a single Image

```bash
IMAGE_ID="00000000-0000-0000-0000-000000000001"

curl -sS "$API_BASE/api/images/images/$IMAGE_ID/"
```

### Update (PUT)

#### ImageSet

It replaces the full object. You must include at least `name` and fields you want to update, otherwise they will be set to null/empty. For relationships:

* **M2M fields** (e.g. `related_material_ids`, `creators_ids`):
  Provide the full updated list of IDs.
* **FK fields** (e.g. `project`):
  Provide either `project_id` or a full `project` object.

```bash
IMAGE_SET_ID="00000000-0000-0000-0000-000000000010"

curl -sS -X PUT "$API_BASE/api/images/image_sets/$IMAGE_SET_ID/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dive 2026-02-11 (processed)",
    "handle": "https://handle.example/12345/abc",
    "copyright": "© NOC",
    "abstract": "Images collected during dive on 2026-02-11. This record was updated after QC.",
    "related_material_ids": [
      "00000000-0000-0000-0000-000000000011",
      "00000000-0000-0000-0000-000000000012"
    ],
    "project": {
      "name": "Benthic survey 2026",
      "uri": "https://example.com/projects/benthic-survey-2026"
    },
    "min_latitude_degrees": 49.95,
    "max_latitude_degrees": 50.10,
    "min_longitude_degrees": -4.20,
    "max_longitude_degrees": -4.05
  }'
```

### Delete (DELETE)

#### Delete a Label

```bash
LABEL_ID="00000000-0000-0000-0000-000000000002"

curl -sS -X DELETE "$API_BASE/api/labels/labels/$LABEL_ID/"
```

## Acknowledgements

This project was supported by the UK Natural Environment Research Council (NERC) through the *Tools for automating image analysis for biodiversity monitoring (AIAB)* Funding Opportunity, reference code **UKRI052**.
