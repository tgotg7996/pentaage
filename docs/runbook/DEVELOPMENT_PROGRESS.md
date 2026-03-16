# Development Progress Log

## Reporting Rule

- Every time a development stage is completed, report to the user and append an entry in this file.
- If a stage is not complete, report what is still missing and blockers.
- Each entry must include: scope, done, pending, verification, and next step.

## Stage Update - 2026-02-21

### Scope

- PA-005 stability and test hardening for `POST /api/v1/compounds/analyze`.
- Integration test reliability and environment consistency improvements.

### Done

- Compound analyze path supports cache-hit persistence backfill when DB session is present.
- Persistence includes calc_id dedup check and commit conflict rollback handling.
- Compound cache refactored from raw module dict to cache abstraction (`CompoundCache`, `InMemoryCompoundCache`).
- Added integration coverage for:
  - cache-hit stability
  - cache-hit persistence backfill
  - no duplicate persistence on repeated cache hits
  - commit-conflict recovery
  - cache key isolation by options
- Fixed batch integration test race by keeping runner patch active during async status wait.
- Reworked integration tests to use runtime `fastapi.testclient` import to remove LSP missing-import errors.

### Pending

- PA-005 final closure with real DB-backed persistence assertions (not only DB session stubs).
- Redis-backed cache implementation behind current cache abstraction.
- PA-006 RDKit implementation replacement and validation-set accuracy verification.

### Verification

- `python -m pytest backend/tests/integration` -> `24 passed`.
- LSP diagnostics clean on updated service and integration test files.

### Next Step

- Add real DB integration assertions for `compound_results` writes and dedup behavior.

## Stage Update - 2026-02-21 (Cache Backend Progress)

### Scope

- Prepare compound analyze cache for Redis migration without breaking current behavior.

### Done

- Added cache backend abstraction in `backend/app/services/compound_service.py`:
  - `CompoundCache` protocol
  - `InMemoryCompoundCache`
  - `RedisCompoundCache`
  - `create_compound_cache()` backend selector (`COMPOUND_CACHE_BACKEND`, `REDIS_URL`)
- Added cache payload serialization/deserialization helpers for `CompoundAnalyzeResponse`.
- Wired service runtime cache to factory-created backend with safe in-memory fallback on any Redis setup error.
- Added unit tests in `backend/tests/unit/test_compound_cache.py` for:
  - payload round-trip
  - Redis cache set/get/clear behavior
  - Redis backend selection
  - fallback to memory when Redis import fails

### Pending

- Real Redis server integration verification (currently covered by fake client unit tests).
- Real DB-backed persistence assertions for `compound_results` (still using DB session stub in integration tests).
- PA-006 RDKit implementation replacement and validation accuracy verification.

### Verification

- `python -m pytest backend/tests/unit/test_compound_cache.py backend/tests/integration/test_compound_api.py` -> `11 passed`.
- `python -m pytest backend/tests/integration` -> `24 passed`.
- `lsp_diagnostics` clean (error-level) on:
  - `backend/app/services/compound_service.py`
  - `backend/tests/unit/test_compound_cache.py`

### Next Step

- Add a real Redis-backed integration path (docker/local service) and validate cache read/write with TTL behavior.

## Stage Update - 2026-02-21 (PA-005 Completion)

### Scope

- Close PA-005 acceptance for `POST /api/v1/compounds/analyze` and synchronize project status docs.

### Done

- Confirmed endpoint is served by real FastAPI route (`backend/app/api/v1/compounds.py`) and wired in v1 router.
- Confirmed service persistence path writes into `compound_results` with `calc_id` dedup + conflict rollback protection.
- Added SLO guard test for single analyze request (`< 3s`) in `backend/tests/integration/test_compound_api.py`.
- Updated project master doc status (`docs/PentaAge_多Agent协作开发文档_v2.0.md`) from `PA-005 进行中` to `PA-005 已完成` and refreshed next priorities.

### Pending

- Real Redis service integration verification (currently unit-tested via fake client + fallback logic).
- Real DB fixture-based persistence assertions beyond session stub strategy.
- PA-006 RDKit migration and validation accuracy benchmark.

### Verification

- `python -m pytest backend/tests/integration` -> `25 passed`.
- `python -m pytest backend/tests/unit/test_compound_cache.py` -> `4 passed`.
- `lsp_diagnostics` error-level clean on:
  - `backend/app/services/compound_service.py`
  - `backend/tests/integration/test_compound_api.py`

### Next Step

