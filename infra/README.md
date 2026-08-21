# Local Infrastructure Guide (`/infra`)

This directory contains the Docker Compose environment for running the sample PostgreSQL database and Qdrant vector store locally.

## Services
1. **PostgreSQL 16 (`postgres-sample`)**:
   - Host: `localhost`
   - Port: `5432`
   - Database: `ecommerce_demo`
   - User: `postgres`
   - Password: `postgres`
   - Auto-seeded with: `customers`, `products`, `orders`, `order_items`, `refunds`, `glossary_terms`, `audit_logs`.

2. **Qdrant Vector DB (`qdrant`)**:
   - HTTP REST API: `http://localhost:6333`
   - Web UI / Dashboard: `http://localhost:6333/dashboard`
   - gRPC Port: `6334`

## Commands

```bash
# Start all infrastructure in background
docker compose up -d

# Check status and health
docker compose ps

# View database initialization logs
docker compose logs -f postgres-sample

# Stop infrastructure
docker compose down

# Stop and wipe persistent volume data (fresh reset)
docker compose down -v
```
