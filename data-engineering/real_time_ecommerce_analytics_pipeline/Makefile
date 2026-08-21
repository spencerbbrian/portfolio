ENV_FLAGS=--env-file .env --env-file .env.airflow

up:
	docker compose $(ENV_FLAGS) up -d

down:
	docker compose $(ENV_FLAGS) down

init:
	docker compose $(ENV_FLAGS) up airflow-init

logs:
	docker compose $(ENV_FLAGS) logs -f

ps:
	docker compose $(ENV_FLAGS) ps

restart:
	docker compose $(ENV_FLAGS) restart

exec-dags-ls:
	docker compose $(ENV_FLAGS) exec airflow-scheduler ls /opt/airflow/dags