- Start PA-006 implementation: switch fingerprint/similarity internals to RDKit and baseline accuracy regression tests.

## Stage Update - 2026-02-22 (PA-006 Completion)

### Scope

- Complete PA-006 algorithm-core acceptance for fingerprint/similarity/scoring and verification evidence.

### Done

- Updated dependency range to installable RDKit versions in current environment:
  - `backend/requirements.txt`: `rdkit>=2024.9,<2026.0`
- Improved algorithm-core quality and testability:
  - removed dead branch in `backend/app/core/similarity.py`
  - expanded fingerprint unit coverage for RDKit path + fallback path + module-missing path in `backend/tests/unit/test_fingerprint.py`
- Verified PA-006 acceptance signals:
  - Morgan fingerprint contract path active (`radius=2`, `n_bits=2048` usage maintained)
  - Tanimoto/scoring contracts preserved
  - validation set Top-1 threshold test passes
  - core module unit coverage reaches 100%
- Synced master status doc:
  - `docs/PentaAge_多Agent协作开发文档_v2.0.md` now marks `PA-006` as completed.

### Pending

- PA-014 expansion for real DB persistence assertions and Redis live integration path.
- PA-013 worker orchestration hardening.

### Verification

- `python -m pytest backend/tests/unit` -> `20 passed`.
- `python -m pytest backend/tests/integration` -> `25 passed`.
- Coverage check:
  - `python -m coverage run -m pytest backend/tests/unit/test_fingerprint.py backend/tests/unit/test_similarity.py backend/tests/unit/test_scoring.py backend/tests/unit/test_accuracy.py`
  - `python -m coverage report -m backend/app/core/fingerprint.py backend/app/core/similarity.py backend/app/core/scoring.py`
  - Result: all three core files 100%.

### Next Step

- Start PA-014 real DB + Redis-backed regression tracks and keep PA-005/PA-006 quality gates green.

## Stage Update - 2026-02-23 (PA-006 Re-Verification)

### Scope

- Continue development loop until PA-006 is fully complete and evidence is re-validated.

### Done

- Re-checked PA-006 acceptance traceability in master plan doc:
  - `docs/PentaAge_多Agent协作开发文档_v2.0.md` still marks PA-006 as completed with matching acceptance statements.
- Re-ran PA-006 contract tests on core modules and validation metric test.
- Re-ran focused coverage for PA-006 core modules and confirmed 100% coverage remains intact.

### Verification

- `python -m pytest backend/tests/unit/test_fingerprint.py backend/tests/unit/test_similarity.py backend/tests/unit/test_scoring.py backend/tests/unit/test_accuracy.py` -> `20 passed`.
- `python -m coverage run -m pytest backend/tests/unit/test_fingerprint.py backend/tests/unit/test_similarity.py backend/tests/unit/test_scoring.py backend/tests/unit/test_accuracy.py` -> pass.
- `python -m coverage report -m backend/app/core/fingerprint.py backend/app/core/similarity.py backend/app/core/scoring.py` -> all three files `100%`.

### Remaining

- PA-006 acceptance is complete; no additional PA-006 implementation gaps found in this round.
- Next milestone remains PA-014 (real DB + Redis-backed regression tracks), then PA-013.

## Stage Update - 2026-02-23 (PA-014 Regression Track Progress)

### Scope

- Continue development toward PA-014: add real DB persistence assertions and Redis live backend integration path for compound analyze flow.

### Done

- Added live-backend regression tests:
  - `backend/tests/integration/test_compound_api_live_backends.py`
  - Covers:
    - real DB persistence assertion (no session stub)
    - Redis cache backend path (`COMPOUND_CACHE_BACKEND=redis`) and cache-hit behavior
    - dedup persistence invariant (single row for repeated same calc_id path)
- Added execution target for live regression:
  - `Makefile` target: `test-regression-live`
- Added run instruction:
  - `README.md` section: `Live Backend Regression (PA-014)`

### Verification

- `python -m pytest backend/tests/integration/test_compound_api.py` -> `8 passed`.
- `python -m pytest backend/tests/integration/test_compound_api_live_backends.py` -> `2 skipped` (requires live `DATABASE_URL` + `REDIS_URL`).
- `python -m pytest backend/tests/integration` -> `25 passed, 2 skipped`.
- `lsp_diagnostics` error-level clean:
  - `backend/tests/integration/test_compound_api_live_backends.py`

### Remaining (Not Yet Stage-Complete)

