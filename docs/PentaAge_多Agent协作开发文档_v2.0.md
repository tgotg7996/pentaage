# PentaAge 多Agent协作开发文档（执行版）

## 0. 文档信息

| 项目     | 内容                                                  |
| :------- | :---------------------------------------------------- |
| 文档版本 | v3.1（多Agent协同执行版，含ULW流程）                 |
| 更新日期 | 2026-02-19                                            |
| 项目名称 | PentaAge - 五单体抗衰老药物预测平台                   |
| 适用阶段 | MVP（8周）+ 可扩展到v1.0                              |
| 面向团队 | 多Agent协同开发（产品、算法、后端、前端、测试、运维） |
| 文档目标 | 从“方案描述”升级为“可并行落地的开发契约”              |

---

## 1. 文档使用方式（关键）

本文件是团队的**单一事实来源（Single Source of Truth）**。多Agent协作时按以下优先级执行：

1. 本文档中的接口契约、数据契约、验收标准高于口头描述。
2. 任何影响跨模块的改动，必须先更新本文档对应章节，再提交代码。
3. 任务拆分、分支、PR、测试、发布，统一遵循第8-13章协作规则。
4. 如出现冲突：`安全/数据正确性 > 可用性 > 性能 > 开发效率`。
5. 日常协作默认启用ULW（UltraWork）执行节奏：并行探索、最小改动、证据交付。

---

## 2. 项目定义与边界

### 2.1 项目目标

构建一个可用于中医药研究场景的化合物抗衰老潜力评估平台，支持：

1. 单体相似度比对（名称/CAS/SMILES/MOL）。
2. 中药方子成分聚合评分。
3. 批量化合物计算与报告导出。

### 2.2 MVP范围（必须完成）

1. 五单体基准库（含可复现指纹）。
2. `/api/v1/compounds/analyze`、`/api/v1/formulas/analyze`、`/api/v1/batch/*` 基础能力。
3. Web端三页：单体分析、方子分析、批量任务。
4. 异步任务队列（提交、查询、下载）。
5. 最小可运维能力（日志、健康检查、错误告警）。

### 2.3 非MVP范围（延后）

1. 复杂QSAR/深度学习模型。
2. 多租户企业权限系统。
3. 自动化实验闭环（LIMS双向联动）。
4. 大规模结构编辑器高级功能（保留接口）。

---

## 3. 成功指标（可验收）

### 3.1 功能正确性

1. 单体比对：对验证集Top-1最相似基准命中率 >= 85%（MVP目标）。
2. 方子评分：输入成分全量返回，缺失成分有明确标记和原因。
3. 批量任务：1000条SMILES任务完成率 >= 99%（无效输入除外）。

### 3.2 性能SLO

1. `single analyze`：P95 < 3秒（冷启动除外）。
2. `formula analyze`（<= 50成分）：P95 < 8秒。
3. `batch submit`接口：P95 < 500ms（仅提交任务）。
4. 批量计算吞吐：1000条在10分钟内完成（标准4核8G环境）。

### 3.3 稳定性

1. API可用性 >= 99.5%（月）。
2. 批任务失败可重试成功率 >= 95%。
3. 未捕获异常为0（上线后阻断级别）。

---

## 4. 技术架构（落地版）

### 4.1 服务边界

1. `frontend`：React + Zustand + Ant Design，负责交互与可视化。
2. `api`：FastAPI，负责参数校验、鉴权、业务编排。
3. `engine`：RDKit计算核心（可在api内模块化，后续可独立服务化）。
4. `worker`：Celery异步批处理。
5. `postgres`：业务数据与计算结果。
6. `redis`：缓存、队列Broker、短期状态。
7. `minio`（可选）：批处理导出文件存储。

### 4.2 核心数据流（必须一致）

#### F-001 单体分析

`输入解析 -> SMILES标准化 -> Morgan指纹 -> 五单体Tanimoto -> 评分 -> 入库 -> 返回`

#### F-002 方子分析

`方剂输入 -> 成分解析 -> 每成分执行F-001 -> 加权聚合 -> 协同指数 -> 入库 -> 返回`

#### F-003 批量分析

`上传CSV -> 创建batch_job -> worker分片执行F-001 -> 结果汇总CSV/JSON -> 下载地址`

### 4.3 缓存策略

1. Key：`fp:{canonical_smiles}:{radius}:{bits}`。
2. TTL：30天（命中后滑动续期可选）。
3. 缓存击穿保护：同key加互斥锁（5秒）。

### 4.4 项目目录结构（所有Agent必须遵守）

