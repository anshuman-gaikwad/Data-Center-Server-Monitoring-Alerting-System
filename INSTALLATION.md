# Installation

## Local Docker

```bash
cp .env.example .env
# Replace all change-me values for anything beyond a demo.
docker compose up -d --build
docker compose ps
```

Open:
- UI: http://localhost:5173
- API docs: http://localhost:8000/docs
- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093
- Grafana: http://localhost:3000

Demo login: `admin / admin` (change it in `.env`).

## Ubuntu host monitoring

Install Node Exporter on every Linux server. Verify:

```bash
curl http://SERVER_IP:9100/metrics
```

Add targets to `monitoring/prometheus/prometheus.yml`:

```yaml
- job_name: "linux-servers"
  static_configs:
    - targets:
        - "10.0.0.21:9100"
        - "10.0.0.22:9100"
      labels:
        environment: "production"
        role: "application"
```

Then:

```bash
docker compose restart prometheus
```

## Email

Set SMTP variables in `.env`:

```text
SMTP_SMARTHOST=smtp.example.com:587
SMTP_FROM=monitor@example.com
SMTP_AUTH_USERNAME=monitor@example.com
SMTP_AUTH_PASSWORD=...
ALERT_EMAIL_TO=ops@example.com
```

Recreate Alertmanager:

```bash
docker compose up -d --force-recreate alertmanager
```

## Ubuntu production notes

- Put the UI/API behind HTTPS with a reverse proxy.
- Restrict 9090/9093/9100 to trusted networks.
- Use a long random `JWT_SECRET`.
- Use unique database/Grafana passwords.
- Prefer SSH keys and a dedicated least-privilege diagnostic account.
- Back up PostgreSQL and Prometheus volumes.
