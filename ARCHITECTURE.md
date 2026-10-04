# Architecture

```text
                         +----------------------+
                         |   Linux Servers      |
                         | CPU/RAM/Disk/Network |
                         +----------+-----------+
                                    |
                              Node Exporter :9100
                                    |
                                    v
+----------------+        +----------------------+
| React UI       | <----> | FastAPI API          |
| Operations     |        | JWT / RBAC / Audit   |
| Center         |        +----------+-----------+
+-------+--------+                   |
        |                            +------ PostgreSQL (metadata)
        |                            |
        |                      Prometheus API
        |                            |
        v                            v
+---------------+              +-----------+
| Grafana       | <------------| Prometheus|
| dashboards    |              | TSDB      |
+---------------+              +-----+-----+
                                      |
                                 Alert rules
                                      |
                                      v
                               +-------------+
                               | Alertmanager|
                               +------+------+ 
                                      |
                                Email/Webhook
```

## Design principles

- Prometheus owns time-series data; PostgreSQL stores application metadata/audit information.
- React never talks directly to Prometheus or Alertmanager.
- FastAPI is the policy boundary for authentication, authorization and safe operations.
- Deterministic Prometheus alerts are separate from the experimental anomaly module.
- Demo data is shown only when the live Prometheus path is unavailable; the UI labels it explicitly.
- SSH diagnostics use an allowlist and are intentionally not arbitrary shell execution.
