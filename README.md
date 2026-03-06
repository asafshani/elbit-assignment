# Jewish Holidays API — DevOps Assignment

A containerized Python web application that fetches Jewish holiday data for the upcoming quarter and displays it via a secure HTTPS endpoint returning JSON. Deployed on a local Kubernetes cluster using Pulumi as Infrastructure as Code.

## Architecture Overview

```
Client (Browser)
    |
    | HTTPS (TLS)
    v
Nginx Ingress Controller
    |
    v
K8s Service (ClusterIP)
    |
    v
K8s Deployment (2 replicas)
    |
    v
Python App Container (non-root user)
    |
    | REST API call
    v
Hebcal Public API (Jewish Calendar)
```

## Tech Stack

- **Application:** Python 3.12 (HTTP server using standard library)
- **Containerization:** Docker (non-root user for security)
- **Orchestration:** Kubernetes (Minikube on Hyper-V)
- **Infrastructure as Code:** Pulumi (Python)
- **TLS/HTTPS:** Self-signed certificate via Nginx Ingress
- **Secret Management:** Pulumi encrypted secrets
- **Configuration:** Pulumi Config + Kubernetes ConfigMap

## Project Structure

```
elbit-assignment/
├── app.py                  # Python web application
├── Dockerfile              # Container image definition
├── .gitignore              # Git ignore rules
├── README.md               # This file
└── infra/                  # Pulumi infrastructure code
    ├── __main__.py         # Pulumi deployment definitions
    ├── Pulumi.yaml         # Pulumi project configuration
    ├── Pulumi.dev.yaml     # Pulumi stack configuration (dev)
    └── requirements.txt    # Python dependencies for Pulumi
```

## Prerequisites

- Windows 11 Pro with Hyper-V enabled
- Docker Desktop
- Minikube
- kubectl
- Pulumi CLI
- Python 3.12+

## Setup & Deployment

### 1. Clone the repository

```bash
git clone https://github.com/asafshani/elbit-assignment.git
cd elbit-assignment
```

### 2. Build the Docker image

```bash
docker build -t jewish-holidays-app:1.0.0 .
```

### 3. Start Minikube and load the image

```bash
minikube start --driver=hyperv
minikube addons enable ingress
minikube image load jewish-holidays-app:1.0.0
```

### 4. Create TLS certificate

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=jewish-holidays.local"

kubectl create secret tls jewish-holidays-tls --cert=tls.crt --key=tls.key
```

### 5. Deploy with Pulumi

```bash
cd infra
python -m venv venv
.\venv\Scripts\activate       # Windows
pip install -r requirements.txt
pip install pulumi-kubernetes

pulumi login --local
pulumi stack init dev
pulumi config set containerImage jewish-holidays-app:1.0.0
pulumi config set replicas 2
pulumi config set cpuRequest 100m
pulumi config set memoryRequest 128Mi
pulumi config set --secret apiKey my-super-secret-api-key-2026
pulumi up
```

### 6. Configure local DNS

Add the Minikube ingress IP to your hosts file:

```bash
# Get the ingress IP
kubectl get ingress

# Add to hosts file (run as Administrator)
Add-Content C:\Windows\System32\drivers\etc\hosts "<INGRESS-IP> jewish-holidays.local"
```

### 7. Access the application

Open in browser: `https://jewish-holidays.local/holidays`

> Note: The browser will show a certificate warning because we use a self-signed certificate. This is expected for local development. In production, you would use cert-manager with Let's Encrypt for trusted certificates.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/holidays` | GET | Returns Jewish holidays for the upcoming quarter |
| `/health` | GET | Health check endpoint |

## Sample Response

```json
{
  "description": "Jewish holidays for the upcoming quarter",
  "period": {
    "from": "2026-03-06",
    "to": "2026-06-04"
  },
  "total_holidays": 14,
  "holidays": [
    {
      "name": "Erev Pesach",
      "hebrew": "ערב פסח",
      "date": "2026-04-01",
      "category": "holiday"
    }
  ]
}
```

## Pulumi Configuration

The deployment is parameterized using Pulumi Config:

| Key | Description | Default |
|-----|-------------|---------|
| `containerImage` | Docker image to deploy | `jewish-holidays-app:1.0.0` |
| `replicas` | Number of pod replicas | `2` |
| `cpuRequest` | CPU request per pod | `100m` |
| `cpuLimit` | CPU limit per pod | `250m` |
| `memoryRequest` | Memory request per pod | `128Mi` |
| `memoryLimit` | Memory limit per pod | `256Mi` |
| `apiKey` | Secret API key (encrypted) | — |

## Security Features

- **Non-root container:** Application runs as `appuser`, not root
- **TLS/HTTPS:** Ingress configured with TLS termination
- **Secret management:** Sensitive values encrypted using Pulumi secrets
- **Resource limits:** CPU and memory limits prevent resource abuse
- **Health checks:** Liveness and readiness probes ensure application health

## Kubernetes Resources Created

- **Deployment** — 2 replicas of the application
- **Service** (ClusterIP) — Internal load balancing
- **Ingress** (Nginx) — External access with TLS
- **ConfigMap** — Application environment configuration
- **Secret** — Sensitive configuration data

## Production Considerations

In a production environment, the following improvements would be made:

- Use a managed Kubernetes cluster (EKS/AKS/GKE)
- Use cert-manager with Let's Encrypt for trusted TLS certificates
- Use an external secret manager (AWS Secrets Manager, Azure Key Vault)
- Add Horizontal Pod Autoscaler (HPA) for automatic scaling
- Set up monitoring with Prometheus and Grafana
- Implement a CI/CD pipeline for automated deployments
- Add network policies for pod-to-pod communication security