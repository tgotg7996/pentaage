Task: Context handoff before session reset
From: Current Agent
To: Next Agent

已完成:

- Batch 链路已打通基础闭环：`submit -> status -> download`，前端已接入轮询与下载。
- Batch `options` 参数已收口：后端解析 JSON，非法输入返回 `400/BATCH_FILE_INVALID`。
- Formula 接口已补齐错误场景：`EMPTY_INGREDIENTS` 与 `ALL_UNRESOLVED`。
- Formula / Batch 集成测试占位已替换为真实接口测试（依赖环境未就绪，见阻塞项）。
- 本轮新增改动：`POST /api/v1/batch/submit` 已按契约返回 `202`，并同步更新测试断言。
- 本轮新增改动：`batch submit` 返回状态调整为 `pending`，并补齐下载前置条件校验（未完成返回 `JOB_NOT_COMPLETED`）。
- 本轮新增改动：补齐批量文件约束校验（CSV 头必须为 `smiles`、行数上限 10000、大小上限 10MB）。
- 本轮新增改动：状态流转细化为 `pending -> running -> completed`，并在服务层接入 `worker/tasks/batch_analyze.py` 作为分析执行入口（动态加载，缺失时回退最小实现）。
- 本轮新增改动：`test_batch_api` 补齐 `running` 阶段断言与运行中下载拦截校验。
- 本轮新增改动：`batch_submit` 增加 CSV UTF-8 解码异常映射，编码异常统一返回 `BATCH_FILE_INVALID`。
- 本轮新增改动：`batch_download` 响应 `media_type` 调整为 `application/octet-stream` 以对齐接口手册。
- 本轮新增改动：新增集成测试覆盖非法文件编码场景。
- 本轮新增改动：`submit` 后即启动后台线程处理任务，状态推进从“轮询副作用”改为“异步执行回写”。
- 本轮新增改动：`status` 接口改为只读，不再触发状态变更。
- 本轮新增改动：`test_batch_api` 增加异步等待完成辅助函数，适配异步状态流转。
- 本轮新增改动：异步执行增加异常兜底，runner 报错时任务状态回写为 `failed`，并写入失败计数避免任务卡在 `running`。
- 本轮新增改动：新增集成测试覆盖 runner 异常场景，校验 `failed` 状态与下载拦截行为。
- 本轮新增改动：新增 `GET /api/v1/health` 接口，返回 `healthy + components(db/redis/rdkit)` 结构。
- 本轮新增改动：`v1 router` 已接入 health 路由。
- 本轮新增改动：新增 `test_health_api` 集成测试覆盖健康检查返回结构。
- 本轮新增改动：前端 `BatchTask` 轮询逻辑已识别 `failed` 状态并停止继续轮询，避免失败任务无限轮询。
- 本轮新增改动：前端在任务失败时增加错误提示文案，完成态仍保留下载入口。

本轮未完成:

- 本地无法执行 pytest（环境缺少 `pytest`）。
- basedpyright 在 backend API 与 integration tests 中仍报 `fastapi`/`fastapi.testclient` 依赖未解析（环境问题）。
- 当前 `batch_service.py` 仅剩 basedpyright `Any` 级别 warning（动态导入 runner 所致），无新增 error。
- 当前 `test_batch_api.py` 存在 basedpyright `Any` 级 warning（测试工具类型缺失 + json动态结构），不影响运行语义。
- 本地无法验证新增失败场景测试（缺少 `pytest` 依赖）。
- 本地无法验证 health 集成测试（缺少 `pytest` 依赖）。

本轮变更文件:

- backend/app/api/v1/batch.py
- backend/app/services/batch_service.py
- backend/tests/integration/test_batch_api.py
- backend/tests/integration/test_health_api.py
- frontend/src/pages/BatchTask.tsx
- worker/tasks/batch_analyze.py
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
3. 进入下一个实现项：将当前内存态状态推进替换为真实异步 worker 触发与回写（避免依赖轮询副作用推进状态）。

交接第一步:

- 先执行 `git status --short` 确认当前仅有本轮三文件改动，再进行提交或继续开发。
