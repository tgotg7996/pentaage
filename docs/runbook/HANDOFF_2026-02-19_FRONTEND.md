Task: Frontend MVP wiring (compound/formula/batch pages)
From: Current Agent
To: Next Agent

已完成:

- 前端运行骨架已补齐（Vite + React + TS）：`frontend/package.json`、`frontend/index.html`、`frontend/src/main.tsx`、`frontend/tsconfig.json`。
- 三个页面已可见并可切换：`frontend/src/App.tsx`。
- 单体分析页面已接入接口并可提交：
  - `frontend/src/api/compounds.ts`
  - `frontend/src/pages/CompoundAnalysis.tsx`
- 方子分析页面已接入接口并可提交：
  - `frontend/src/api/formulas.ts`
  - `frontend/src/pages/FormulaAnalysis.tsx`
- 批量任务页面已接入接口并可提交：
  - `frontend/src/api/batch.ts`
  - `frontend/src/pages/BatchTask.tsx`

未完成:

- 后端 `formulas` / `batch` 真实接口仍未落地（前端已做失败提示兜底）。
- 根目录 `make dev` 仍为占位命令，尚未打通一键联调。
- 批量任务缺少 `status/download` 前端轮询与下载链路。

验证命令:

- `npm run build` (workdir: `frontend`)：passed
- `lsp_diagnostics`:
  - `frontend/src/api/batch.ts` clean
  - `frontend/src/pages/BatchTask.tsx` clean
  - 本轮新增/修改页面与 API 文件无 TS 错误

下一步建议:

- 对接后端 `POST /api/v1/formulas/analyze` 与 `POST /api/v1/batch/submit` 真正实现，去掉当前前端兜底报错路径。
- 增加 `GET /api/v1/batch/{job_id}/status` 轮询和 `download` 按钮。
- 打通根目录 `make dev`（并行启动 backend + frontend）。