```
pentaage/
├── backend/                    # Agent-1 & Agent-2 主责
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI 入口
│   │   ├── config.py           # 统一配置（环境变量加载）
│   │   ├── dependencies.py     # FastAPI 依赖注入
│   │   ├── core/               # Agent-1 主责：算法核心
│   │   │   ├── __init__.py
│   │   │   ├── fingerprint.py  # Morgan指纹计算
│   │   │   ├── similarity.py   # Tanimoto相似度
│   │   │   ├── scoring.py      # 评分公式
│   │   │   ├── formula.py      # 方子解析与聚合
│   │   │   └── reference.py    # 基准数据加载
│   │   ├── api/                # Agent-2 主责：接口层
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py
│   │   │   │   ├── compounds.py
│   │   │   │   ├── formulas.py
│   │   │   │   └── batch.py
│   │   │   └── deps.py
│   │   ├── models/             # Agent-2 主责：数据模型
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # SQLAlchemy Base
│   │   │   ├── compound.py
│   │   │   ├── formula.py
│   │   │   └── batch.py
│   │   ├── schemas/            # Agent-2 主责：Pydantic schemas（前后端契约）
│   │   │   ├── __init__.py
│   │   │   ├── common.py       # 通用响应/分页
│   │   │   ├── compound.py
│   │   │   ├── formula.py
│   │   │   └── batch.py
│   │   ├── services/           # Agent-2 主责：业务逻辑编排
│   │   │   ├── __init__.py
│   │   │   ├── compound_service.py
│   │   │   ├── formula_service.py
│   │   │   └── batch_service.py
│   │   └── utils/              # 共享工具函数
│   │       ├── __init__.py
│   │       ├── logger.py
│   │       └── validators.py
│   ├── alembic/                # Agent-2 主责：DB迁移
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/                  # Agent-5 主责，各Agent配合
│   │   ├── unit/
│   │   │   ├── test_fingerprint.py
│   │   │   ├── test_similarity.py
│   │   │   └── test_scoring.py
│   │   ├── integration/
│   │   │   ├── test_compound_api.py
│   │   │   ├── test_formula_api.py
│   │   │   └── test_batch_api.py
│   │   ├── e2e/
│   │   ├── fixtures/
│   │   │   ├── reference_compounds.json
│   │   │   └── validation_set.json
│   │   └── conftest.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── pyproject.toml
├── worker/                     # Agent-4 主责
│   ├── celery_app.py
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── batch_analyze.py
│   │   └── cleanup.py
│   └── Dockerfile
├── frontend/                   # Agent-3 主责
│   ├── src/
│   │   ├── api/                # API调用层（对齐后端schemas）
│   │   │   ├── client.ts
│   │   │   ├── compounds.ts
│   │   │   ├── formulas.ts
│   │   │   └── batch.ts
│   │   ├── components/
│   │   │   ├── common/
│   │   │   ├── compound/
│   │   │   ├── formula/
│   │   │   └── batch/
│   │   ├── pages/
│   │   │   ├── CompoundAnalysis.tsx
│   │   │   ├── FormulaAnalysis.tsx
│   │   │   └── BatchTask.tsx
│   │   ├── stores/             # Zustand状态管理
│   │   ├── types/              # TypeScript类型（对齐后端schemas）
│   │   │   ├── api.ts          # 通用响应类型
│   │   │   ├── compound.ts
│   │   │   ├── formula.ts
│   │   │   └── batch.ts
│   │   ├── hooks/
│   │   ├── utils/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── infra/                      # Agent-4 主责
│   ├── docker/
│   │   ├── docker-compose.yml
│   │   ├── docker-compose.dev.yml
│   │   ├── Dockerfile.backend
│   │   ├── Dockerfile.frontend
│   │   └── Dockerfile.worker
│   ├── nginx/
│   │   └── nginx.conf
│   ├── scripts/
│   │   ├── init-db.sh
│   │   ├── seed-reference.py   # 基准数据导入脚本
│   │   └── health-check.sh
│   └── monitoring/
│       ├── prometheus.yml
│       └── grafana/
├── docs/                       # Agent-0 主责
│   ├── PentaAge_多Agent协作开发文档_v2.0.md
│   ├── api-examples/           # 每个接口的curl示例
│   ├── adr/                    # 架构决策记录
│   └── runbook/                # 运维手册
├── .github/                    # Agent-4 主责
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
├── shared/                     # 跨Agent共享定义
│   ├── error_codes.py          # 错误码枚举（Python）
│   ├── error_codes.ts          # 错误码枚举（TypeScript）
│   └── constants.py            # 共享常量
├── .env.example
├── .gitignore
├── Makefile                    # 统一命令入口
└── README.md
```

### 4.5 环境与依赖规范

#### 运行时版本（所有Agent必须一致）

| 组件       | 版本      | 锁定方式               |
| :--------- | :-------- | :--------------------- |
| Python     | 3.11.x    | `.python-version`      |
| Node.js    | 20 LTS    | `.nvmrc`               |
| PostgreSQL | 16.x      | `docker-compose.yml`   |
| Redis      | 7.x       | `docker-compose.yml`   |
| RDKit      | 2024.03.x | `requirements.txt` pin |

#### 核心Python依赖

```
fastapi==0.115.*
uvicorn[standard]==0.34.*
sqlalchemy==2.0.*
alembic==1.14.*
celery[redis]==5.4.*
rdkit  # conda安装或rdkit-pypi
pydantic==2.10.*
httpx==0.28.*
pytest==8.*
```

#### 核心前端依赖

```
react@18
zustand@5
antd@5
axios@1
@ant-design/charts@2
vite@6
typescript@5
```

#### 一键启动命令

```bash
# 首次初始化（Agent-4 负责维护）
make init          # 安装依赖 + 创建.env + 初始化DB

# 日常开发
make dev           # 启动全栈（docker-compose up + frontend dev server）
make dev-backend   # 仅后端
make dev-frontend  # 仅前端

# 测试
make test          # 全量测试
make test-unit     # 仅单元测试
make test-integ    # 仅集成测试

# 代码质量
make lint          # ruff + eslint
make format        # ruff format + prettier
make typecheck     # mypy + tsc
```

---

## 5. 数据与算法契约

### 5.1 五单体基准数据管理

1. 基准数据仅允许从`reference_compounds`维护，不在代码中硬编码。
2. 每条基准数据必须有：`name_cn/name_en/cas/smiles/canonical_smiles/fingerprint_version`。
3. 每次更新基准库必须产出`数据变更记录`与`回归测试结果`。

### 5.2 算法版本化

新增字段：

1. `algorithm_version`：如`sim-v1.0.0`。
2. `fingerprint_params`：JSON，记录`radius/bits/useFeatures`。
3. `score_formula_version`：如`score-v1.0.0`。

### 5.3 评分公式（MVP固定）

1. `base_score = max_similarity * 60`
2. `composite_score = top3_avg_similarity * 40`
3. `total_score = min(int(base_score + composite_score), 100)`
4. 方子协同加分：`min(2 * components_count, 10)`

任何公式变动必须升级`score_formula_version`并回归验证。

### 5.4 共享类型定义（跨Agent契约）

以下Pydantic/TypeScript类型是前后端的**绑定契约**，任何修改需Agent-2发起、Agent-3确认。

#### Python (backend/app/schemas/compound.py)

