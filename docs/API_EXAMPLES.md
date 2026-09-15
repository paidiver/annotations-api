# API Examples

Set your API base URL once:

```bash
export API_BASE="http://localhost:8000"
```

The GET endpoints shown below are public. POST, PUT, PATCH, and DELETE requests require an API token:

```bash
export API_TOKEN="replace-with-your-api-token"
```

The examples use `Authorization: Bearer $API_TOKEN`. Interactive documentation is
available at `$API_BASE/api/docs/`, and the OpenAPI schema at `$API_BASE/api/schema/`.

Object IDs are UUIDs returned in the `id` field. Replace the example UUIDs with IDs
from your own responses; the server generates IDs for ordinary create requests.

## Search endpoints

Search returns annotation-label assignments: one annotation can produce multiple
rows when it has multiple labels or annotators.

| Query parameter | Behaviour |
| --- | --- |
| `name_part` | Partial label name, at least 3 characters; also resolves matching WoRMS taxa. |
| `aphia_ids[]` | Repeat for multiple AphiaIDs. |
| `include_descendants=true` | Include descendants of explicitly supplied AphiaIDs. Default: false. |
| `image_set_name`, `project`, `platform` | Partial image-set metadata names, at least 3 characters each. |
| `deployment`, `fauna_attraction`, `marine_zone` | Exact image-set metadata values; see the schema for allowed choices. |
| `min_lat`, `max_lat`, `min_lon`, `max_lon` | Inclusive bounds on image coordinates. Latitude: -90 to 90; longitude: -180 to 180; minimum must not exceed maximum. |
| `exclude_aphia_ids[]` | Repeat to exclude label AphiaIDs. |
| `exclude_annotation_set[]`, `exclude_image_set[]` | Repeat to exclude set UUIDs. |
| `order_by` | `label_aphia_id`, `annotation_creation_datetime`, or `label_name`. |
| `calculate_summary=true` | Include counts across all matching rows. Default: false. |
| `return_image_annotation_name_info=true` | Include image-set, annotation-set, and AphiaID information. Default: false. |
| `page`, `page_size` | Pagination controls; default page size 100, maximum 500. |
| `disable_pagination=true` | Return all rows for the flat search endpoint only. Default: false. |

At least one of `name_part` or `aphia_ids[]` is required. Invalid search parameters
return `400 Bad Request`. An AphiaID-only query with no resolved taxa returns
`404 Not Found`; a name search can still match local labels when no taxa resolve.
When both name and resolved AphiaIDs are supplied, labels matching either are
included, subject to the other filters. A valid search with no matching assignments
returns an empty collection.

### Search annotation labels

Use `--get --data-urlencode` to encode query values and the brackets in array
parameter names safely:

```bash
curl -sS --get "$API_BASE/api/annotations/search/" \
  --data-urlencode 'name_part=cod' \
  --data-urlencode 'aphia_ids[]=126436' \
  --data-urlencode 'aphia_ids[]=126437' \
  --data-urlencode 'include_descendants=true' \
  --data-urlencode 'calculate_summary=true' \
  --data-urlencode 'page_size=25'
```

The paginated response has `count`, `next`, `previous`, and `results`.
`results.annotations` is the list of matching rows. Each row contains:

- `uuid` (the annotation-label assignment ID)
- `creation_datetime`, `annotation_creation_datetime`
- `image_filename`, `image_handle`, `image_uuid`
- `label_name`, `label_aphia_id`
- `annotation_platform`, `annotation_shape`, `annotation_coordinates`, `annotation_dimension_pixels`
- `annotator_name`
- `annotation_set_uuid`, `annotation_set_name`, `image_set_uuid`, `image_set_name`

If requested, `results.summary` contains `n_annotations` (assignment count),
`n_images`, `n_annotation_sets`, and `n_image_sets`; `results.info` contains
`image_sets`, `annotation_sets`, and `aphia_ids`. With `disable_pagination=true`,
`annotations`, `summary`, and `info` are at the top level instead.

### Search grouped by annotation set

```bash
curl -sS --get "$API_BASE/api/annotations/search/grouped/" \
  --data-urlencode 'name_part=coral' \
  --data-urlencode 'calculate_summary=true' \
  --data-urlencode 'page_size=25'
```

The response is paginated. `results.annotations` is an object keyed by annotation
set UUID, with a list of matching rows for each key. Rows omit
`annotation_set_uuid`, since it is the group key. Pagination happens **before**
grouping, so one annotation set can appear on several pages. Summary and info,
when requested, cover the full matching results. This endpoint does not honour
`disable_pagination`.

### Export search results

