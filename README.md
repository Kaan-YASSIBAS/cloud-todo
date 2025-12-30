# Cloud-Todo — Microservices + DevOps + OpenShift (Kubernetes) + Observability

Cloud-Todo is a small **microservices-based Todo application** designed to demonstrate an end-to-end modern delivery pipeline:
- **Microservices** (Auth + Task + Frontend)
- **Containerization** (Docker)
- **Deployment on OpenShift** (Developer Sandbox / namespace-scoped)
- **CI/CD** (GitHub Actions → Docker Hub → OpenShift rollout)
- **Monitoring + Logging** (Prometheus, Grafana, Loki, Promtail)
- **Database** (PostgreSQL + PVC)

> This repository is **our own implementation** (not a template) and includes source code, OpenShift manifests, and CI/CD definitions.

---

## ✨ Architecture (High Level)

Users
|
v
[Frontend (Nginx)] --calls--> [Auth Service (FastAPI)] ---> [PostgreSQL]
| |
| +--> JWT verification
|
+------------calls--------> [Task Service (FastAPI)] ---> [PostgreSQL]


**Observability**
- **Prometheus** scrapes `/metrics` from services
- **Blackbox Exporter** checks HTTP/TCP uptime (Routes + DB port)
- **Postgres Exporter** exposes DB internal metrics
- **Promtail** collects pod logs and pushes to **Loki**
- **Grafana** visualizes everything (Metrics + Logs)

---

## 📦 Services

### `auth-service` (FastAPI)
- User registration / login
- Issues JWT tokens
- `/healthz` health endpoint
- `/metrics` for Prometheus scraping
- Uses SQLAlchemy models and auto-creates tables on startup (see `Base.metadata.create_all`)

### `task-service` (FastAPI)
- Todo CRUD operations (task business logic)
- JWT validation / protected endpoints
- `/healthz` + `/metrics`
- Uses SQLAlchemy models and auto-creates tables on startup

### `frontend` (Nginx static)
- Simple UI served by Nginx
- Configured for OpenShift non-root compatibility
- Exposed via OpenShift **Route**

---

## 🗂 Repository Structure

.
├─ auth-service/
│ ├─ app/ (FastAPI code: main.py, models.py, schemas.py, security.py, db.py, config.py)
│ ├─ tests/
│ ├─ Dockerfile
│ └─ requirements.txt
├─ task-service/
│ ├─ app/ (similar structure)
│ ├─ tests/
│ ├─ Dockerfile
│ └─ requirements.txt
├─ frontend/
│ ├─ *.html / *.css / *.js
│ ├─ Dockerfile (nginx)
│ └─ package.json (if used for assets)
├─ infra/
│ └─ openshift/
│ ├─ auth-service/ (deployment, service, configmap, secret, route)
│ ├─ task-service/ (deployment, service, configmap, secret, route)
│ ├─ frontend/ (deployment, service, route)
│ ├─ postgres/ (deployment, service, secret, pvc)
│ └─ monitoring/
│ ├─ grafana/
│ ├─ loki/
│ ├─ promtail/
│ └─ prometheus/ (blackbox + postgres-exporter)
└─ .github/workflows/
├─ ci-cd-kaan.yaml
└─ release-please.yaml

release-please-config.json

release-please-manifest.json


---

## 🧰 Tech Stack

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL
- **Frontend:** Static UI served by **Nginx**
- **CI/CD:** GitHub Actions, Docker Hub, OpenShift CLI (`oc`)
- **Monitoring:** Prometheus, Grafana, Blackbox Exporter, Postgres Exporter
- **Logging:** Loki + Promtail
- **Platform:** OpenShift Developer Sandbox (namespace-scoped permissions)

---

## 🚀 Deploy on OpenShift (Developer Sandbox)

### Prerequisites
- An OpenShift project/namespace (e.g. `kyassibas-dev`)
- `oc` CLI logged in
- Docker images pushed to Docker Hub (or build via CI/CD)
- Apply manifests from `infra/openshift`