```python
class CompoundAnalyzeRequest(BaseModel):
    input_type: Literal["smiles", "name", "cas", "mol"]
    input_value: str
    options: AnalyzeOptions | None = None

class AnalyzeOptions(BaseModel):
    radius: int = 2
    n_bits: int = 2048
    use_features: bool = False
    top_n: int = 5

class SimilarityResult(BaseModel):
    reference_name: str
    reference_cas: str
    similarity: float  # 0.0 ~ 1.0, 保留4位小数
    rank: int

class CompoundAnalyzeResponse(BaseModel):
    compound_name: str | None
    canonical_smiles: str
    total_score: int  # 0 ~ 100
    base_score: float
    composite_score: float
    top_similarities: list[SimilarityResult]
    algorithm_version: str
    fingerprint_params: dict
    cached: bool
    calc_id: str  # uuid
```

#### TypeScript (frontend/src/types/compound.ts)

```typescript
interface CompoundAnalyzeRequest {
  input_type: "smiles" | "name" | "cas" | "mol";
  input_value: string;
  options?: AnalyzeOptions;
}

interface CompoundAnalyzeResponse {
  compound_name: string | null;
  canonical_smiles: string;
  total_score: number;
  base_score: number;
  composite_score: number;
  top_similarities: SimilarityResult[];
  algorithm_version: string;
  fingerprint_params: Record<string, unknown>;
  cached: boolean;
  calc_id: string;
}
```

> **规则**：后端`schemas/*.py`字段名变更时，必须同步更新`frontend/src/types/*.ts`，并在PR中标注 `[SCHEMA-CHANGE]`。

---

## 6. 数据库设计（增强）

在你现有三张核心表基础上，补充以下表：

### 6.1 `batch_jobs`

用途：批任务主表，追踪任务进度。

关键字段：

1. `id (uuid, pk)`
2. `user_id`
3. `status (pending/running/completed/failed/canceled)`
4. `total_count/success_count/failed_count`
5. `result_file_url`
6. `created_at/started_at/completed_at`

### 6.2 `batch_job_items`

用途：批任务明细，支持重试与断点续算。

关键字段：

1. `id (bigserial, pk)`
2. `job_id (fk)`
3. `row_no`
4. `input_smiles`
5. `status`
6. `error_message`
7. `result_ref`（关联compound_results或冗余JSON）

### 6.3 `formula_components`

用途：方子解析后的标准化成分存档。

关键字段：

1. `id (bigserial, pk)`
2. `calc_id (fk)`
3. `ingredient_name`
4. `resolved_compound_name`
5. `resolved_smiles`
6. `weight`
7. `resolved_source`（tcms/db/manual）

### 6.4 迁移规范

1. 使用Alembic，禁止手工改线上表结构。
2. 每个迁移脚本必须可回滚。
3. 迁移PR必须附带数据兼容说明。

---

## 7. API契约（多Agent并行前必须冻结）

### 7.1 通用响应规范

```json
{
  "success": true,
  "data": {},
  "error": null,
  "request_id": "uuid",
  "processing_time_ms": 123
}
```