```bash
curl -sS --get "$API_BASE/api/annotations/search/export/" \
  --data-urlencode 'name_part=coral' \
  --data-urlencode 'min_lat=49.95' \
  --data-urlencode 'max_lat=50.10' \
  --output annotations-export.json
```

Export accepts the same search filters and ordering, and returns an unpaginated
object with `annotations`, `images`, `annotation_sets`, and `image_sets` arrays.
It uses export-specific field names such as `annotation_label_name` and
`annotation_shape_name`; it does not return the flat search response structure
or optional summary/info sections.

## Look up WoRMS taxa

```bash
curl -sS --get "$API_BASE/api/taxonomy/worms/taxa/" \
  --data-urlencode 'name_part=Gadus' \
  --data-urlencode 'combine_vernaculars=true'
```

Returns an unpaginated list of taxa. `name_part` must be nonblank;
`combine_vernaculars` defaults to true and enables vernacular-name matching.

## Ingest imagery from an iFDO payload (POST)

This endpoint ingests an iFDO payload and creates an `ImageSet` together with its related `Image` records in a single request.

The request body accepts:

* `ifdo` (required): an object containing `image-set-header` and a list of `image-set-items`.

The header requires `image-set-name`; each item requires `image-filename`.
To supply UUIDs, use `image-set-uuid` inside the header and `image-uuid` inside
each item. The top-level `submission_id` and `image_set_uuid` fields are currently
ignored by the ingest view. This endpoint creates records; it does not update
existing records by UUID.

Example:

```bash
curl -sS -X POST "$API_BASE/api/ingest/image-sets/" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ifdo": {
      "image-set-header": {
        "image-set-name": "Dive 2026-02-11",
        "image-set-handle": "https://handle.example/12345/abc"
      },
      "image-set-items": [
        {
          "image-filename": "dive2026-02-11_img001.jpg"
        },
        {
          "image-filename": "dive2026-02-11_img002.jpg"
        }
      ]
    }
  }'
```

If the `ifdo` object is missing or invalid, the API returns `400 Bad Request`. If one or more image items fail validation, the whole transaction is rolled back and the API returns a `400 Bad Request` response describing the failed items.

A successful request returns `201 Created` with `message`, `image_set_id` (a UUID),
and `image_count`.

## Ingest annotations from an XLSX file (POST)

Use a completed annotation workbook with the sheets `Annotation set metadata`,
`Label set`, and `Annotation data`. A template is available at
[`annotation_metadata_template_v1.xlsx`](../api/tests/test_data/annotation_metadata_template_v1.xlsx).
Referenced imagery must already exist.

```bash
curl -sS -X POST "$API_BASE/api/ingest/annotation-sets/" \
  -H "Authorization: Bearer $API_TOKEN" \
  -F 'file=@/path/to/completed-annotations.xlsx'
```

Let curl set the multipart content type. Success returns `201 Created` with
`{"status": "uploaded", "data": ...}`. Invalid files, worksheets, parsed data, or
failed ingestion return `400 Bad Request`.

## Create (POST)

### Field endpoints

You can see below some examples of how to create objects through the API for the field endpoints, that only need to provide a `name` field. You can also include `uri` if you want.

#### Context

```bash
curl -sS -X POST "$API_BASE/api/fields/context/" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "test Context",
      "uri": "https://example.com/contexts/test-context"
      }'
```

#### PI

```bash
curl -sS -X POST "$API_BASE/api/fields/pi/" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "test PI"}'
```

### RelatedMaterial

For related material, the `uri` field is required, but you can also include `title` and `relation` if you want.

```bash
curl -sS -X POST "$API_BASE/api/fields/relatedmaterial/" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"uri": "https://example.com/related-material/12345", "title": "Related material title", "relation": "isSupplementTo"
  }'
```

> Important: you may need to output IDs of created objects (e.g. related materials, context, pi) to use them in the examples below for creating ImageSets, AnnotationSets, etc. You can do this by running a GET request to the corresponding endpoint (e.g. `GET /api/fields/relatedmaterial/`) and looking for the ID in the response.

### ImageSet

`ImageSet` requires at least a `name`. These examples also demonstrate how to create related objects through relationships:

* **Many-to-many (M2M)** (e.g. `creators`):

  * Provide full objects (e.g. `{ "name": "..." }`) → the API creates them if needed
  * OR provide existing IDs via `creators_ids`

* **Foreign keys (FK)** (e.g. `project`):

  * Provide `project_id`
  * OR provide a full `project` object with the required fields

Do not supply both an object field and its corresponding ID field in one request
(e.g. `project` and `project_id`, or `creators` and `creators_ids`). Nested named
metadata can reuse matching records, but conflicting metadata is rejected. Use
existing IDs when linking records you already know.

