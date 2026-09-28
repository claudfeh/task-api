# task-api — containerized multi-tier app

A small REST API (Python/Flask + PostgreSQL) behind an nginx reverse proxy,
packaged as production-style containers and orchestrated with Docker Compose.

This is **Project 1** of a DevOps portfolio series: the same app is later
wired into a CI/CD pipeline, provisioned with Terraform on AWS, and deployed
to Kubernetes.

## Architecture

```
              ┌─────────┐      ┌─────────┐      ┌──────────┐
 Internet ──► │  proxy  │ ───► │   app   │ ───► │    db    │
  :8080       │ (nginx) │      │ (Flask) │      │(postgres)│
              └─────────┘      └─────────┘      └──────────┘
               frontend ◄────► backend ◄────► backend
```

- **proxy** — nginx:1.27-alpine, terminates HTTP on port 80 (mapped to 8080
  on the host), reverse-proxies `/api/*` and `/health` to the app.
- **app** — multi-stage Python 3.12 image running gunicorn as a **non-root
  user**, with a container healthcheck.
- **db** — postgres:16-alpine with a named volume (`pgdata`) so data survives
  container recreation, plus an init script that creates the schema and seeds
  demo tasks.
- Two isolated networks: `frontend` (proxy ↔ app) and `backend` (app ↔ db).
  The database is not reachable from outside the backend network.

## Quickstart

```bash
cp .env.example .env        # adjust passwords/ports if you like
docker compose up --build -d
docker compose ps           # all three services should show "healthy"
curl http://localhost:8080/api/tasks
```

## API endpoints

| Method | Path               | Description            |
|--------|--------------------|------------------------|
| GET    | `/health`          | Service + DB status    |
| GET    | `/api/tasks`       | List all tasks         |
| POST   | `/api/tasks`       | Create a task `{"title": "..."}` |
| PATCH  | `/api/tasks/{id}`  | Toggle a task done/undone |
| DELETE | `/api/tasks/{id}`  | Delete a task          |

Try it:

```bash
curl -X POST http://localhost:8080/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Write the Terraform module"}'
```

## What this demonstrates

- **Multi-stage Dockerfile** — dependencies built in a throwaway stage, so the
  runtime image stays slim.
- **Non-root container user** — the app never runs as root inside the container.
- **Healthchecks + ordered startup** — `depends_on` with
  `condition: service_healthy` means the app waits for Postgres to actually
  accept connections (not just for the container to exist).
- **Network segmentation** — the database lives on an internal-only network.
- **Persistent data** — named volume; `docker compose down` does not delete
  your data (only `docker compose down -v` does).
- **12-factor config** — all credentials/ports come from the environment
  (`.env`), with sane defaults so it runs out of the box.
- **Read-only mounts** — nginx config and DB init script are mounted `:ro`.

## Teardown

```bash
docker compose down        # stop, keep data
docker compose down -v     # stop and delete the database volume
```

## Series roadmap

1. ✅ `task-api` — containerized app (this repo)
2. ⬜ CI/CD pipeline with GitHub Actions (build → test → push to GHCR)
3. ⬜ Terraform infrastructure on AWS (VPC, compute, remote state)
4. ⬜ Kubernetes manifests + Helm chart
