# Interview Guide

## Explain the project in 30 seconds

"I built a Linux data-center monitoring and alerting platform. Node Exporter exposes server-level metrics, Prometheus collects and stores them, PromQL evaluates infrastructure health, Alertmanager routes alerts, and Grafana provides historical dashboards. I also built a React operations dashboard backed by FastAPI so an administrator can see server status, CPU, memory, disk and alerts from one place."

## Technologies and why

| Technology | Purpose |
|---|---|
| Linux/Ubuntu | Target infrastructure |
| Bash | Server health and disk diagnostics |
| Node Exporter | Host metric exporter |
| Prometheus | Metrics collection and time-series database |
| PromQL | Queries and alert conditions |
| Alertmanager | Alert routing/deduplication |
| Grafana | Operational visualization |
| Python/FastAPI | Custom REST integration layer |
| React/Vite | Professional monitoring UI |
| Docker | Reproducible deployment |
| TCP/IP | Network communication between components |
| SSH | Secure administration/remote diagnostics |

## Key mechanisms

### CPU
Node Exporter exposes CPU counters. Prometheus uses `rate()` to calculate utilization over time and the alert fires when usage remains above the threshold.

### RAM
Memory usage is calculated from total memory minus available memory.

### Disk
Filesystem available bytes are compared with filesystem size to calculate utilization.

### Server down
Prometheus checks the target's `up` metric. `0` means the scrape failed.

### Alert noise control
Rules use `for: 5m`, `for: 10m`, etc. so short spikes do not immediately page an administrator.

## Future improvements

- Kubernetes/Kube State Metrics
- SNMP exporter for switches/routers
- Windows Exporter
- ML-based anomaly detection
- SSO/RBAC
- Slack/Teams/PagerDuty
- Maintenance windows
- Capacity forecasting
- Multi-region monitoring
