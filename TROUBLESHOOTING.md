# Troubleshooting

### UI says DEMO MODE
Check:
```bash
docker compose ps
curl http://localhost:8000/health
curl http://localhost:9090/-/healthy
```
Then verify Prometheus has a `linux-servers` target.

### No servers appear
Confirm Node Exporter:
```bash
curl http://SERVER:9100/metrics
```
Check the target in Prometheus → Status → Targets.

### Alerts do not email
Verify SMTP variables and:
```bash
docker compose logs alertmanager
```

### Temperature is Unavailable
This is expected when Linux hardware sensors are not exposed to Node Exporter. The project intentionally does not fabricate temperature values.

### PostgreSQL error
```bash
docker compose logs postgres
docker compose up -d postgres
```

### Rebuild after code changes
```bash
docker compose up -d --build
```
