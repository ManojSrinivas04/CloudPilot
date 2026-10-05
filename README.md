# CloudPilot

CloudPilot is a cloud cost optimization platform that uses workload characteristics and a trained Random Forest model to recommend resource configurations. It evaluates bundled multi-cloud pricing data to compare estimated costs across AWS, Azure, and GCP.

## Features

- JWT authentication with protected API operations.
- User-owned resource create, read, update, and delete operations.
- Hourly, monthly, and yearly resource cost estimation, including storage.
- Random Forest prediction of required vCPU and RAM.
- Multi-cloud pricing comparison across AWS, Azure, and GCP catalog data.
- Persisted recommendation history scoped to the authenticated user.
- Responsive React dashboard with login, registration, and dashboard views.
- Docker and Docker Compose support for the PostgreSQL development environment.

## Architecture

```text
React + TypeScript
        |
      REST
        |
     FastAPI
      /    \
PostgreSQL  ML + Pricing
               |
        AWS / Azure / GCP
```

- **Frontend:** The React and TypeScript application collects user input, manages authentication state, and calls the REST API.
- **API:** FastAPI validates requests, applies JWT access control, and coordinates resources, costs, and recommendations.
- **Database:** PostgreSQL stores users, owned resources, and recommendation history through SQLAlchemy.
- **ML and pricing:** The Random Forest artifact predicts vCPU and RAM. Catalog services then match suitable VM and storage configurations and calculate estimated costs for the supported providers.

## Tech Stack

**Frontend:**
- React
- TypeScript

**Backend:**
- Python
- FastAPI
- SQLAlchemy
- REST APIs
- JWT

**Database:**
- PostgreSQL

**Machine Learning:**
- Scikit-learn
- Random Forest

**Infrastructure:**
- Docker
- Docker Compose

## How It Works

### Recommendation flow

1. The user provides workload characteristics such as application type, user volume, concurrency, storage, region, and traffic pattern.
2. The Random Forest model predicts the required vCPU and RAM.
3. The pricing engine evaluates suitable VM and storage configurations across AWS, Azure, and GCP.
4. The system compares estimated hourly, monthly, and yearly costs and identifies the cheapest suitable option.
5. A recommendation can be stored for the authenticated user and viewed later through recommendation history.

### Resource cost flow

An authenticated user creates or updates a resource with its provider, region, capacity, storage, and hourly cost. The cost service combines the hourly compute estimate with the provider's catalog storage rate, then returns monthly and yearly totals through the resource cost endpoint.

## Project Structure

```text
CloudPilot/
├── backend/
│   └── app/                 # FastAPI app, API routes, models, schemas, and services
├── frontend/
│   └── web/                 # Vite React + TypeScript frontend
├── ml/                      # Preprocessing, VM/storage catalogs, and region pricing
├── models/                  # cloud_model.pkl and model_features.pkl
├── datasets/                # Training dataset
├── tests/                   # Backend unit and API tests
├── docker-compose.yml       # PostgreSQL development service
├── requirements.txt         # Python dependencies
└── .env.example             # Local environment variable template
```

## API Overview

The current FastAPI application mounts these routes under `/api`:

| Area | Routes | Purpose |
| --- | --- | --- |
| Authentication | `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me` | Register, authenticate, and retrieve the current user. |
| Resources | `POST /api/resources`, `GET /api/resources`, `GET /api/resources/{resource_id}`, `PATCH /api/resources/{resource_id}`, `DELETE /api/resources/{resource_id}` | Manage resources owned by the authenticated user. |
| Resource cost | `GET /api/resources/{resource_id}/cost` | Calculate estimated costs for an owned resource. |
| Recommendations | `POST /api/recommendations`, `GET /api/recommendations`, `GET /api/recommendations/{recommendation_id}` | Create and retrieve user-scoped recommendation history. |
| Prediction | `POST /api/predict`, `POST /api/predict/compare` | Predict resource needs and recommend or compare suitable cloud configurations. |
| Supported options | `GET /api/supported-options` | Return supported application types, regions, and traffic patterns. |
| Health check | `GET /health` | Report API health and version. |

Interactive API documentation is available at `/docs` when the backend is running.

## Running Locally

### Docker Compose setup

Docker Compose currently provides the PostgreSQL database only. The FastAPI backend and React/Vite frontend run separately as local development processes.

1. Clone the repository and enter its directory:

   ```bash
   git clone <repository-url>
   cd Finops_AI
   ```

2. Copy `.env.example` to `.env` and replace placeholder values, especially `POSTGRES_PASSWORD` and `JWT_SECRET_KEY`.

   ```bash
   cp .env.example .env
   ```

3. Start the Compose services:

   ```bash
   docker compose up
   ```

   PostgreSQL starts on `127.0.0.1:5432`; no backend or frontend containers are defined in the current Compose file.

4. Start the backend in a second terminal:

   ```bash
   python -m uvicorn backend.app.main:app --reload
   ```

5. Start the frontend in a third terminal:

   ```bash
   cd frontend/web
   npm install
   npm run dev
   ```

   Open the frontend at `http://127.0.0.1:5173`. The Vite port can be overridden with its `--port` option, and the API base URL can be set with `VITE_API_BASE_URL`. Backend database and JWT settings are configured through `.env`.

### Non-Docker option

The backend requires PostgreSQL. With PostgreSQL already running and `DATABASE_URL` configured in `.env`, start the backend and frontend using the commands above without running Compose.

## Testing

The project verification includes:

- 32 backend `unittest` tests.
- Frontend production build with `npm run build`.
- Docker container health checks.
- SQLAlchemy/PostgreSQL connectivity check.
- End-to-end browser workflow covering registration, login, resource creation, cost retrieval, recommendation generation and history, and logout.
- Responsive checks across desktop and mobile viewports.

These checks do not represent 100% test coverage.

## Machine Learning

The model artifact is a Random Forest regressor. It uses workload characteristics to predict required vCPU and RAM; it does not directly predict cloud provider pricing. The pricing engine separately evaluates suitable configurations from the AWS, Azure, and GCP catalog data. The artifact is loaded with scikit-learn; the inference environment should match the artifact's training version for reproducible results.

## Future Improvements

- Use larger real-world workload and pricing datasets.
- Improve recommendation accuracy.
- Add more comprehensive automated testing.
- Add application logging and monitoring.
- Improve dashboard comparison of current versus recommended configuration.
