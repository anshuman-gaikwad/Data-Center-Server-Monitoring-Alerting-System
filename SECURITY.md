# Security

## Implemented

- JWT authentication with 8-hour expiry.
- Roles: ADMIN, OPERATOR, VIEWER.
- Passwords are bcrypt-hashed before persistence.
- Explicit CORS origins.
- Request validation through Pydantic.
- Diagnostic commands are allowlisted; frontend input cannot become arbitrary shell commands.
- Log paths are allowlisted.
- Audit events are persisted in PostgreSQL.
- Docker services use private networks and health checks.
- Frontend adds security headers through Nginx.
- Secrets are supplied through environment variables.

## Production hardening

1. Replace every default credential.
2. Generate a random 32+ byte JWT secret.
3. Use TLS for the UI/API.
4. Restrict Prometheus, Alertmanager and Node Exporter with firewall/VPN rules.
5. Use a dedicated SSH account with minimal sudo permissions.
6. Store secrets in Vault/Kubernetes Secrets/cloud secret managers.
7. Rotate credentials.
8. Add rate limiting and centralized identity (OIDC) for enterprise deployments.
