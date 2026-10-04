up:
	docker compose up -d --build
down:
	docker compose down
logs:
	docker compose logs -f --tail=200
test:
	cd backend && pytest -q
build-ui:
	cd frontend && npm install && npm run build
validate:
	docker compose config