错误时：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_SMILES",
    "message": "Invalid smiles string",
    "details": {}
  },
  "request_id": "uuid"
}
```

### 7.2 状态码约定

1. `200` 成功。
2. `202` 异步任务已受理（batch submit）。
3. `400` 参数错误。
4. `404` 资源不存在。
5. `429` 触发限流。
6. `500` 服务器错误。

### 7.3 幂等要求

1. `POST /batch/submit` 支持`Idempotency-Key`请求头。
2. 相同key + 相同文件hash在24小时内返回同一任务ID。

### 7.4 版本治理

1. 仅允许`/api/v1/*`对外。
2. 破坏性变更必须新开`v2`，禁止静默修改字段语义。
3. OpenAPI文档作为前后端联调契约，CI中校验schema破坏变更。

### 7.5 接口详细定义（前后端并行开发基准）

#### `POST /api/v1/compounds/analyze`

| 项目     | 说明                                                    |
| :------- | :------------------------------------------------------ |
| 功能     | 单体化合物抗衰老潜力分析                                |
| 请求体   | `CompoundAnalyzeRequest`（见§5.4）                      |
| 成功响应 | `200` + `ApiResponse<CompoundAnalyzeResponse>`          |
| 错误场景 | `INVALID_SMILES` / `COMPOUND_NOT_FOUND` / `RDKIT_ERROR` |
| 缓存     | 命中时返回 `cached: true`，P95 < 100ms                  |

#### `POST /api/v1/formulas/analyze`

| 项目     | 说明                                                                                     |
| :------- | :--------------------------------------------------------------------------------------- |
| 功能     | 中药方子成分聚合评分                                                                     |
| 请求体   | `{ formula_name: str, ingredients: [{name, weight?}], options?: {} }`                    |
| 成功响应 | `200` + 含 `total_score / component_scores[] / synergy_bonus / unresolved_ingredients[]` |
| 错误场景 | `EMPTY_INGREDIENTS` / `ALL_UNRESOLVED`                                                   |
| 限制     | 成分数上限 50                                                                            |

#### `POST /api/v1/batch/submit`

| 项目     | 说明                                                      |
| :------- | :-------------------------------------------------------- |
| 功能     | 提交批量分析任务                                          |
| 请求体   | `multipart/form-data`，字段 `file`（CSV）+ `options` JSON |
| 成功响应 | `202` + `{ job_id, status: "pending", total_count }`      |
| 幂等     | 支持 `Idempotency-Key` header                             |
| 限制     | 单文件最大 10MB / 10000行                                 |

#### `GET /api/v1/batch/{job_id}/status`

| 项目     | 说明                                                                           |
| :------- | :----------------------------------------------------------------------------- |
| 功能     | 查询批任务进度                                                                 |
| 成功响应 | `200` + `{ job_id, status, progress: {total, success, failed}, eta_seconds? }` |
| 轮询     | 前端建议间隔 3秒                                                               |

#### `GET /api/v1/batch/{job_id}/download`

| 项目     | 说明                                           |
| :------- | :--------------------------------------------- |
| 功能     | 下载批任务结果                                 |
| 成功响应 | `200` + `application/octet-stream`（CSV/JSON） |
| 前置条件 | `status == "completed"`                        |
| 错误场景 | `JOB_NOT_COMPLETED` / `JOB_NOT_FOUND`          |

#### `GET /api/v1/health`

| 项目     | 说明                                                            |
| :------- | :-------------------------------------------------------------- |
| 功能     | 健康检查                                                        |
| 成功响应 | `200` + `{ status: "healthy", components: {db, redis, rdkit} }` |
| 用途     | 负载均衡探针 + 运维监控                                         |

### 7.6 统一错误码目录

所有Agent必须使用以下错误码，禁止自行发明新代码（需新增请找Agent-0审批后添加到此列表）。

| 错误码                 | HTTP状态码 | 含义               | 触发场景                |
| :--------------------- | :--------: | :----------------- | :---------------------- |
| `INVALID_SMILES`       |    400     | SMILES格式无效     | RDKit解析失败           |
| `COMPOUND_NOT_FOUND`   |    404     | 找不到化合物       | 名称/CAS查询无结果      |
| `EMPTY_INGREDIENTS`    |    400     | 方子成分为空       | ingredients数组为空     |
| `ALL_UNRESOLVED`       |    422     | 所有成分均无法解析 | 无一成分可匹配SMILES    |
| `RDKIT_ERROR`          |    500     | RDKit计算异常      | 内部计算失败            |
| `BATCH_FILE_INVALID`   |    400     | 批量文件格式错误   | CSV列缺失或编码异常     |
| `BATCH_FILE_TOO_LARGE` |    413     | 文件超过大小限制   | >10MB 或 >10000行       |
| `JOB_NOT_FOUND`        |    404     | 批任务不存在       | job_id无效              |
| `JOB_NOT_COMPLETED`    |    409     | 任务未完成         | 下载时status非completed |
| `RATE_LIMITED`         |    429     | 触发限流           | 超过频率限制            |
| `IDEMPOTENCY_CONFLICT` |    409     | 幂等键冲突         | 相同key不同内容         |
| `INTERNAL_ERROR`       |    500     | 未知内部错误       | 兜底错误                |

---

## 8. 多Agent协作模型（核心章节）

### 8.1 Agent角色定义

| Agent                  | 职责                                     | 主要交付                       |
| :--------------------- | :--------------------------------------- | :----------------------------- |
| Agent-0 Orchestrator   | 任务拆解、依赖管理、里程碑推进、冲突裁决 | Sprint计划、任务看板、风险清单 |
| Agent-1 Algorithm/Data | RDKit算法、基准数据、验证集维护          | engine模块、算法报告、验证数据 |
| Agent-2 Backend/API    | FastAPI接口、DB模型、任务编排            | API实现、OpenAPI、迁移脚本     |
| Agent-3 Frontend       | 页面实现、可视化、交互体验               | React页面、状态管理、联调结果  |
| Agent-4 Worker/Infra   | Celery、缓存、部署流水线、监控           | worker实现、docker、CI/CD      |
| Agent-5 QA/Release     | 测试设计、回归、发布验收                 | 测试报告、缺陷单、发布结论     |

### 8.2 代码所有权（避免冲突）

| 路径                     | 主责Agent | 评审Agent    |
| :----------------------- | :-------- | :----------- |
| `/backend/app/core/**`   | Agent-1   | Agent-2      |
| `/backend/app/api/**`    | Agent-2   | Agent-3      |
| `/backend/app/models/**` | Agent-2   | Agent-4      |
| `/worker/**`             | Agent-4   | Agent-2      |
| `/frontend/src/**`       | Agent-3   | Agent-2      |
| `/infra/**`              | Agent-4   | Agent-5      |
| `/tests/**`              | Agent-5   | 对应模块主责 |
| `/docs/**`               | Agent-0   | Agent-5      |

### 8.3 任务卡标准（每个任务必须有）

```yaml
task_id: PA-XXX
title: 描述目标，不写实现细节
owner: Agent-X
reviewer: Agent-Y
depends_on: [PA-001, PA-002]
scope:
  in: [明确包含]
  out: [明确不包含]
acceptance:
  - 可验证条件1
  - 可验证条件2
deliverables:
  - code paths
  - test cases
  - docs update
risk:
  - 主要风险与应对
```

### 8.4 分支与合并策略

1. 主干：`main`（始终可部署）。
2. 开发分支：`codex/<agent>/<task-id>-<short-name>`。
3. 合并方式：`squash merge`。
4. 禁止直接推送`main`。

### 8.5 PR门禁（必须全部通过）

1. 单元测试通过。
2. 关键集成测试通过。
3. lint/format通过。
4. OpenAPI或DB变更有文档更新。
5. 关联任务卡与验收项勾选完成。

### 8.6 交接协议（Hand-off）

每次跨Agent交接必须提供：

1. 当前状态：完成/未完成清单。
2. 变更文件列表。
3. 本地验证命令与结果摘要。
4. 已知问题与阻塞项。
5. 下一Agent可直接执行的第一步。

### 8.7 Agent间通信协议

#### 消息格式（所有跨Agent通信必须遵循）

```yaml
msg_id: MSG-20260219-001
from: Agent-2
to: Agent-3
type: dependency_ready | blocked | question | schema_change | review_request
priority: P0 | P1 | P2
subject: "/compounds/analyze 接口已就绪，可开始联调"
body: |
  变更摘要：...
  可用分支：codex/agent2/PA-005-compound-api
  验证命令：curl -X POST http://localhost:8000/api/v1/compounds/analyze ...
  阻塞说明：（如有）
  需要回复：是/否
  截止时间：2026-02-21 EOD
```

#### 依赖声明规则

Agent在开始任务前必须声明输入依赖，格式：

```yaml
task: PA-010
requires:
  - from: Agent-2
    artifact: "POST /api/v1/compounds/analyze 接口可调用"
    status: ready # ready / not_ready / mock_available
  - from: Agent-1
    artifact: "五单体基准数据JSON fixture"
    status: ready
provides:
  - to: Agent-5
    artifact: "单体分析页面可E2E测试"
    eta: W3-周三
```

#### 阻塞升级路径

```
1. Agent间直接沟通（< 2小时解决）
2. 在任务卡标记 Blocked + @阻塞方（< 4小时）
3. 升级到 Agent-0 Orchestrator 裁决（< 8小时）
4. 人工介入（Agent-0无法裁决时）
```

### 8.8 Agent系统提示词模板

每个Agent启动时应携带的上下文（用于AI Agent场景）：

#### Agent通用前缀

```
你是 PentaAge 项目的 Agent-{N} ({角色名})。
- 项目：五单体抗衰老药物预测平台
- 技术栈：FastAPI + React + Celery + PostgreSQL + Redis + RDKit
- 你必须严格遵守《PentaAge_多Agent协作开发文档_v2.0》中的所有契约
- 你只能修改你拥有所有权的路径（见§8.2），其他路径需要对应Agent审批
- 任何接口/Schema变更必须标注 [SCHEMA-CHANGE] 并通知相关Agent
- 提交代码前必须通过 make lint && make test-unit
```

#### Agent-1 (Algorithm/Data) 专用

```
你负责 /backend/app/core/ 下的算法核心模块。
关键约束：
1. Morgan指纹参数：radius=2, nBits=2048（除非score_formula_version升级）
2. 评分公式见§5.3，任何改动需升级版本号
3. 所有算法函数必须是纯函数（无副作用），输入SMILES → 输出评分
4. 基准数据从DB读取（reference_compounds表），不可硬编码
5. 新增算法必须附带验证集测试，命中率 >= 85%
```

#### Agent-2 (Backend/API) 专用

```
你负责 /backend/app/api/ 和 /backend/app/models/ 和 /backend/app/schemas/。
关键约束：
1. API响应格式必须符合§7.1通用响应规范
2. 错误码只能使用§7.6目录中已有的，需新增找Agent-0审批
3. 所有DB变更必须通过Alembic迁移，迁移脚本必须可回滚
4. Schema变更需同步通知Agent-3更新前端types
5. 新接口必须有OpenAPI注解 + curl示例
```

#### Agent-3 (Frontend) 专用

```
你负责 /frontend/src/ 下所有前端代码。
关键约束：
1. API类型定义必须与后端schemas对齐（见§5.4）
2. 使用 Zustand 管理状态，API调用层在 /src/api/
3. 批任务轮询间隔3秒，使用useEffect + cleanup
4. 所有页面需要loading/error/empty三种状态处理
5. 接到 [SCHEMA-CHANGE] 通知后24小时内完成类型同步
```

#### Agent-4 (Worker/Infra) 专用

```
你负责 /worker/ 和 /infra/ 下所有基础设施代码。
关键约束：
1. Celery任务必须支持幂等重试（max_retries=3, countdown=exponential）
2. Docker镜像基于python:3.11-slim，多阶段构建
3. 所有配置项通过环境变量注入（见.env.example）
4. CI流水线在PR合入前必须通过lint + unit test + integration test
5. Makefile是所有开发命令的唯一入口
```

### 8.9 架构决策记录（ADR）

任何影响多Agent的技术决策需记录在 `/docs/adr/` 下。

#### 8.9.1 触发条件（满足任一条必须写ADR）

1. 接口或Schema发生破坏性变更。
2. 跨2个及以上Agent所有权路径的架构调整。
3. 数据模型、缓存策略、队列语义、鉴权策略变化。
4. 对性能SLO、稳定性SLO、安全边界有显著影响的技术决策。

#### 8.9.2 文件命名与状态规则

1. 路径：`/docs/adr/ADR-{NNN}-{slug}.md`（如 `ADR-012-schema-versioning.md`）。
2. 编号递增且不可复用；废弃ADR不删除，仅标记状态。
3. 状态流转：`proposed -> accepted -> deprecated/superseded`。
4. `superseded` 必须指向替代ADR编号。

#### 8.9.3 最小模板（必填字段）

```markdown
# ADR-{NNN}: {决策标题}

## 元信息

- Date: YYYY-MM-DD
- Owner: Agent-X
- Reviewer: Agent-Y
- Related Task/PR: PA-XXX / #PR
- Supersedes: ADR-00X（可选）

## 状态

proposed / accepted / deprecated / superseded

## 决策驱动（Decision Drivers）

- Driver-1: ...
- Driver-2: ...

## 背景

为什么需要做这个决策？

## 决策

我们决定...

## 影响的Agent

Agent-X, Agent-Y

## 影响范围

- In scope: ...
- Out of scope: ...

## 后果

### 正面

- ...

### 负面

- ...

## 替代方案（已否决）

- 方案A：...（否决原因：...）

## 验证与回滚

- 验证：对应测试/指标/验收命令
- 回滚：触发条件 + 回滚步骤 + 数据兼容说明
```

#### 8.9.4 执行约束

1. ADR状态为 `accepted` 前，不得将其作为跨Agent强约束。
2. 涉及 `[SCHEMA-CHANGE]` 的PR必须在描述中引用ADR编号。
3. Agent-0负责ADR编号分配与冲突裁决，Agent-5负责可验证性抽查。

### 8.10 ULW执行协议（新增，默认启用）

适用场景：所有跨2个及以上模块的任务，或涉及接口/Schema/数据模型变更的任务。

#### 阶段A：意图校验（Intent Gate）

1. 先判定任务类型：Trivial / Explicit / Exploratory / Open-ended / Ambiguous。
2. 若存在多种解释且工作量差异 >= 2倍，必须先做仓内探索再定默认方案。
3. 默认遵循“最小可行解释”，禁止在未请求时扩展需求。

#### 阶段B：双轨上下文收集（必须并行）

1. Direct Track：`grep/read/lsp` 直查本仓代码与文档。
2. Background Track：
   - `explore`：查内部模式、模块边界、既有约定。
   - `librarian`：查外部框架文档、OSS可复用实践。
3. 满足任一条件即可停止继续搜索：
   - 已能安全实现；
   - 新一轮搜索无新增有效信息；
   - 已获得直接可执行方案。

#### 阶段C：执行与验证

1. 变更必须“外科手术式”：只改请求范围内文件与逻辑。
2. 每个逻辑单元完成后运行 `lsp_diagnostics`（修改文件级）。
3. 任务收尾至少提供以下证据：
   - 修改文件清单；
   - 关键验证命令与结果（通过/失败+原因）；
   - 未解决风险与后续动作。

### 8.11 标准交接契约（Hand-off Contract v2）

除§8.6内容外，跨Agent交接新增强制字段：

```yaml
handoff_version: 2
source_context:
  branch: codex/agent2/PA-005-compound-api
  commit: <sha>
  changed_paths:
    - backend/app/api/v1/compounds.py
definition_of_done:
  - POST /api/v1/compounds/analyze 返回字段与§5.4一致
resource_budget:
  max_tool_calls: 30
  max_retry_rounds: 2
verification_gates:
  - schema_contract_check: pass
  - unit_test_target: pass
open_risks:
  - P1: formula接口仍使用mock数据
```

### 8.12 变更门禁（Gatekeeper）

任意交接或PR进入评审前，必须通过以下不变量检查：

1. **契约不变量**：后端 `schemas/*.py` 与前端 `types/*.ts` 字段语义一致。
2. **安全不变量**：未新增密钥泄露、未绕过鉴权、错误返回不暴露堆栈。
3. **可观测性不变量**：新增关键流程包含 `request_id` 与错误码。
4. **回归不变量**：受影响路径具备至少1条对应测试或可复现验证步骤。

### 8.13 冲突处理与升级（Three-Tier）

1. Tier-1（直接回退）：Reviewer给出失败证据，Owner仅允许1轮定向修复。
2. Tier-2（编排裁决）：1轮后仍失败，提交Agent-0给出统一方案与边界。
3. Tier-3（人工介入）：Agent-0无法裁决时冻结任务，等待人工决策。

约束：禁止在冲突阶段并行引入无关重构；禁止“先合并后修复”。

### 8.14 决策留痕（Decision Ledger）

跨模块任务必须在任务卡或PR描述中追加“决策留痕”三项：

1. Why：为什么这样改（业务/技术约束）。
2. Evidence：依据了哪些代码证据或文档证据。
3. Trade-off：放弃了什么方案及原因。

目的：保证其他Agent在无口头上下文时可继续维护。

### 8.15 联合开发最后一步执行规则（强制）

每次任务完成后的**最后一步**必须执行以下三项，缺一不可：

1. **中文汇报**：任务进展、交接说明、结果汇总一律使用中文编写。
2. **Git版本管理**：所有代码与文档改动必须通过 Git 纳入版本管理并形成提交记录。
3. **更新内容记录**：每次提交或交接必须明确记录本次更新内容（做了什么、为什么改）。

---

## 9. 开发流程（Sprint节奏）

### 9.1 每周固定节奏

1. 周一：Sprint计划会（拆任务、确认依赖、冻结接口变更）。
2. 周二-周四：并行开发 + 每日同步（15分钟）。
3. 周五：集成回归 + 演示 + 风险复盘。

### 9.2 状态流转

`Todo -> In Progress -> In Review -> In Test -> Done`

补充状态：

1. `Blocked`：依赖未满足，需注明阻塞人和预计解除时间。
2. `Rework`：评审驳回后返工。

### 9.3 Definition of Ready（DoR）

任务开始前必须满足：

1. 输入输出明确。
2. 上下游依赖清楚。
3. 验收标准可测试。
4. 风险可识别。

### 9.4 Definition of Done（DoD）

任务完成必须满足：

1. 代码、测试、文档三者齐全。
2. 无P0/P1未解决缺陷。
3. 监控与日志字段完整。
4. 可以被其他Agent无上下文继续维护。

---

## 10. 测试与质量门槛

### 10.1 测试分层

1. 单元测试：算法函数、工具函数、schema校验。
2. 集成测试：API + DB + Redis + worker联动。
3. 端到端测试：核心用户路径（单体、方子、批量）。
4. 性能测试：P95时延、吞吐与资源占用。
5. 准确性测试：化学验证集命中率。

### 10.2 覆盖率目标

1. `backend` 语句覆盖率 >= 80%。
2. `core algorithm` 分支覆盖率 >= 85%。
3. `frontend` 关键页面用例覆盖率 >= 70%。

### 10.3 质量红线

1. 任何导致错误评分的缺陷视为P0。
2. 任何导致结果不可追溯（无版本/无参数）的缺陷视为P1。
3. 无法稳定复现的算法结果禁止发布。

---

## 11. 环境、部署与发布

### 11.1 环境分层

1. `dev`：开发联调环境，可重置数据。
2. `staging`：预发布环境，接近生产配置。
3. `prod`：生产环境，只允许发布流水线变更。

### 11.2 CI流水线

`lint -> unit test -> integration test -> build image -> security scan -> deploy staging`

生产发布前增加：

1. 冒烟测试。
2. 回滚点创建（镜像tag + DB备份点）。

### 11.3 发布策略

1. 默认每周一次小版本发布。
2. 紧急修复使用hotfix分支，24小时内补齐回归测试。
3. 发布说明必须包含：变更、影响范围、回滚方案。

---

## 12. 安全与合规

1. 所有密钥使用环境变量注入，禁止入库、入git。
2. API统一限流（默认60 req/min，可按用户分层）。
3. 输入内容严格校验，防止注入与恶意文件上传。
4. 审计日志至少保留90天（任务创建、结果导出、权限操作）。
5. 对外返回不暴露内部堆栈信息。

---

## 13. 监控与运维

### 13.1 指标（最低要求）

1. API：QPS、P95、错误率、429率。
2. Worker：队列长度、任务耗时、失败重试次数。
3. DB：慢查询、连接数、锁等待。
4. 业务：分析成功率、无效输入比例、Top失败原因。

### 13.2 告警规则（初版）

1. API错误率 > 2% 持续5分钟告警。
2. 批任务失败率 > 5% 持续10分钟告警。
3. 数据库连接使用率 > 85% 持续5分钟告警。

### 13.3 日志规范

1. 统一JSON日志格式。
2. 强制字段：`timestamp/request_id/user_id/module/action/status/duration_ms/error_code`。
3. 敏感字段脱敏（邮箱、token、密钥）。

---

## 14. 8周执行排期（多Agent并行版）

| 周次 | 目标                             | Agent主责 | 可验收交付                          |
| :--: | :------------------------------- | :-------- | :---------------------------------- |
|  W1  | 基线搭建、数据入库、接口草案冻结 | 0/1/2/4   | 目录结构、五单体入库、OpenAPI草案   |
|  W2  | 单体分析核心链路打通             | 1/2       | `/compounds/analyze`可用 + 单测     |
|  W3  | 前端单体页联调 + 可视化初版      | 3/2       | 单体页可完整闭环                    |
|  W4  | 方子解析实现与成分聚合评分       | 1/2/3     | `/formulas/analyze`可用             |
|  W5  | 批量任务与导出                   | 4/2/3     | `/batch/submit/status/download`可用 |
|  W6  | 性能优化、缓存、索引、重试机制   | 1/2/4     | 达到P95和吞吐目标                   |
|  W7  | 全链路测试与缺陷收敛             | 5/全员    | 测试报告、P0/P1清零                 |
|  W8  | 发布准备、演示材料、运维手册     | 0/4/5     | staging签收、发布说明、演示版       |

---

## 15. 风险清单与应对

| 风险              | 等级 | 触发信号       | 应对策略                         |
| :---------------- | :--: | :------------- | :------------------------------- |
| 外部成分API不稳定 |  高  | 超时/限流激增  | 本地缓存 + 降级到手工输入        |
| RDKit性能不达标   |  高  | P95超标        | 指纹缓存 + 任务并行 + 预计算     |
| 数据质量不足      |  中  | 命中率下降     | 验证集扩充 + 专家复核流程        |
| 多Agent冲突修改   |  中  | 频繁rebase冲突 | 路径所有权 + 小PR + 接口先行     |
| 批任务失败率高    |  中  | 失败>5%        | 细粒度重试 + 死信队列 + 错误分类 |

---

## 16. 交付物清单（MVP）

1. 可运行的docker compose环境。
2. 完整OpenAPI文档与示例请求。
3. 前端三大页面可演示。
4. 批量任务导出结果可下载。
5. 自动化测试与质量报告。
6. 运维监控面板与告警规则。
7. 用户使用手册与开发者手册。

---

## 17. 附录模板

### 17.1 PR描述模板

```markdown
## 变更目的

## 变更范围

- [ ] backend
- [ ] frontend
- [ ] worker
- [ ] infra
- [ ] docs

## 验收标准对应

- [ ] AC-1
- [ ] AC-2

## 测试结果

- 单元测试：
- 集成测试：
- 手工验证：

## 风险与回滚
```

### 17.2 Hand-off模板

```markdown
Task: PA-XXX
From: Agent-X
To: Agent-Y

已完成:

- ...

未完成:

- ...

变更文件:

- ...

验证命令:

- ...

阻塞项:

- ...

下一步建议:

- ...
```

---

## 18. W1-W2 首批任务卡（可直接分配）

### PA-001: 项目骨架初始化

```yaml
task_id: PA-001
title: 创建monorepo目录结构与基础配置文件
owner: Agent-4
reviewer: Agent-0
depends_on: []
acceptance:
  - 目录结构符合§4.4，所有__init__.py就位
  - Makefile包含 init/dev/test/lint 四个目标
  - .env.example 包含所有必要环境变量
  - docker-compose.dev.yml 可一键启动 postgres + redis
deliverables:
  - 完整目录结构
  - Makefile / docker-compose.dev.yml / .env.example
  - README.md（包含快速启动指南）
```

### PA-002: 五单体基准数据入库

```yaml
task_id: PA-002
title: 五单体基准数据JSON准备与DB种子脚本
owner: Agent-1
reviewer: Agent-2
depends_on: [PA-001]
acceptance:
  - reference_compounds表含5条完整记录
  - 每条有name_cn/name_en/cas/smiles/canonical_smiles/fingerprint_version
  - seed脚本幂等（重复运行不报错不重复插入）
deliverables:
  - tests/fixtures/reference_compounds.json
  - infra/scripts/seed-reference.py
```

### PA-003: 数据库模型与迁移初始化

```yaml
task_id: PA-003
title: SQLAlchemy模型定义 + Alembic初始迁移
owner: Agent-2
reviewer: Agent-1
depends_on: [PA-001]
acceptance:
  - 6张表模型完整（reference_compounds/compound_results/formula_results/batch_jobs/batch_job_items/formula_components）
  - alembic upgrade head 可无错执行
  - alembic downgrade -1 可回滚
deliverables:
  - backend/app/models/*.py
  - alembic/versions/001_initial.py
```

### PA-004: OpenAPI Schema冻结

```yaml
task_id: PA-004
title: 冻结v1 API的Pydantic schemas与OpenAPI文档
owner: Agent-2
reviewer: Agent-3
depends_on: [PA-003]
acceptance:
  - schemas/compound.py 与 §5.4 完全一致
  - schemas/formula.py 与 schemas/batch.py 定义完整
  - Agent-3确认TypeScript类型可对齐
deliverables:
  - backend/app/schemas/*.py
  - frontend/src/types/*.ts（Agent-3同步产出）
```

### PA-005: 单体分析API实现

```yaml
task_id: PA-005
title: 实现 POST /api/v1/compounds/analyze 完整链路
owner: Agent-2
reviewer: Agent-1
depends_on: [PA-003, PA-004, PA-006]
acceptance:
  - 输入SMILES返回正确评分（与§5.3公式对齐）
  - 缓存命中时返回 cached:true
  - 无效SMILES返回 INVALID_SMILES 错误码
  - P95 < 3秒
deliverables:
  - backend/app/api/v1/compounds.py
  - backend/app/services/compound_service.py
```

### PA-006: 算法核心模块

```yaml
task_id: PA-006
title: 实现指纹计算、相似度比对、评分函数
owner: Agent-1
reviewer: Agent-2
depends_on: [PA-002]
acceptance:
  - fingerprint.py 生成Morgan指纹（radius=2, nBits=2048）
  - similarity.py 计算Tanimoto系数
  - scoring.py 实现§5.3评分公式
  - 验证集Top-1命中率 >= 85%
  - 所有函数为纯函数，100%单测覆盖
deliverables:
  - backend/app/core/*.py
  - tests/unit/test_*.py
```

### PA-007: CI流水线搭建

```yaml
task_id: PA-007
title: GitHub Actions CI配置（lint + test + build）
owner: Agent-4
reviewer: Agent-5
depends_on: [PA-001]
acceptance:
  - PR触发lint（ruff + eslint）
  - PR触发单元测试
  - main合入触发集成测试 + Docker镜像构建
deliverables:
  - .github/workflows/ci.yml
```

### PA-008 ~ PA-015 概要

| 任务ID | 标题                                 | Owner   | 依赖          | 目标周 |
| :----- | :----------------------------------- | :------ | :------------ | :----: |
| PA-008 | 前端项目初始化（Vite+React+AntD）    | Agent-3 | PA-001        |   W1   |
| PA-009 | 前端通用组件（Layout/Loading/Error） | Agent-3 | PA-008        |   W2   |
| PA-010 | 单体分析页面开发                     | Agent-3 | PA-004,PA-009 | W2-W3  |
| PA-011 | 方子解析算法实现                     | Agent-1 | PA-006        | W3-W4  |
| PA-012 | 方子分析API实现                      | Agent-2 | PA-011        |   W4   |
| PA-013 | 批量任务Worker实现                   | Agent-4 | PA-005        | W4-W5  |
| PA-014 | 回归测试框架搭建                     | Agent-5 | PA-005        |   W2   |
| PA-015 | 健康检查与监控基础                   | Agent-4 | PA-001        |   W2   |

---

## 19. 术语表

| 术语     | 英文                                         | 含义                   | 使用场景              |
| :------- | :------------------------------------------- | :--------------------- | :-------------------- |
| 五单体   | Five Monomers                                | 5种抗衰老基准化合物    | 相似度比对基准        |
| 方子     | Formula                                      | 中药药方（含多种成分） | 方子分析功能          |
| 指纹     | Fingerprint                                  | Morgan分子指纹向量     | 化学结构编码          |
| Tanimoto | Tanimoto Coefficient                         | 分子相似度度量[0,1]    | 相似度计算            |
| SMILES   | Simplified Molecular-Input Line-Entry System | 分子线性表示法         | 化合物输入            |
| CAS      | CAS Registry Number                          | 化学物质唯一编号       | 化合物标识            |
| 基准库   | Reference Library                            | 五单体数据集           | reference_compounds表 |
| 评分     | Score                                        | 抗衰老潜力评分[0-100]  | 核心输出              |
| 协同指数 | Synergy Index                                | 方子成分协同加分       | 方子评分              |
| Hand-off | Hand-off                                     | 跨Agent任务交接        | 协作流程              |
| DoR      | Definition of Ready                          | 任务开始条件           | Sprint流程            |
| DoD      | Definition of Done                           | 任务完成条件           | Sprint流程            |
| ADR      | Architecture Decision Record                 | 架构决策记录           | 技术决策              |

---

## 20. 下一步落地建议（从今天开始）

1. **Agent-0**：创建任务看板，将PA-001~PA-007分配给对应Agent，标记W1 Sprint。
2. **Agent-4**：立即执行PA-001（项目骨架），所有Agent的工作都依赖此任务。
3. **Agent-1**：并行准备五单体基准数据（PA-002），与Agent-4同步进行。
4. **Agent-2**：PA-001完成后立即启动PA-003（DB模型）和PA-004（Schema冻结）。
5. **Agent-3**：PA-001完成后启动PA-008（前端初始化），并review PA-004的Schema。
6. **Agent-5**：从W2开始同步编写PA-014（回归测试框架），避免最后一周补测试。

> **关键路径**：`PA-001 → PA-003 → PA-004 → PA-005/PA-006 → PA-010（前端联调）`
> 任何延期必须在24小时内通知Agent-0并更新排期。

---

## 21. 当前执行状态（2026-02-19）

1. `PA-001` 已完成：目录骨架、`Makefile`、`.env.example`、`docker-compose.dev.yml`、`README` 已就位。
2. `PA-002` 已完成：`backend/tests/fixtures/reference_compounds.json` 已提供5条基准数据；`infra/scripts/seed-reference.py` 支持按 `cas` 幂等导入。
3. `PA-003` 已完成：6张核心表模型与 `backend/alembic/versions/001_initial.py` 已落地。
4. `PA-004` 已完成：`backend/app/schemas/*.py` 与 `frontend/src/types/*.ts` 已按契约同步。
5. `PA-005` 进行中：`/compounds/analyze` 已具备请求校验、相似度计算、评分与统一响应；仍需补齐真实FastAPI路由与数据库持久化。

### 21.1 下一步优先级

1. 完成 `PA-005` 剩余项：将当前函数式入口替换为真实FastAPI路由并接入持久化。
2. 并行推进 `PA-006`：将轻量指纹实现切换为RDKit实现，并补验证集准确率测试。
3. 启动 `PA-014`：建立回归测试框架，覆盖 `INVALID_SMILES` 与缓存命中路径。

### 21.2 交接入口

最新交接文件：`docs/runbook/HANDOFF_2026-02-19_PA005.md`
