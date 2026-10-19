# CI pipeline

The workflow is in `.github/workflows/ci.yml`. It checks the week 3 Flask app
on every change: style first, then tests on three Python versions, then the
Docker image.

```
           ┌──────────┐     ┌───────────────────────┐     ┌──────────┐
 trigger ─►│   lint   │ ──► │ test (matrix)         │ ──► │  build   │
           │  ruff    │     │ py3.11  py3.12  py3.13│     │  docker  │
           └──────────┘     └───────────────────────┘     └──────────┘
                              artifact: junit XML         artifact: image digest
```

## CI, CD and CD

- **Continuous integration** — every push is built and tested automatically,
  so broken code is found minutes after it is written. This workflow is CI.
- **Continuous delivery** — CI plus a release-ready artifact (here: the Docker
  image) that can be deployed with one manual click.
- **Continuous deployment** — the same, but the deploy also happens
  automatically when the pipeline is green, with no human step.

## Triggers

| Event | When it runs | Why |
| --- | --- | --- |
| `push` to `main` | After a merge or a direct push to `main` | `main` must always be green |
| `pull_request` to `main` | When a PR is opened or a new commit is pushed to it | Problems are found before the merge |
| `workflow_dispatch` | Manually, with **Run workflow** on the Actions tab | Re-run without a new commit |

`concurrency` cancels an older run of the same branch when a newer commit
arrives, so CI time is not wasted on outdated code. `permissions:
contents: read` gives the job token read-only access; the workflow uses no
secrets.

## Jobs

### 1. `lint`

Installs the dev tools and runs [ruff](https://docs.astral.sh/ruff/):

- `ruff check` — unused imports, undefined names, import order, likely bugs
  (rules `E`, `W`, `F`, `I`, `B` in `pyproject.toml`). `--output-format=github`
  shows the problems as annotations right on the changed lines.
- `ruff format --check` — fails if the code is not formatted.

It runs first because it is the fastest (a few seconds); there is no point in
running tests on code that does not pass basic checks.

### 2. `test` (matrix)

`needs: lint`, so it starts only after lint is green. A **matrix** runs the
same job three times in parallel, on Python **3.11, 3.12 and 3.13**, to show
the app works on every supported version.

- `pytest` runs the 6 tests in `tests/test_app.py` with Flask's test client
  (no real server needed).
- **Fail fast:** if any test fails, pytest exits with a non-zero code, the step
  fails, the job fails, and `build` is skipped because it `needs: test`.
  `strategy.fail-fast: true` also cancels the other matrix jobs as soon as one
  of them fails.
- `--junitxml` writes a test report. It is uploaded as the artifact
  `test-results-py<version>` with `if: always()`, so the report is kept even
  (and especially) when tests fail.

### 3. `build`

`needs: test`, so an image is built only from tested code.

- `docker/build-push-action` builds the same multi-stage `Dockerfile` as in
  week 3. `push: false` — nothing is published, so no registry credentials
  are needed.
- **Smoke test:** runs the image, waits for `/healthz` to answer and prints the
  user the container runs as (`uid=999(app)`).
- The image ID and digest are written to `image-digest.txt` and uploaded as the
  artifact `image-digest`.

## Caching

Without a cache every run downloads every dependency again. Two caches are used:

| Cache | How | What it saves |
| --- | --- | --- |
| pip | `actions/setup-python` with `cache: pip` and `cache-dependency-path: requirements-dev.txt` | Downloaded wheels of Flask, pytest, ruff, … are restored instead of fetched from PyPI |
| Docker layers | `cache-from: type=gha` / `cache-to: type=gha,mode=max` | Unchanged image layers (base image, `pip install` in the builder stage) are reused |

The cache **key** is a hash of `requirements-dev.txt`. While the file does not
change, every run gets a cache hit. When a dependency version changes, the hash
changes, a fresh cache is created, and the old one is no longer used — so the
cache can never serve outdated packages. This is the same idea as Docker layer
caching from week 3: copy the dependency list first, so the expensive install
step is only redone when that list changes.

## Pinned versions

Every action is pinned to a major version (`actions/checkout@v4`,
`actions/setup-python@v5`, `actions/upload-artifact@v4`,
`docker/setup-buildx-action@v3`, `docker/build-push-action@v6`), the runner is
`ubuntu-24.04` instead of `ubuntu-latest`, and every Python package has an
exact version. A new release of a tool cannot silently change or break the
pipeline.

## Running the same checks locally

```bash
pip install -r requirements-dev.txt
ruff check .
ruff format --check .
pytest
```
