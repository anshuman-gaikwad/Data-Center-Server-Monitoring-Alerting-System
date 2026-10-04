# Architecture & Design

## Components

### Node Exporter
Runs on each Linux server and exposes host metrics over HTTP.

### Prometheus
Scrapes metrics periodically and stores them as time-series data. PromQL powers the alert rules and dashboard queries.

### Alertmanager
Receives firing alerts from Prometheus and handles grouping, routing and notification integrations.

### Grafana
Provides rich operational dashboards for historical and real-time visualization.

### Python FastAPI
A lightweight integration layer used by the custom operations dashboard. It queries Prometheus and Alertmanager and provides a clean REST API.

### React
Professional custom dashboard for server inventory, KPIs, alerts and resource trends.

## Reliability design

- Containers restart automatically.
- Prometheus data persists in a Docker volume.
- Grafana data persists in a Docker volume.
- Alerts have `for` durations to reduce transient noise.
- Monitoring target availability is represented by Prometheus `up`.

## Scaling path

For 10–100+ servers:
1. Use static configuration initially.
2. Move to file-based/service discovery.
3. Add labels for environment, region, team and role.
4. Use remote_write for long-term storage.
5. Introduce Thanos/Cortex/Mimir when retention and scale require it.
6. Add Alertmanager clustering for high availability.
