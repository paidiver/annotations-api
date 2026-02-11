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


## API Examples

Set your API base URL once:

```bash
export API_BASE="http://localhost:8000"
```

### Create (POST)

Ensure you run following command in order so to create annotation_sets and annotation record you have required record already created. 

#### Creator

```bash
curl -sS -X POST "$API_BASE/api/fields/creator/" \
  -H "Content-Type: application/json" \
  -d '{"name": "test Creator"}'
```


#### Context

```bash
curl -sS -X POST "$API_BASE/api/fields/context/" \
  -H "Content-Type: application/json" \
  -d '{"name": "test Context"}'
  ```


#### PI

```bash
curl -sS -X POST "$API_BASE/api/fields/pi/" \
  -H "Content-Type: application/json" \
  -d '{"name": "test PI"}'
```


#### Event

```bash
curl -sS -X POST "$API_BASE/api/fields/event/" \
  -H "Content-Type: application/json" \
  -d '{"name": "test Event"}'
```


#### License

```bash
curl -sS -X POST "$API_BASE/api/fields/license/" \
  -H "Content-Type: application/json" \
  -d '{"name": "test License"}'
```


#### Platform

```bash
curl -sS -X POST "$API_BASE/api/fields/platform/" \
  -H "Content-Type: application/json" \
  -d '{"name": "test Platform"}'
```


#### Project

```bash
curl -sS -X POST "$API_BASE/api/fields/project/" \
  -H "Content-Type: application/json" \
  -d '{"name": "test Project"}'
```


#### RelatedMaterial

```bash
curl -sS -X POST "$API_BASE/api/fields/relatedmaterial/" \
  -H "Content-Type: application/json" \
  -d '{"name": "test Related Material"}'
```


#### Sensor

```bash
curl -sS -X POST "$API_BASE/api/fields/sensor/" \
  -H "Content-Type: application/json" \
  -d '{"name": "test Sensor"}'
```


#### Image Camera Pose

```bash
curl -sS -X POST "$API_BASE/api/fields/image_camera_pose/" -H "Content-Type: application/json" -d '{"utm_zone": "56H", "utm_epsg": "32756", "utm_east_north_up_meters": [123456.7, 8910111.2, 50.5], "absolute_orientation_utm_matrix": [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]}'
```

#### Image Domeport Parameter

```bash
curl -sS -X POST "$API_BASE/api/fields/image_domeport_parameter/" -H "Content-Type: application/json" -d '{"outer_radius_millimeters": 150.0, "decentering_offset_xyz_millimeters": [0.0, 0.0, 5.2], "extra_description": "test Domeport"}'
```


#### Image Flatport Parameter

```bash
curl -sS -X POST "$API_BASE/api/fields/image_flatport_parameter/" -H "Content-Type: application/json" -d '{"lens_port_distance_millimeters": 25.5, "interface_normal_direction": [0.0, 0.0, 1.0], "extra_description": "test Flatport"}'
```


#### Image Camera Calibration Model

```bash
curl -sS -X POST "$API_BASE/api/fields/image_camera_calibration_model/" -H "Content-Type: application/json" -d '{"calibration_model_type": "rectilinear water", "focal_length_xy_pixel": [3500.0, 3500.0], "principal_point_xy_pixel": [1920.0, 1080.0], "distortion_coefficients": [-0.2, 0.1, 0.0, 0.0, 0.0], "approximate_field_of_view_water_xy_degree": [70.5, 50.2], "extra_description": "test Calibration"}'
```


#### Image Camera Housing Viewport

```bash
curl -sS -X POST "$API_BASE/api/fields/image_camera_housing_viewport/" -H "Content-Type: application/json" -d '{"viewport_type": "dome port", "optical_density": 1.49, "thickness_millimeters": 10.0, "extra_description": "test Viewport"}'
```


#### Image Photometric Calibration

```bash
curl -sS -X POST "$API_BASE/api/fields/image_photometric_calibration/" -H "Content-Type: application/json" -d '{"sequence_white_balancing": "manual preset", "exposure_factor_rgb": [1.2, 1.0, 1.5], "sequence_illumination_type": "artificial", "sequence_illumination_description": "dual strobe", "illumination_factor_rgb": [1.0, 1.0, 1.0], "water_properties_description": "clear oceanic"}'
```

#### Annotators

```bash
curl -sS -X POST "$API_BASE/api/annotations/annotators/" -H "Content-Type: application/json" -d '{"name": "test Annotator"}'
```


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

#### List Creator
```bash
curl -sS -X GET "$API_BASE/api/fields/creator/" -H "Accept: application/json"
```

#### List Context
```bash
curl -sS -X GET "$API_BASE/api/fields/context/" -H "Accept: application/json"
```

#### List PI
```bash
curl -sS -X GET "$API_BASE/api/fields/pi/" -H "Accept: application/json"
```

#### List Event
```bash
curl -sS -X GET "$API_BASE/api/fields/event/" -H "Accept: application/json"
```

#### List License
```bash
curl -sS -X GET "$API_BASE/api/fields/license/" -H "Accept: application/json"
```

#### List Platform
```bash
curl -sS -X GET "$API_BASE/api/fields/platform/" -H "Accept: application/json"
```

#### List Project
```bash
curl -sS -X GET "$API_BASE/api/fields/project/" -H "Accept: application/json"
```

#### List RelatedMaterial
```bash
curl -sS -X GET "$API_BASE/api/fields/relatedmaterial/" -H "Accept: application/json"
```

#### List Sensor
```bash
curl -sS -X GET "$API_BASE/api/fields/sensor/" -H "Accept: application/json"
```

#### List Image Camera Pose
```bash
curl -sS -X GET "$API_BASE/api/fields/image_camera_pose/" -H "Accept: application/json"
```

#### List List Image Domeport Parameter
```bash
curl -sS -X GET "$API_BASE/api/fields/image_domeport_parameter/" -H "Accept: application/json"
```

#### List Image Flatport Parameter
```bash
curl -sS -X GET "$API_BASE/api/fields/image_flatport_parameter/" -H "Accept: application/json"
```

#### List Image Camera Calibration Model
```bash
curl -sS -X GET "$API_BASE/api/fields/image_camera_calibration_model/" -H "Accept: application/json"
```

#### List Image Camera Housing Viewport
```bash
curl -sS -X GET "$API_BASE/api/fields/image_camera_housing_viewport/" -H "Accept: application/json"
```

#### List Image Photometric Calibration
```bash
curl -sS -X GET "$API_BASE/api/fields/image_photometric_calibration/" -H "Accept: application/json"
```

#### List Annotators
```bash
curl -sS -X GET "$API_BASE/api/annotations/annotators/" -H "Accept: application/json"
```


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