To run the example below, replace `RELATED_MATERIAL_ID` with an existing related material ID from your database, or provide a list of full `related_materials` objects instead.

```bash
RELATED_MATERIAL_ID="00000000-0000-0000-0000-000000000001"
curl -sS -X POST "$API_BASE/api/images/image_sets/" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dive 2026-02-11",
    "handle": "https://handle.example/12345/abc",
    "creators": [
      {
        "name": "Dr. Jane Doe",
        "uri": "https://example.com/creators/jane-doe"
      }
    ],
    "related_materials_ids": [
      "'$RELATED_MATERIAL_ID'"
    ],
    "project": {
      "name": "Benthic survey 2026",
      "uri": "https://example.com/projects/benthic-survey-2026"
    }
  }'
```

This will result in the following objects being created:

* An `ImageSet` with the provided name and handle, linked to the project supplied in the request
* A `Creator` with the provided name and URI, linked to the `ImageSet` through an M2M relationship
* A `Project` with the provided name and URI, linked to the `ImageSet` through an FK relationship

### AnnotationSet

`AnnotationSet` requires at least a `name`. These examples also demonstrate how to create related objects through relationships. You must use existing `ImageSet` IDs from your database for the `image_set_ids` field. For the other M2M and FK relationships, the same rules apply as described in the `ImageSet` example above. In the example below, replace `project_id` with an existing project ID from your database, or provide a full `project` object instead. Also replace `image_set_ids` with existing `ImageSet` IDs from your database.

```bash
IMAGE_SET_ID="00000000-0000-0000-0000-000000000010"
PROJECT_ID="00000000-0000-0000-0000-000000000100"
curl -sS -X POST "$API_BASE/api/annotations/annotation_sets/" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Benthic survey annotations (v1)",
    "version": "1.0.0",
    "image_set_ids": [
      "'$IMAGE_SET_ID'"
    ],
    "creators": [
      {
        "name": "Dr. Jane Doe",
        "uri": "https://example.com/creators/jane-doe"
      }
    ],
    "project_id": "'$PROJECT_ID'",
    "abstract": "Annotation set for the benthic imagery collected during survey XYZ."
  }'
```

This will create an `AnnotationSet` linked to the specified `ImageSet` and `Project`. Read its generated `id` from the response. You can then use this `annotation_set_id` when creating `Annotation` objects to link annotations to this annotation set.

### Image

For the `Image` model, the following fields are required: `image_set_id` and `filename`. The `image_set_id` field must reference an existing `ImageSet` in your database. The `filename` should be a string representing the name of the image file (e.g. "dive2026-02-11_img001.jpg"). Replace the `image_set_id` value in the example below with an existing `ImageSet` ID from your database.

```bash
IMAGE_SET_ID="00000000-0000-0000-0000-000000000010"
curl -sS -X POST "$API_BASE/api/images/images/" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "image_set_id": "'$IMAGE_SET_ID'",
    "filename": "dive2026-02-11_img001.jpg"
  }'
```

This will create an `Image` linked to the specified `ImageSet`. Read its generated `id` from the response. You can then use this `image_id` when creating `Annotation` objects to link annotations to this image.

### Annotation

For the `Annotation` model, the following fields are required: `shape` and `coordinates`. The `shape` field must be one of the allowed values (e.g. "polygon", "circle", etc.), and the `coordinates` field must be a list of lists, where each inner list represents a set of coordinates corresponding to the specified shape. For a polygon, each inner list contains flattened coordinates `[x1, y1, x2, y2, ...]`, with the first point repeated at the end. Canonical shapes are `single-pixel`, `polyline`, `polygon`, `circle`, `rectangle`, `ellipse`, and `whole-image`.

This endpoint also requires the `annotation_set_id` and `image_id` fields to link the annotation to an existing `AnnotationSet` and `Image`. You must use IDs that exist in your database for these fields.

```bash
IMAGE_ID="00000000-0000-0000-0000-000000000001"
ANNOTATION_SET_ID="00000000-0000-0000-0000-000000000020"
curl -sS -X POST "$API_BASE/api/annotations/annotations/" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "annotation_set_id": "'$ANNOTATION_SET_ID'",
    "image_id": "'$IMAGE_ID'",
    "annotation_platform": "SQUIDLE+",
    "shape": "polygon",
    "coordinates": [
      [100.5, 120.0, 180.2, 125.1, 175.0, 210.6, 98.9, 205.3, 100.5, 120.0]
    ],
    "dimension_pixels": 92.4
  }'
```

This will create an `Annotation` linked to the specified `AnnotationSet` and `Image`. Read its generated `id` from the response.

