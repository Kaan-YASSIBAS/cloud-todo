# ☁️ Cloud ToDo – Microservices Project

A simple cloud-native **To-Do web application** built with a **microservices architecture** for the Cloud Computing course.  
The project demonstrates **containerization**, **Kubernetes deployment**, and a basic **DevOps CI/CD pipeline** using GitHub Actions.

---

## 🧩 Overview

**Cloud ToDo** is a minimal task management app built with two backend microservices and one frontend interface:

| Service | Description | Technology |
|----------|--------------|-------------|
| 🧠 **Auth Service** | Handles login and JWT authentication | FastAPI (Python) |
| 📝 **Task Service** | Manages To-Do CRUD operations | FastAPI + MySQL |
| 💻 **Frontend** | Simple web UI for task management | Vanilla JS + Nginx |
| 🗄️ **Database** | Persists user tasks | MySQL 8 |

---

## ⚙️ Architecture Diagram

[Frontend] ──> [Auth Service] ──┐
                               ├──> [MySQL DB]
           ──> [Task Service] ──┘
        (All running on Kubernetes via Ingress)



🧱 Technologies Used
FastAPI (Python 3.11) – REST microservices

MySQL 8 – relational database

Docker & Docker Compose – containerization

Kubernetes (Minikube) – deployment & scaling

Nginx – static frontend serving

GitHub Actions – CI/CD automation

Prometheus / Grafana – optional monitoring



🚀 Project Structure

cloud-todo/
├─ auth-service/
│  ├─ app.py
│  ├─ requirements.txt
│  ├─ Dockerfile
│  └─ tests/
├─ task-service/
│  ├─ app.py
│  ├─ requirements.txt
│  ├─ Dockerfile
│  └─ tests/
├─ frontend/
│  ├─ index.html
│  ├─ main.js
│  └─ Dockerfile
├─ k8s/
│  ├─ mysql/
│  ├─ auth-service/
│  ├─ task-service/
│  ├─ frontend/
│  └─ ingress.yaml
├─ .github/workflows/ci.yaml
└─ docker-compose.yml



🐳 Run Locally with Docker Compose

bash

# 1. Clone the repository
git clone https://github.com/Kaan-YASSIBAS/cloud-todo.git
cd cloud-todo

# 2. Build and run all containers
docker compose up -d --build

# 3. Access the app
Frontend → http://localhost:8080  
Auth API → http://localhost:8001  
Task API → http://localhost:8002



☸️ Deploy on Kubernetes (Minikube Example)

bash

# Start Minikube and enable Ingress
minikube start
minikube addons enable ingress

# Apply all manifests
kubectl apply -f k8s/

# Add to /etc/hosts (use minikube ip)
echo "$(minikube ip)  todo.local" | sudo tee -a /etc/hosts

# Visit the app
http://todo.local



🔄 CI/CD Pipeline

Trigger: On every push to main or dev

Actions:

Build Docker images for all services

Push images to GitHub Container Registry (ghcr.io)

(Optional) Deploy to cluster via kubectl apply

You can find the pipeline file under .github/workflows/ci.yaml.



🧪 Testing

Each service includes simple test scripts using pytest.

Run tests locally:

bash

cd auth-service
pytest

cd ../task-service
pytest



📊 Monitoring (Optional)

Add Prometheus + Grafana stack using kube-prometheus-stack Helm chart.

All services expose /healthz endpoints for readiness/liveness probes.

Example probe snippet:

yaml

livenessProbe:
  httpGet:
    path: /healthz
    port: 8001
  initialDelaySeconds: 10
  periodSeconds: 10



  🌟 Summary

✅ Microservices Architecture (Auth + Task + Frontend)
✅ Containerized with Docker
✅ Deployed on Kubernetes
✅ CI/CD via GitHub Actions
✅ Monitoring ready (Prometheus / Grafana)

“Cloud-native begins with small services — simplicity scales better.”
