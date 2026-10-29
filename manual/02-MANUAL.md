# BugLens 操作实施手册（02-MANUAL）

> **文档角色**：项目的"宪法 + 施工规范"——约束条件、成功指标、数据集、模型框架、包结构一致性、命名规范、证据闭环、日志/可复现/记忆/清理/复盘制度。
> **优先级**：本手册 §2 约束条件总表是全项目最高执行准则，与任何文档冲突时以本表为准；修改约束需走 §2.5 约束变更流程。

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-28 | 建立 |
| v1.1 | 2026-10-29 | T06 修订（EXP-01 环境适配：本地=conda `lumin`/Python 3.11+；构建后端 setuptools）；SKILL-03 沉淀 |

---

## 1. 手册定位与"防脱轨"总览

项目脱轨的四种经典死法与本章对策：

| 死法 | 对策条款 |
|---|---|
| 范围膨胀（顺便做个 UI/支持所有框架） | §2.2 范围约束 + 01-PLAN §5.2 调整评审 |
| 吹牛皮被抓（宽口径学术表述） | §2.3 表述红线（源自 DECISION §5.3） |
| 结构腐烂（文件乱放、包交叉依赖） | §7 包结构 + §8 命名 + §12 清洁制度 |
| 无法复现（"上次明明能跑"） | §10 日志与可复现规范 |

---

## 2. 约束条件总表（硬边界，每条有 ID，可被 PR/实验引用）

### 2.1 技术约束（T）

| ID | 约束 | 理由 |
|---|---|---|
| T01 | **CPU-only**：任何组件不得要求 GPU/训练 | 用户硬件与成本约束 |
| T02 | 编排框架 = **LangGraph ≥1.2**（MIT） | 用户指定；有状态图与回环控制 |
| T03 | 视觉推理主力 **GLM-4V-Flash（免费）**，降级链 DeepSeek-flash → 本地 moondream(ONNX) | 成本近零 + 可用性兜底 |
| T04 | 本地检索 = BM25 + **bge-m3**（CPU）；不引入 GPU 嵌入 | T01 |
| T05 | 复现环境 = **Docker/devcontainer + Playwright**，确定性 profile（固定视口/时区/禁动画/固定种子） | 复现保真度是产品核心承诺 |
| T06 | Python **3.11+**（本地运行环境 = conda env `lumin`，Python 3.11.14，用户指定）；依赖唯一真源 `pyproject.toml`；构建后端 **setuptools**（中文路径下唯一安全的 PEP 660 editable 方式，见 SKILL-03）；CI 侧用 uv；src 布局 | 工程一致性 + 本机环境适配（v1.1 修订） |
| T07 | 质量门禁：ruff + mypy(strict) + pytest，内核覆盖率 ≥85%，CI 全绿才可合并 | 可靠性 |
| T08 | 许可证 Apache-2.0；依赖必须兼容（不引入 GPL 传染组件） | 商业化路径 |
| T09 | 所有模型调用走 Provider 抽象层，禁止业务代码直连 SDK | 可替换与降级 |
| T10 | 用户代码一律沙箱执行，默认禁网，白名单显式开 | 安全 |

### 2.2 范围约束（S）——首版只做这些

| ID | 约束 |
|---|---|
| S01 | 输入=截图（PNG/JPG）+ 可选文本报错 + 可选 issue URL；**不做**录屏（v0.3 后） |
| S02 | 框架适配首版仅 **React（Vite/CRA/Next 标准脚手架）**；Vue/Flutter 是适配器插件（M3+） |
| S03 | 输出=PR 草案 + 证据链报告；**绝不自动合并**（红线中的红线） |
| S04 | 回环上限 3 次；超限输出"定位+建议"降级报告 |
| S05 | 非标准仓库（无标准脚手架/devcontainer）复现失败时优雅降级，不硬试 |
| S06 | 不做通用 agent 框架、不做 RAG 问答、不做 deep research（红海，BLUEPRINT §1.2） |
| S07 | 不训练/微调任何模型（学术路线是评测与基准，不是训练） |
| S08 | Web UI 不早于 v0.3；UI 只读消费 Evidence Store |
| S09 | 每实验单案例成本上限 ¥1；超标先降级模型再砍功能 |
| S10 | 基准 VisBugBench-Pro 首版 300 案例（可扩 500），**2027-01 前 arXiv 占坑** |