### Label

For the `Label` model, the following fields are required: `name` and `parent_label_name`. You also need to provide an existing `annotation_set_id` from your database to link the label to an `AnnotationSet`:

```bash
ANNOTATION_SET_ID="00000000-0000-0000-0000-000000000020"
curl -sS -X POST "$API_BASE/api/labels/labels/" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "coral",
    "parent_label_name": "organism",
    "annotation_set_id": "'$ANNOTATION_SET_ID'"
  }'
```

This will create a `Label` with the specified name and parent label, linked to the specified `AnnotationSet`, with a generated `id` returned in the response. You can then use this `label_id` when creating `AnnotationLabel` objects to link annotations to this label.

### AnnotationLabel

For the `AnnotationLabel` model, the following fields are required: `creation_datetime`, `annotation_id` and `label_id`. You must use existing IDs from your database for these fields to link an existing `Annotation` to an existing `Label`.

For the `annotator` field, it applies the same rules described for `ImageSet`: you can either provide an existing `annotator_id` or a full `annotator` object with the required fields (e.g. `name`). To link an existing annotator, use its `annotator_id`; use a nested object to create a new annotator with a unique name.

```bash
ANNOTATION_ID="00000000-0000-0000-0000-000000000100"
LABEL_ID="00000000-0000-0000-0000-000000000002"
curl -sS -X POST "$API_BASE/api/annotations/annotation_labels/" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "annotation_id": "'$ANNOTATION_ID'",
    "label_id": "'$LABEL_ID'",
    "annotator": {
      "name": "Dr. Jane Doe"
    },
    "creation_datetime": "2026-02-15T10:30:00Z"
  }'
```

## Read (GET)

Standard list endpoints return `count`, `next`, `previous`, and a `results` array.
Use `?page=2&page_size=25` to navigate; page size defaults to 100 and is capped at
500. Detail endpoints return a single object.

### List Creator

```bash
curl -sS -X GET "$API_BASE/api/fields/creator/" -H "Accept: application/json"
```

### List Context

```bash
curl -sS -X GET "$API_BASE/api/fields/context/" -H "Accept: application/json"
```

### List PI

```bash
curl -sS -X GET "$API_BASE/api/fields/pi/" -H "Accept: application/json"
```

### List all Images

```bash
curl -sS "$API_BASE/api/images/images/"
```

### Retrieve a single Image

In the example below, replace `IMAGE_ID` with an existing image ID from your database.

```bash
IMAGE_ID="00000000-0000-0000-0000-000000000001"
curl -sS "$API_BASE/api/images/images/$IMAGE_ID/"
```

## Update (PUT)

### ImageSet

PUT requires the required fields (including `name` for an ImageSet). In the current implementation, omitted optional fields and relationships retain their existing values; they are not automatically cleared. Use PATCH to change selected fields without resending required fields. For relationships:

* **M2M fields** (e.g. `related_materials_ids`, `creators_ids`):
  Provide the full updated list of IDs.
* **FK fields** (e.g. `project`):
  Provide either `project_id` or a full `project` object.

In the example below, replace `IMAGE_SET_ID` with an existing image set ID from your database. For `creators_ids`, replace them with existing IDs from your database or remove the field if you do not want to update it. For `project`, you can either provide an existing `project_id` or a full `project` object with the required fields.

```bash
IMAGE_SET_ID="00000000-0000-0000-0000-000000000010"
CREATOR_ID="4f545b61-4c4a-47ed-b9f9-a59d72dcfcb9"
curl -sS -X PUT "$API_BASE/api/images/image_sets/$IMAGE_SET_ID/" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dive 2026-02-11 (processed)",
    "handle": "https://handle.example/12345/abc",
    "copyright": "© NOC",
    "abstract": "Images collected during the dive on 2026-02-11. This record was updated after QC.",
    "creators_ids": [
      "'$CREATOR_ID'"
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

### Partially update an ImageSet (PATCH)

```bash
curl -sS -X PATCH "$API_BASE/api/images/image_sets/$IMAGE_SET_ID/" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"abstract": "Updated description after quality control."}'
```

For updates, supplying an M2M list replaces that relationship's membership;
use `[]` to clear it. Use `null` on a nullable FK ID field, such as `project_id`,
to unlink it. Do not supply both nested objects and IDs for the same relationship.

## Delete (DELETE)

### Delete a Label

In the example below, replace `LABEL_ID` with an existing label ID from your database.

```bash
LABEL_ID="00000000-0000-0000-0000-000000000002"

curl -sS -X DELETE "$API_BASE/api/labels/labels/$LABEL_ID/" \
  -H "Authorization: Bearer $API_TOKEN"
```