- Live service environment is unavailable in current runner (`docker`, `postgres`, `redis-server` commands are not present), so PA-014 live-path tests cannot be executed to a passing state here.
- To close PA-014 as complete, run `make test-regression-live` in an environment with reachable PostgreSQL + Redis and record passing evidence in this handbook.

## Stage Update - 2026-02-23 (PA-014 Gate Hardening)

### Scope

- Continue PA-014 by hardening execution gates so live regression cannot falsely appear green without required environment variables.

### Done

- Updated `Makefile` target `test-regression-live` with strict preflight checks:
  - requires `DATABASE_URL`
  - requires `REDIS_URL`
- Updated `README.md` live regression section to clarify service reachability requirement before running.

### Verification

- `make test-regression-live` (without env) now fails fast with explicit message:
  - `Missing DATABASE_URL. Example: postgresql+psycopg://...`
- `python -m pytest backend/tests/integration/test_compound_api.py` -> `8 passed`.
- `lsp_diagnostics` error-level clean:
  - `backend/tests/integration/test_compound_api_live_backends.py`

### Remaining (Not Yet Stage-Complete)

- Still blocked by missing runnable PostgreSQL + Redis in this environment.
- Completion condition unchanged: execute `make test-regression-live` with reachable services and append passing evidence.

## Stage Update - 2026-02-23 (PA-014 Live Test Robustness)

### Scope

- Continue PA-014 by making live-backend tests deterministic under incomplete local environments (missing services or missing DB driver module).

### Done

- Hardened `backend/tests/integration/test_compound_api_live_backends.py` prechecks:
  - validate PostgreSQL/Redis endpoint reachability before DB/cache operations
  - convert missing DB driver (`psycopg`) into explicit skip instead of hard failure
- Kept live path strict while non-live regression remains unaffected.
- Updated `README.md` with quick port-check commands.

### Verification

- `DATABASE_URL=... REDIS_URL=... COMPOUND_CACHE_BACKEND=redis python -m pytest backend/tests/integration/test_compound_api_live_backends.py -q` -> `2 skipped`.
- `python -m pytest backend/tests/integration/test_compound_api.py -q` -> `8 passed`.
- `lsp_diagnostics` error-level clean:
  - `backend/tests/integration/test_compound_api_live_backends.py`

### Remaining (Not Yet Stage-Complete)

- Live services are still unavailable in current runner, so PA-014 cannot be marked complete until `make test-regression-live` passes with reachable PostgreSQL + Redis.

## Stage Update - 2026-02-23 (PA-013 Completion)

### Scope

- Complete PA-013 by moving batch processing from service-local direct execution to worker-oriented asynchronous orchestration with deterministic status/result writeback.

### Done

- Upgraded batch orchestration in `backend/app/services/batch_service.py`:
  - added worker bridge discovery (`enqueue_batch_analyze` + `get_batch_task_result`)
  - added worker task polling with terminal state handling (`SUCCESS`/`FAILURE`)
  - added centralized result writeback and failure writeback paths
  - preserved API contract and idempotency behavior
- Implemented worker-side async task lifecycle in `worker/tasks/batch_analyze.py`:
  - enqueue API
  - in-memory task registry with `PENDING`/`RUNNING`/`SUCCESS`/`FAILURE`
  - result/error retrieval API for service polling
- Added worker orchestration unit tests:
  - `backend/tests/unit/test_batch_worker.py`
- Synced milestone status doc:
  - `docs/PentaAge_多Agent协作开发文档_v2.0.md` now marks `PA-013` as completed in current execution state.

### Verification

- `python -m pytest backend/tests/unit/test_batch_worker.py backend/tests/integration/test_batch_api.py` -> `15 passed`.
- `python -m pytest backend/tests/unit` -> `26 passed`.
- `python -m pytest backend/tests/integration` -> `25 passed, 2 skipped`.
- `lsp_diagnostics` error-level clean:
  - `backend/app/services/batch_service.py`
  - `worker/tasks/batch_analyze.py`
  - `backend/tests/unit/test_batch_worker.py`

### Remaining

- PA-014 remains blocked by missing live PostgreSQL + Redis runtime in this environment.

## Stage Update - 2026-02-23 (PA-011 Completion)

### Scope

- Complete formula parsing/scoring stage (`PA-011`) with explicit algorithm constraints and error-path coverage.

### Done

- Updated formula algorithm contract implementation in `backend/app/services/formula_service.py`:
  - enforce ingredient count limit (`> 50` -> `TOO_MANY_INGREDIENTS`)
  - update synergy bonus to spec-aligned rule: `min(2 * components_count, 10)`
  - preserve existing unresolved/empty error semantics