### 2.3 表述红线（N）——论文/README/宣传中禁止出现

| ID | 禁止 | 替代（窄口径） |
|---|---|---|
| N01 | "首个/唯一的视觉修复验证 oracle" | "修复循环内的可执行视觉 oracle"（引用 SWE-bench M 69 像素实例、SWE-PolyVision） |
| N02 | "复现保真度从未被量化" | "修复管线内 LLM 近似复现的保真度未被度量"（引用 ReBug RSR 49.96%） |
| N03 | "此前全部绑定闭源模型" | "免费 API 开源模型路线的可达性与差距未被系统评估"（引用 SVRepair） |
| N04 | "开源界没有同类" | "开源界无有牵引力的占用者（玩具级尝试均 0–6★）" |

### 2.4 工程约束（E）

| ID | 约束 |
|---|---|
| E01 | 目录五分区隔离（plan/manual/reports/docs/code），写入规则见 01-PLAN §4 |
| E02 | 中间产物只进 `temp/`（已 gitignore），入库的只有结论与必要压缩截图 |
| E03 | 命名遵守 §8 总表；任何新文件先查表 |
| E04 | 日志/报告遵守 §10/§14 滚动规则，禁止一实验一文件 |
| E05 | 每次 commit 前 `make check` 通过；CI 红=事故 |

### 2.5 约束变更流程

改约束 = 改宪法：在 PROGRESS 写"约束变更提案"（改哪条/为什么/影响什么）→ 冷静期 48h → 在本表改版并记录版本号 → 受影响文档同步。**任何 PR 不得与现行约束冲突；发现冲突即打回。**

---

## 3. 分阶段实施指南

| 阶段 | 周期 | 输入 | 关键动作 | 输出/出口判据 |
|---|---|---|---|---|
| Phase 0 环境 | W1 | 本手册+01-PLAN | 仓库基建、CI、golden-1 采集 | `uv run buglens --help` + CI 绿 |
| Phase 1 内核 | W2–W4 | golden 案例、API key | 四核心节点 + 回环 | **M0：golden 3/3、<¥1/案例** |
| Phase 2 交付 | W5–W8 | Phase 1 内核 | 证据链、CLI、降级、Action | **M1：测试仓库 issue→PR 端到端** |
| Phase 3 基准 | M2（+6 周） | 挖掘管线 | 数据采集、行级标注、指标实现、评测 | 300 案例 + arXiv 占坑（2027-01 前） |
| Phase 4 发布 | M3–M4 | v1.0 候选 | 适配器、MCP、双语、发布日、云 Pro | 趋势榜冲击 + 论文投稿 |

每阶段结束写阶段复盘（§13），复盘通过才进下一阶段。

---

## 4. 成功指标体系（分层 KPI 与测量方法）

| 层 | 指标 | 目标（时点） | 测量方法 |
|---|---|---|---|
| 实验 | 单实验验收 | 每张实验卡片的验收标准 | 卡片内验收命令 |
| 产品-复现 | 自动复现成功率 | ≥80%（golden，W2） | 连跑 10 次计数 |
| 产品-定位 | 行级定位 top-5 命中率 | ≥80%（golden，W3） | 与人工标注行号比对 |
| 产品-修复 | golden 端到端通过率 | 3/3（W4）→ ≥60%（基准口径，3 个月） | oracle + 人工确认 |
| 产品-成本 | 单案例成本 | <¥1（W4 起） | token 计数×单价，REPORT 记录 |
| 产品-速度 | 单案例闭环时长 | ≤15 分钟（W6） | 耗时埋点 |
| 工程 | 内核覆盖率 / CI | ≥85% / 永远绿 | pytest-cov |
| 传播 | GitHub stars / 贡献者 | 5k/20 人（3 个月，M3 后起算） | GitHub Insights |
| 学术 | 基准 arXiv / 论文在投 | 2027-01 / 2027-05 | arXiv 号 / 提交回执 |
| 商业 | 云 Pro 安装仓库 | ≥50（6 个月） | 后台计数 |

