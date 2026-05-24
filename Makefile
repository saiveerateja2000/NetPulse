.PHONY: up down api-test frontend-build

up:
docker compose up --build

down:
docker compose down -v

api-test:
cd api-service && pip install -r requirements.txt -r requirements-dev.txt && PYTHONPATH=. pytest -q

frontend-build:
cd frontend && npm run build
