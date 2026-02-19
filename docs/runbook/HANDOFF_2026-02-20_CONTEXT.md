Task: Context handoff before session reset
From: Current Agent
To: Next Agent

已完成:

- Batch 链路已打通基础闭环：`submit -> status -> download`，前端已接入轮询与下载。
- Batch `options` 参数已收口：后端解析 JSON，非法输入返回 `400/BATCH_FILE_INVALID`。
- Formula 接口已补齐错误场景：`EMPTY_INGREDIENTS` 与 `ALL_UNRESOLVED`。
- Formula / Batch 集成测试占位已替换为真实接口测试（依赖环境未就绪，见阻塞项）。
- 本轮新增改动：`POST /api/v1/batch/submit` 已按契约返回 `202`，并同步更新测试断言。

本轮未完成:

- 本地无法执行 pytest（环境缺少 `pytest`）。
- basedpyright 在 backend API 与 integration tests 中仍报 `fastapi`/`fastapi.testclient` 依赖未解析（环境问题）。

本轮变更文件:

- backend/app/api/v1/batch.py
- backend/tests/integration/test_batch_api.py
- docs/runbook/HANDOFF_2026-02-20_CONTEXT.md

近期关键提交:

- `0d931cf` feat: 打通batch状态查询与结果下载链路
- `7526e24` test: 补齐batch提交状态下载集成测试
- `c31ac8f` test: 补齐formula分析接口集成测试
- `5e0ba3a` feat: 收口batch options参数并补齐异常测试
- `67800a3` feat: 补齐formula空成分与全未解析错误处理

建议下一步（按优先级）:

1. 安装后端测试依赖后执行：`python -m pytest backend/tests/integration/test_batch_api.py backend/tests/integration/test_formula_api.py`
2. 统一 backend 运行环境，消除 `fastapi`/`fastapi.testclient` 的 LSP 误报。
3. 进入下一个契约收口项：`Idempotency-Key`（`POST /batch/submit`）最小实现与测试。

交接第一步:

- 先执行 `git status --short` 确认当前仅有本轮三文件改动，再进行提交或继续开发。
