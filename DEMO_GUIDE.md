# Interview Demo Guide

1. Start with the architecture: Node Exporter → Prometheus → Alertmanager/Grafana; FastAPI is the secure application/API layer; React is the operator UI; PostgreSQL stores metadata/audit records.
2. Log in as ADMIN and show role-based access.
3. Show Overview KPIs and the explicit DEMO MODE badge if no live target exists.
4. Add a real Linux server as a Prometheus target and refresh.
5. Open Servers and explain the health-score formula.
6. Open Alerts and explain warning/critical/emergency thresholds.
7. Open Metrics and Grafana to demonstrate historical observability.
8. Open Anomaly Lab and explain why anomaly detection is experimental and separate from Prometheus rules.
9. Open Audit & Logs and explain accountability.
10. Explain security: JWT, RBAC, bcrypt, allowlists, env secrets, CORS and restricted ports.
11. Show `docker compose config` and CI checks.
