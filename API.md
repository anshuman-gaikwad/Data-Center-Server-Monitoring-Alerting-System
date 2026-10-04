# API Reference

All `/api/*` endpoints require `Authorization: Bearer <JWT>` except login.

| Endpoint | Purpose | Role |
|---|---|---|
| GET `/health` | Service + Prometheus health | Public |
| POST `/api/auth/login` | JWT login | Public |
| GET `/api/auth/me` | Current user | Any |
| GET `/api/overview` | KPI summary | Any |
| GET `/api/servers` | Inventory + live metrics | Any |
| GET `/api/servers/{id}/metrics` | Prometheus range metrics | Any |
| GET `/api/alerts` | Alertmanager alerts | Any |
| GET `/api/alerts/active` | Active alerts | Any |
| GET `/api/alerts/history` | Alert history | Any |
| POST `/api/alerts/{fingerprint}/acknowledge` | Record acknowledgement | Admin/Operator |
| GET `/api/network` | Network summary | Any |
| GET `/api/disk` | Disk summary | Any |
| GET `/api/system` | Load/temp/uptime | Any |
| GET `/api/anomaly` | Experimental anomaly candidates | Any |
| GET `/api/logs` | Allowlisted log tail | Admin/Operator |
| POST `/api/diagnostics` | Allowlisted diagnostic request | Admin/Operator |
| GET `/api/audit` | Audit history | Admin/Operator |
| GET `/api/maintenance` | Maintenance windows | Any |
| POST `/api/maintenance` | Create maintenance window | Admin/Operator |

Swagger/OpenAPI is available at `/docs`.