### 1) Deploy PostgreSQL (stateful)
Postgres is deployed with a **PVC** for persistence.

```bash
oc project <YOUR_NAMESPACE>

# Postgres (PVC + Secret + Service + Deployment)
oc apply -f infra/openshift/postgres/

2) Deploy Services (auth + task)
oc apply -f infra/openshift/auth-service/
oc apply -f infra/openshift/task-service/


Note: auth-service and task-service include Route manifests for development/demo Swagger access.
In production, these services are usually kept internal (expose only frontend or an API gateway).

3) Deploy Frontend (public Route)
oc apply -f infra/openshift/frontend/

4) Deploy Monitoring & Logging
oc apply -f infra/openshift/monitoring/

🔎 Monitoring (Prometheus + Grafana)

Prometheus scrapes:

Application metrics: auth-service:8001/metrics, task-service:8002/metrics

Blackbox checks:

HTTP uptime for Routes (frontend, auth/healthz, task/healthz)

TCP uptime for DB port (todo-db:5432)

Postgres exporter metrics: postgres-exporter:9187

Grafana is provisioned via ConfigMaps:

Prometheus datasource auto-configured

Dashboards auto-loaded into a folder (e.g. Cloud-Todo)

Access Grafana

Open the Grafana Route created by infra/openshift/monitoring/grafana/route.yaml

Login using credentials stored in grafana/secret.yaml

Sandbox note: In Developer Sandbox we are namespace-scoped, so monitoring is built to scrape and observe only resources in our namespace (not cluster-wide metrics).

🧾 Logging (Loki + Promtail)

Promtail discovers pods in our namespace and pushes logs to Loki:

Loki push endpoint: http://loki:3100/loki/api/v1/push

Labels (namespace, pod, container) are attached so logs can be filtered easily in Grafana Explore.

View Logs

Grafana → Explore → datasource Loki

Filter by labels to isolate service logs (e.g. auth-service / task-service)

🔁 CI/CD (GitHub Actions)

We use two workflows:

1) ci-cd-kaan.yaml — Build + Push + Deploy to OpenShift

Two modes:

A) Branch Mode (kaan-branch)

Trigger: push to kaan-branch

Detects which components changed (auth / task / frontend)

Builds only changed services

Pushes unique image tags using commit SHA (avoids cache issues)

Deploys using:

oc set image deploy/<service> ...:<sha-tag>

oc rollout status

B) Tag Mode (SemVer per service)

Trigger: push tag like:

auth-v1.0.9

task-v1.0.7

frontend-v1.0.7

Builds the specific component and pushes immutable version tags:

auth-service-v1.0.9, etc.

Deploys the exact version to OpenShift

OpenShift credentials are provided via GitHub Secrets (server, token, namespace, Docker Hub creds).

2) release-please.yaml — Automated versioning per service

Trigger: push to kaan-branch

Manages SemVer + changelog per component using:

release-please-config.json

release-please-manifest.json

Produces service-scoped tags like task-vX.Y.Z

🧪 Testing

Each service includes a tests/ folder.
Example (inside a service folder):

pip install -r requirements.txt
pytest -q


Demo videos show running application on OpenShift and include monitoring/logging evidence.

🔐 Configuration & Secrets

We follow a clean separation:

ConfigMap: non-sensitive config (e.g. CORS_ORIGINS)

Secret: sensitive values (JWT secret, DB URL, passwords)

Example DB URL used in OpenShift:
postgresql+psycopg2://todo_user:todo_pass@todo-db:5432/todo_db

📽 Demo Checklist (What we demonstrate)

OpenShift Topology: all pods running (app + monitoring/logging)

Grafana dashboard: service health + request rate + blackbox uptime + DB metrics

Loki logs in Grafana Explore: auth/task logs, filtered by pod/container labels

CI/CD proof:

a small frontend change → push to kaan-branch

GitHub Actions run builds & deploys

OpenShift rollout updates image tag (SHA) and UI change appears on Route