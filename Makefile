.PHONY: demo demo-start demo-test demo-browser

DEMO_COMPOSE = DB_CONTAINER_NAME=hirehub_demo_db \
	BACKEND_CONTAINER_NAME=hirehub_demo_backend \
	POSTGRES_PORT=15432 \
	BACKEND_PORT=18000 \
	docker compose -p hirehub-demo

demo-start:
	@if ! docker info >/dev/null 2>&1; then \
		echo "Docker is not running. Start Docker Desktop and retry: make demo"; \
		exit 1; \
	fi
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created local .env from .env.example"; \
	fi
	@echo "Starting HireHub API and PostgreSQL..."
	@if ! $(DEMO_COMPOSE) up --build -d >/dev/null 2>&1; then \
		echo "HireHub startup failed. Recent diagnostics:"; \
		$(DEMO_COMPOSE) ps; \
		$(DEMO_COMPOSE) logs --tail=80 backend db; \
		exit 1; \
	fi

demo: demo-start
	@$(DEMO_COMPOSE) exec backend python demo/run_demo.py

demo-test: demo-start
	@$(DEMO_COMPOSE) exec -T backend pytest demo/test_demo.py -q --no-cov

# Requires the backend on :8000 and frontend on :5173; see demo/browser/README.md.
demo-browser:
	@node demo/browser/record_walkthrough.mjs
