test:
	pytest ./

dev:
	DOCKER_BUILDKIT=1 docker compose -f docker-compose.dev.yml build backend-core
	DOCKER_BUILDKIT=1 docker compose -f docker-compose.dev.yml up --build

prod:
	docker compose build backend-core
	docker compose -f docker-compose.yml up --build
