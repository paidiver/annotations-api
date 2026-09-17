## Helm Charts

The [charts](api) directory contains Helm charts that can be used to deploy this app.

### Helm Chart Versioning & Release Process

Helm chart releases are automated and driven by Git tags.

To release a new Helm Chart version, create a Git tag in the format:

`helm-vMAJOR.MINOR.PATCH[-PRERELEASE]`

Examples:
- `v1.2.3` → stable release
- `v1.3.0-alpha.1` → prerelease

The workflow triggers on tag creation.
The CI workflow:

- Reads the tag version (1.2.3 from helm-v1.2.3)
- Patches charts/api/Chart.yaml at package time (does not commit to the repo)
- Packages the Helm chart with the correct version
- Publishes the chart via [helm/chart-releaser-action](https://github.com/helm/chart-releaser-action)

Whenever you make any change to a Chart, you must update the version in `Chart.yaml`.

* Increment the version to a higher value (e.g. `0.0.0-dev` → `0.0.1-dev`)
* This is required because the lint process checks that the new version is greater than the previous one
* If the version is not increased, linting will fail and the release will not run

> Note: The `Chart.yaml` version does not need to match the Git tag, but it must always be higher than the previous version.

To tag a git commit:

```bash
git tag helm-vX.X.X
git push origin helm-vX.X.X
```

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

## Releasing Docker Images

### Production release

A new `latest` Docker image is built and published to https://ghcr.io/paidiver/annotations-api on each push to main.

### Versioned release
Pushing a Git tag matching `v*` also publishes a Docker image. The full tag is
preserved: `v1.2.3` publishes `ghcr.io/paidiver/annotations-api:v1.2.3`, and
`v1.3.0-alpha.1` publishes `ghcr.io/paidiver/annotations-api:v1.3.0-alpha.1`.
The commit SHA is published as an additional image tag. Versioned pushes do not
update `latest`, which continues to track pushes to `main`.

### Development release
Development versions of Docker images can be released manually, driven by Git tags.
To release a new Docker image, create a Git tag in the format:

`docker-vMAJOR.MINOR.PATCH[-PRERELEASE]`

Examples:
- `v1.2.3` → stable release
- `v1.3.0-alpha.1` → prerelease

The workflow triggers on tag creation.
The CI workflow:

- Reads the tag version (1.2.3 from docker-v1.2.3)
- Builds a new Docker image
- Tags the Docker image with the tag version as well as the tagged commit SHA
- Pushes the images to the GitHub Container Repository

To tag a git commit:

```bash
git tag docker-vX.X.X
git push origin docker-vX.X.X
```