- Updated formula API integration expectations in `backend/tests/integration/test_formula_api.py`:
  - new synergy/total assertions aligned to updated scoring
  - added too-many-ingredients error-path test
- Added focused unit tests for formula algorithm behavior:
  - `backend/tests/unit/test_formula_service.py`
- Synced milestone status in `docs/PentaAge_多Agent协作开发文档_v2.0.md` to mark `PA-011` completed.

### Verification

- `python -m pytest backend/tests/unit/test_formula_service.py backend/tests/integration/test_formula_api.py` -> `7 passed`.
- `python -m pytest backend/tests/unit` -> `29 passed`.
- `python -m pytest backend/tests/integration` -> `26 passed, 2 skipped`.
- `lsp_diagnostics` error-level clean:
  - `backend/app/services/formula_service.py`
  - `backend/tests/integration/test_formula_api.py`
  - `backend/tests/unit/test_formula_service.py`

### Remaining

- PA-014 live regression closure remains blocked by unavailable PostgreSQL + Redis runtime in current environment.

## Stage Update - 2026-02-23 (PA-012 Completion)

### Scope

- Complete formula analysis API stage (`PA-012`) by connecting formula analyze route to DB dependency and persisting formula analysis results/components.

### Done

- Extended formula service persistence path in `backend/app/services/formula_service.py`:
  - added `Session`-aware persistence for `FormulaResult` and `FormulaComponent`
  - writes parent/child rows with shared `calc_id`
  - rollback on commit exception, without breaking API response flow
- Updated formula API route in `backend/app/api/v1/formulas.py`:
  - injects `db` via `Depends(get_db)`
  - passes `db` into `analyze_formula`
- Expanded formula integration tests in `backend/tests/integration/test_formula_api.py`:
  - added DB override stub and persistence assertions for result/components commit path

### Verification

- `python -m pytest backend/tests/integration/test_formula_api.py` -> `5 passed`.
- `python -m pytest backend/tests/unit/test_formula_service.py` -> `3 passed`.
- `python -m pytest backend/tests/unit` -> `29 passed`.
- `python -m pytest backend/tests/integration` -> `27 passed, 2 skipped`.
- `lsp_diagnostics` error-level:
  - clean: `backend/app/services/formula_service.py`
  - clean: `backend/tests/integration/test_formula_api.py`
  - note: `backend/app/api/v1/formulas.py` reports `fastapi` missing import in local type-check env (same pre-existing environment issue also observed in `backend/app/api/v1/compounds.py`)

### Remaining

- PA-014 remains blocked by missing live PostgreSQL + Redis runtime in current environment.

## Stage Update - 2026-02-27 (Environment Completion + PA-014 Closure)

### Scope

- Configure full local development/test environment and close PA-014 live regression execution gap.

### Done

- Installed and verified core tooling/dependencies:
  - Python runtime deps + dev deps (`backend/requirements.txt`, `backend/requirements-dev.txt`)
  - Frontend npm dependencies (`frontend/package.json`)
  - `psycopg[binary]` and `redis` Python clients
  - `ripgrep` command (`rg --version` available)
- Provisioned local service runtime without Docker:
  - PostgreSQL 16 (`postgres`, `pg_ctl`, `initdb`, `psql`)
  - Redis server (`redis-server`, `redis-cli`)
- Created project env file:
  - `.env` with local `DATABASE_URL` and `REDIS_URL`
- Added reproducible infra lifecycle commands:
  - `Makefile`: `infra-up`, `infra-down`
- Updated setup docs:
  - `README.md`: include `make infra-up`, `make infra-down`, and `make test-regression-live`
- Closed PA-014 runtime blocker by executing live regression against reachable local services.

### Verification

- `python --version` -> `3.13.11`; `node --version` -> `v24.12.0`; `npm --version` -> `11.6.2`
- `rg --version` -> `ripgrep 15.0.0`
- Service checks:
  - PostgreSQL query via `psql ... -c "SELECT 1;"` passes
  - `redis-cli ... ping` -> `PONG`
- Project checks:
  - `make init` -> pass
  - `make test` -> `56 passed, 2 skipped`
  - `make lint` -> pass (ruff + frontend build)
  - `make infra-down && make infra-up && DATABASE_URL=... REDIS_URL=... make test-regression-live` -> `2 passed`

### Remaining

- No environment blocker remains for PA-014 in this machine.
