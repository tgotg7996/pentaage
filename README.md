# PentaAge

## Quick Start

```bash
make init
make infra-up
make dev
```

## Common Commands

```bash
make test
make test-regression-live
make lint
```

To stop local PostgreSQL/Redis started by `make infra-up`:

```bash
make infra-down
```

## Live Backend Regression (PA-014)

```bash
export DATABASE_URL="postgresql+psycopg://pentaage:pentaage@127.0.0.1:5432/pentaage"
export REDIS_URL="redis://127.0.0.1:6379/0"
make test-regression-live
```

`test-regression-live` requires both services to be reachable. If PostgreSQL/Redis are not running, start infra services first, then re-run.

Quick port checks:

```bash
python -c "import socket; s=socket.socket(); print('postgres', s.connect_ex(('127.0.0.1',5432))); s.close()"
python -c "import socket; s=socket.socket(); print('redis', s.connect_ex(('127.0.0.1',6379))); s.close()"
```
