.PHONY: help
help:
	@echo "Доступные команды."
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

COMPOSE := docker compose --env-file .env

.PHONY: app
app: ## Запустить приложение
	uv run -m app.manage runserver

.PHONY: format
format: ## Форматировать код
	@printf "Вы хотите применить команду в контейнере? [Y/n]: " && read ans; \
	if [ "$$ans" = "y" ] || [ "$$ans" = "Y" ] || [ -z "$$ans" ]; then \
		echo "Выполняю в контейнере..."; \
		$(COMPOSE) exec battleship-app ruff format; \
	else \
		echo "Выполняю локально..."; \
		uv run ruff format; \
	fi

.PHONY: migrate
migrate: ## Применить миграции базы данных
	@printf "Вы хотите применить команду в контейнере? [Y/n]: " && read ans; \
	if [ "$$ans" = "y" ] || [ "$$ans" = "Y" ] || [ -z "$$ans" ]; then \
		echo "Выполняю в контейнере..."; \
		$(COMPOSE) exec battleship-app python -m app.manage migrate; \
	else \
		echo "Выполняю локально..."; \
		uv run -m app.manage migrate; \
	fi

.PHONY: makemigrations
makemigrations: ## Создать новые миграции на основе изменений в моделях
	@printf "Вы хотите применить команду в контейнере? [Y/n]: " && read ans; \
	if [ "$$ans" = "y" ] || [ "$$ans" = "Y" ] || [ -z "$$ans" ]; then \
		echo "Выполняю в контейнере..."; \
		$(COMPOSE) exec battleship-app python -m app.manage makemigrations; \
	else \
		echo "Выполняю локально..."; \
		uv run -m app.manage makemigrations; \
	fi

.PHONY: createsuperuser
createsuperuser: ## Создать суперпользователя
	@printf "Вы хотите применить команду в контейнере? [Y/n]: " && read ans; \
	if [ "$$ans" = "y" ] || [ "$$ans" = "Y" ] || [ -z "$$ans" ]; then \
		echo "Выполняю в контейнере..."; \
		$(COMPOSE) exec battleship-app python -m app.manage createsuperuser; \
	else \
		echo "Выполняю локально..."; \
		uv run -m app.manage createsuperuser; \
	fi

.PHONY: shell
shell: ## Запустить интерактивную консоль
	@printf "Вы хотите применить команду в контейнере? [Y/n]: " && read ans; \
	if [ "$$ans" = "y" ] || [ "$$ans" = "Y" ] || [ -z "$$ans" ]; then \
		echo "Выполняю в контейнере..."; \
		$(COMPOSE) exec battleship-app python -m app.manage shell; \
	else \
		echo "Выполняю локально..."; \
		uv run -m app.manage shell; \
	fi

.PHONY: build
build: ## Собрать образы
	$(COMPOSE) build

.PHONY: up
up: ## Поднять приложение в контейнерах
	$(COMPOSE) up

.PHONY: stop
stop: ## Остановить приложение без удаления контейнеров
	$(COMPOSE) stop

.PHONY: down
down: ## Остановить приложение с удалением контейнеров
	$(COMPOSE) down

.PHONY: clean
clean: ## Остановить приложение с удалением контейнеров и томов
	$(COMPOSE) down -v