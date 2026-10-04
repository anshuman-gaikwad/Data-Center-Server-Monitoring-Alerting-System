# Interview Questions & Answers

### Why Prometheus?
Prometheus is optimized for numeric time-series telemetry and provides PromQL, scraping and alert rules.

### Why Node Exporter?
It exposes Linux host metrics such as CPU, memory, filesystem, network and load in Prometheus format.

### Why Alertmanager?
It groups, deduplicates and routes Prometheus alerts to notification receivers.

### Why PostgreSQL if Prometheus already stores data?
Prometheus remains the time-series store. PostgreSQL stores application metadata such as users, audit events and maintenance windows.

### How is the health score calculated?
Start at 100 for an available server and subtract transparent penalties for CPU above 60%, memory above 65%, disk above 70%, and high temperature. It is a project-defined indicator, not an industry standard.

### How is arbitrary command execution prevented?
The diagnostic API accepts only a small allowlist of named operations. The frontend cannot submit a shell command string for execution.

### What happens if sensors are unavailable?
Temperature is returned as unavailable; the system never invents sensor values.

### How does the project scale?
Use Prometheus service discovery, remote-write/long-term storage, multiple Prometheus shards/federation, centralized identity and horizontally scaled API/UI services.

### What is the AI/ML component?
The Anomaly Lab is an experimental module that flags unusual resource conditions separately from deterministic alert rules. It can be upgraded to rolling z-score or Isolation Forest baselines using historical Prometheus samples.