**指标纪律**：所有数字必须可复算——测量脚本入库 `benchmarks/`，报告里的每个数都能一条命令重跑出来。**真实可靠不造假：宁可报告难看的真实数字，不写好看的编造数字。**

---

## 5. 数据集与数据管线

| 数据集 | 用途 | 来源与构造 | 规模 |
|---|---|---|---|
| golden-3 | 开发期回归 + 演示（README GIF 素材） | 自建最小 React 仓库 + 已知视觉 bug（遮挡/溢出/错位），每例含：bug 截图、复现步骤、期望修复 | 3 例（W1 定稿） |
| SWE-bench Multimodal | 离线评测参考集 | 直接复用公开数据（[2410.03859](https://arxiv.org/abs/2410.03859)，617 实例） | 按需抽样 |
| VisBugBench-Pro | 学术基准（M2） | 挖掘管线：GitHub API 查前端仓库 → issue 含截图 + 关联 PR 已合并 + diff ≤5 文件 → 半自动标注（LLM 预标注行级 + 人工抽查 20%） | 300 例（含 Vue/H5/Flutter Web 扩展集） |
| badcase 库 | Agent 调优（持续） | 每次失败案例按 §13 分类入库 `tests/badcases/`（脱敏后） | 持续增长 |

**数据纪律**：数据集不入 git 大文件（用 release 附件/HF dataset）；标注规范单独成文放 `benchmarks/`；许可证合规（挖掘公开仓库需注明来源与 license）。

## 6. 模型与框架清单（含降级链）

| 角色 | 首选 | 备选 | 兜底 |
|---|---|---|---|
| 视觉分析/验证 VLM | GLM-4V-Flash（免费） | qwen3-vl-plus / DeepSeek-flash | moondream-2B ONNX（本地离线） |
| 文本推理（规划/补丁） | GLM-4.5-Flash（免费） | DeepSeek-chat | 本地小模型不承诺 |
| 嵌入 | bge-m3（本地 CPU） | API 嵌入 | BM25-only |
| 编排 | LangGraph ≥1.2 | — | — |
| 复现 | Playwright + devcontainer | — | — |
| 代码切片 | tree-sitter | — | — |
| CLI | Typer；Action=GitHub Actions；MCP=官方 MCP Python SDK | — | — |

选型详细理由见 [BLUEPRINT §4.5](../docs/PROJECT_BLUEPRINT.md)。

---

## 7. 包结构与一致性管理

### 7.1 代码区目录（W1 按此建立，定稿后改动需走约束变更）

```
src/buglens/
├── cli.py               # Typer 入口（唯一 console_script）
├── graph/               # LangGraph 装配：state.py（状态/Evidence 模型）、builder.py（节点+条件边）
├── agents/              # 九智能体，每智能体一个子包：run.py（纯函数）+ prompts.py
│   ├── intake/ reproducer/ visual_analyst/ locator/
│   └── planner/ fixer/ verifier/ critic/ reporter/
├── vision/              # 截图采集、像素 diff、SSIM、布局断言（oracle 核心）
├── repro/               # 沙箱 profile、Playwright 确定性配置
├── repo/                # 索引：AST 切片、BM25、bge-m3 混合检索
├── evidence/            # Evidence Store（内容寻址、只增）
├── wiki/                # Repair Wiki 读写（v0.3+）
├── adapters/            # 框架适配器：react/（vue/、flutter_web/ 为插件位）
├── models/              # Provider 抽象 + 三级降级 + 缓存
└── delivery/            # cli/ github_action/ mcp_server 三形态适配（只做包装）
tests/                   # unit + e2e（tests/golden/ = golden-3）
benchmarks/              # 指标测量脚本 + VisBugBench-Pro 管线
examples/                # 演示仓库
temp/                    # 中间产物（gitignore，唯一合法的"脏"目录）
```

### 7.2 依赖方向规则（防止包腐烂）

```
delivery → graph → agents → {vision, repro, repo, evidence, wiki, adapters} → models
```

- 只允许上层 import 下层，**禁止同层横向 import、禁止反向**；
- agents 之间不互相 import（协作只通过 state）；
- 违例 = CI 检查失败（§7.3）。

### 7.3 一致性自动检查（CI 内）

1. import 方向检查（简单脚本：解析 AST 生成依赖图，断言无环、无横向）；
2. ruff + mypy(strict)；
3. 覆盖率门禁 ≥85%（内核包）；
4. 术语一致性：关键类名与 §8.4 术语表对齐（code review 人工把关 + 定期 grep 审计）。

---

## 8. 命名规范总表

| 对象 | 规则 | 示例 |
|---|---|---|
| Python 模块/函数/变量 | snake_case | `visual_analyst/run.py`、`locate_candidates()` |
| 类 | PascalCase | `EvidenceStore` |
| 常量 | UPPER_SNAKE | `MAX_RETRIES = 3` |
| 文档区 MD | UPPER_SNAKE + 编号 | `01-PLAN.md`、`REPORT-001.md` |
| 实验编号 | `EXP-NN`（两位，从 01） | EXP-03 |
| 技能库条目 | `SKILL-NN` | SKILL-01 |
| 每日卡片 | `#NNN 日期 [a/b]` | `#003 2026-11-02` |
| 分支 | `feat/`、`fix/`、`exp/EXP-NN-短名` | `exp/EXP-03-reproducer` |
| Commit | Conventional Commits | `exp: EXP-03 复现官确定性 profile` |
| 证据工件 | `ev-{sha8}-{kind}.{ext}` | `ev-3f2a1b9c-screenshot.png` |
| Release tag | 语义化版本 | `v0.1.0` |
| 环境变量 | `BUGLENS_` 前缀 | `BUGLENS_GLM_API_KEY` |

### 8.4 术语表（文档与代码统一用词，禁止同义混用）

| 中文 | 代码/英文 | 禁止的混用 |
|---|---|---|
| 复现官 | reproducer | reproduce agent |
| 视觉分析官 | visual_analyst | vision agent |
| 定位官 | locator | finder |
| 修复工程师 | fixer | repairer |
| 验证官 | verifier | checker |
| 审查官 | critic | reviewer（留给代码评审用） |
| 证据链 | evidence chain | proof chain |
| 证据工件 | evidence artifact | evidence file |

---

## 9. 证据一致性闭环（Evidence IR 实施规范）

这是产品核心卖点，也是内部质量管理机制，规格如下：

1. **数据结构**：`Evidence(kind, artifact_ref, claim, produced_by, created_at)`；kind ∈ {screenshot, dom, code_span, diff, render_diff, test_run, model_output}；
2. **只增不改**：Evidence Store 内容寻址（sha8），任何智能体的任何断言（claim）必须挂至少一条证据，否则下游节点拒绝消费（graph 内断言检查）；
3. **闭环要求**：最终 PR 中的每一句话必须能点开一条证据——截图异常↔DOM 节点↔代码行↔diff↔渲染前后对比，五环相扣缺一不可交付；
4. **内部复用**：实验报告（REPORT）与阶段复盘同样引用证据工件编号，保证"报告里的结论"与"原始证据"一一对应。

---

## 10. 日志·可复现·版本记录规范

1. **实现过程完整日志**：开发动作记 PROGRESS（每日卡片）；实验记 REPORT（EXP 记录）；两者都是只追加；
2. **run 可复现三要素**：每次实验记录必须含 ① 环境指纹（`uv.lock` 提交哈希 + Python 版本）② 模型指纹（provider+model+版本+温度等参数）③ 输入指纹（golden 案例版本 / 数据快照哈希）；
3. **随机性控制**：所有采样/生成固定 seed=42，除非实验目的就是测随机性；
4. **版本记录**：文档表头版本号+变更表；代码走 git tag；数据集走快照哈希。

## 11. 记忆体系（长短期记忆 + 每日工作记忆 + 自我进化）

| 记忆类型 | 载体 | 生命周期 | 写入规则 |
|---|---|---|---|
| 短期（当日） | PROGRESS 每日卡片 | 当天 | 收工必写"明日入口" |
| 中期（周/阶段） | REPORT 实验结论 + 01-PLAN checkpoint | 周期 | 每实验/每 checkpoint |
| 长期（项目级） | docs/ 定稿文档 | 项目全程 | 每月"蒸馏"：把 REPORT 中已验证结论的一句话更新进定稿文档并记版本 |
| 技能（可复用知识） | 03-EXPERIMENTS 附录 A 技能库 SKILL-NN | 永久 | 踩坑解法具通用性时蒸馏入库 |
| 产品自身记忆 | Repair Wiki（v0.3+，`wiki/` 包） | 用户级 | 症状→根因→补丁模式条目 |
| AI 会话记忆 | ZCode 持久记忆 | 跨会话 | 项目关键决策同步（已启用） |

**蒸馏纪律**：同一知识只允许一个"权威家"（single source of truth）——结论住 REPORT，方法论住 manual，事实住 docs，操作住技能库。搬家时旧位置留指针。

## 12. 目录整洁制度（清理与防污染）

- **禁止入库**：`temp/`、`.venv`、`__pycache__`、`*.pyc`、`.env`、`node_modules`、`dist/`、`artifacts/`、截图原图（>500KB 的进 release 附件）；`.gitignore` 已覆盖；
- **每周五清洁例程**（5 分钟）：`git status` 应干净；temp/ 清空；reports/ 无游离文件；发现无家可归的文件立即按 01-PLAN §4.2 判例归位或删除；
- **月度审计**：目录树与 §7.1 逐行比对，新增顶层条目必须先修文档再建目录。

## 13. 实验总结与复盘制度（含"不正收益"处理）

**每次实验后 15 分钟，在 REPORT 追加记录**，必填字段：
1. 目标（预期指标）；2. 配置（三要素，§10）；3. 结果（真实数字）；4. **结论：是否达到成功目标 / 是否正收益**；5. 问题与归因；6. 下一步。

**归因四步法**（结果不及预期时按序排查）：
① 查 trace（哪一步先错：定位？补丁？oracle 误判？）→ ② 查输入（截图质量/案例是否超范围 S02）→ ③ 查提示词版本（diff 出改动）→ ④ 查模型原始输出（保存了 model_output 证据吗）。

**四类典型问题分类入库**（badcase 库，与 04-PLAYBOOK §5 对齐）：A 选错工具/走错节点、B 参数填错、C 幻觉（无证据断言）、D 兜底缺失。

**两周一次阶段复盘**（REPORT 内独立小节）：上期 KPI vs 本期 → 是否正收益 → 负收益时先归因再决策（修/降级/砍范围），并检查是否触碰 §2 约束。

## 14. 报告文档滚动管理规则（1500 行规则）

1. 实验记录一律追加进 `reports/REPORT-001.md`，**禁止一实验一文件**；
2. 单卷总行数 >1500 → 开新卷 `REPORT-002.md`：旧卷末尾写 `→ 承接 REPORT-002`，新卷开头写承接行与卷内索引；
3. 每卷开头维护"卷内索引表"（EXP 号 → 小节号 → 结论一行），保证可检索；
4. PROGRESS 日志同样适用本规则（`PROGRESS-002.md`…）；
5. 命名固定 `REPORT-NNN.md` / `PROGRESS-NNN.md`（三位，够用 999 卷×1500 行）。
