# BugLens 项目总体规划与周期管理手册（01-PLAN）

> **文档角色**：项目的"总调度台"——规划周期、资源、前后端分工、八周路线、GitHub 日常管理。
> **配套滚动日志**：[PROGRESS-001.md](PROGRESS-001.md)（每日工作记忆与进展记录，追加式）。
> **不变约束**：本手册所有条款服从 [02-MANUAL](../manual/02-MANUAL.md) §2 约束条件总表；冲突时以 02-MANUAL 为准。

| 项 | 值 |
|---|---|
| 版本 | v1.0（2026-10-28 建立） |
| 当前阶段 | 策划完成（[BLUEPRINT](../docs/PROJECT_BLUEPRINT.md) v1.1 + [DECISION](../docs/DEEP_DIVE_DECISION.md)），待 W1 启动 |
| 执行人 | 个人开发者（学生，业余时间每天 2–3 小时） |
| 硬件 | 现有 Windows PC（16GB 内存起步），CPU-only |

---

## 1. 这套文档体系怎么用（小白新生指南）

### 1.1 文档地图：四份核心文档 + 两类滚动日志 + 定稿区

```
buglens/
├── README.md                 ← 总入口（文档地图 + 当前状态）
├── plan/      【计划区】     01-PLAN.md（本手册，改版需记录）
│                             PROGRESS-NNN.md（进展日志·每日卡片·滚动追加）
├── manual/    【手册区】     02-MANUAL.md（操作实施手册·约束·一致性）
│                             03-EXPERIMENTS.md（实验指令手册·agent 指令集）
│                             04-AGENT-PLAYBOOK.md（AI Agent 工程方法论）
├── reports/   【报告区】     REPORT-NNN.md（实验报告·滚动追加，>1500 行开新卷）
├── docs/      【定稿区】     PROJECT_BLUEPRINT.md（策划书 v1.1）
│                             DEEP_DIVE_DECISION.md（深查决策）
├── .gitignore
└── src/ 等    【代码区】     W1 按 02-MANUAL §7 建立（在此之前不写任何代码）
```

**分区纪律**（为什么这么分）：计划会改、日志会涨、报告会滚、定稿少动、代码独立——五类东西生命周期完全不同，混在一个文件夹必然互相污染。**只有日志类文件允许追加写入，其余改动必须走版本号**。

### 1.2 每天开工与收工的固定动作（SOP，10 分钟）

**开工三步**：
1. 打开 `plan/PROGRESS-001.md`，读最后一张每日卡片（昨天做到哪、今天入口在哪）；
2. 打开本手册 §5 八周表，确认本周行与今天该做的实验号；
3. 打开 `manual/03-EXPERIMENTS.md` 对应实验卡片，复制指令块给编码智能体开干。

**收工三步**：
1. 在 PROGRESS 追加今天的每日卡片（模板见该文件）；
2. 若完成了一个实验，在 `reports/REPORT-001.md` 追加实验记录（模板见该文件）；
3. `git add -A && git commit -m "exp: EXP-0x ..."`（W1 git init 之后）。

### 1.3 内容索引：想找什么看哪里（避免重复维护）

| 你想找 | 去哪里 |
|---|---|
| 行业分析 / 前景 / 未来方向 / 趋势榜打法 | docs/PROJECT_BLUEPRINT.md §1、§7 |
| 空白点 / 痛点 / 证伪记录 / 竞争分析 | docs/DEEP_DIVE_DECISION.md §2–§4 |
| 技术点 / 价值点 / 架构 / 技术设计 | docs/PROJECT_BLUEPRINT.md §4 |
| 市场价值 / 商业模式 | docs/PROJECT_BLUEPRINT.md §6 |
| 学术路线 / 未来研究 / 投稿日历 | docs/PROJECT_BLUEPRINT.md §5、DECISION §5 |
| 八周路线 / 每次做什么 / 资源 / GitHub 管理 | 本手册 §3、§5、§7、§8 |
| 约束条件 / 包结构 / 命名 / 数据集 / 成功指标 | manual/02-MANUAL.md |
| 实验指令（可直接粘贴给 AI） | manual/03-EXPERIMENTS.md |
| 怎么和 Agent 协作开发 / 术语 | manual/04-AGENT-PLAYBOOK.md |
| 在线来源与复核 | 两份定稿文档附录（已逐条附 URL） |

**给小白的生产建议**：不要试图一次读懂全部文档。按 1.2 的 SOP 走，用到哪节读哪节；写任何新文档前先查 1.3 索引，已有内容一律引用不复制——**重复内容是文档腐烂的开始**。

---

## 2. 项目一页纸摘要

- **做什么**：给一张 UI 缺陷截图（可选报错文本/录屏），多智能体自动完成：复现（Playwright 沙箱）→ 视觉定位（VLM）→ 行级代码定位（跨模态检索）→ 最小补丁 → 修复循环内可执行视觉验证（像素 diff + 布局断言 + 测试）→ 带证据链的 PR。
- **为谁**：前端/全栈开发者、开源维护者（GitHub 最大开发者群体）。
- **凭什么赢**：开源界无有牵引力的占用者（6+ 玩具仓库均 0–6★）；商业付费已验证（Devin $20/月起）；学术窄口径空白（行级视觉定位 GT、修复循环内 oracle）。
- **硬约束**：CPU-only、LangGraph 编排、免费 API 优先（GLM-4V-Flash）、只提 PR 不自动合并、首版仅 React 标准脚手架。
- **目标**：八周内 CLI+Action 可用（M0+M1）；2027-01 前基准挂 arXiv；主投 ASE 2027 与 NeurIPS 2027 D&B。

---

## 3. 资源与平台清单

### 3.1 硬件与环境

| 项 | 要求 | 说明 |
|---|---|---|
| PC | Windows（本机），16GB 内存起步，32GB 更稳 | Docker + Playwright + Chromium 并发渲染吃内存 |
| 网络 | 稳定访问 GitHub / PyPI / 模型 API | 需配置 pip/uv 镜像与 API 代理时记录进 PROGRESS |
| Docker Desktop | WSL2 后端 | 沙箱复现用户代码（安全约束 S05） |
| Python | **3.11+**（本地 = conda env `lumin`；CI = uv + Python 3.11） | 单一 `pyproject.toml` 真源；构建后端 setuptools（中文路径适配，SKILL-03） |

### 3.2 账号与费用表（启动总成本 < ¥100）

| 资源 | 用途 | 费用 | 接入时间 |
|---|---|---|---|
| 智谱开放平台 API key | GLM-4V-Flash（免费）+ GLM-4.5-Flash（免费）主力 | ¥0（注意免费档并发限制） | W1 |
| DeepSeek API | 备用视觉/文本（$0.15–0.30/百万输入） | 月均 <¥50（按需充值） | W6 降级演练前 |
| GitHub 账号 | 仓库/Action/PyPI 发布/Issue 机器人 | ¥0 | 已有 |
| PyPI 账号 | `pip/uvx buglens` 一行安装 | ¥0 | W6（发 0.1.0） |
| Docker Hub | Action 沙箱镜像 | 免费档 | W7 |
| 域名（可选） | 项目主页跳转 | ~¥60/年 | M3 前 |
| 魔搭 / Trae 社区 | MCP 形态分发、中文冷启动 | ¥0 | M3 发布日 |
| 掘金 / V2EX / CSDN 账号 | 发布日集中导流 | ¥0 | M3 前 |

### 3.3 平台矩阵：每个平台什么时候用、干什么

| 平台 | 用途 | 日常动作 |
|---|---|---|
| GitHub | 代码、CI、issue/PR 治理、release、社交（star） | §8 |
| PyPI | CLI 分发 | 每次 tag 发布 |
| 智谱 / DeepSeek | 模型推理 | 监控免费额度与并发 |
| 魔搭 MCP 广场 / Trae 市场 | MCP server 上架（蹭生态分发） | M3 一次性 + 版本更新 |
| arXiv | 基准占坑（2027-01 前） | M2 |
| 掘金 / V2EX / X / HN | 发布日导流 + 每月实战内容 | M3 起每周一篇 |

---

## 4. 目录宪法（分区隔离制度）

### 4.1 分区职责与写入规则

| 分区 | 职责 | 允许的操作 | 禁止的操作 |
|---|---|---|---|
| `plan/` | 计划与执行日志 | PLAN 改版走版本号；PROGRESS 只追加 | 放实验数据、放代码 |
| `manual/` | 操作手册（人怎么干、AI 怎么被指挥） | 改版走版本号 | 记录一次性事实 |
| `reports/` | 实验报告（滚动追加） | 只追加；>1500 行开新卷 REPORT-002 | 一实验一文件 |
| `docs/` | 定稿对外文档（策划/决策/未来论文素材） | 改版走版本号 + 修订记录 | 被日志类内容稀释 |
| `src/` 等 | 代码（W1 建立） | 走 git 分支与 PR | 放文档、放数据集大文件 |

### 4.2 判例（遇到拿不准的往哪放）

- 今天踩了个坑（中文路径/依赖版本）→ **PROGRESS 每日卡片**；
- 坑的解法具有通用性（如"Playwright 禁动画的完整配置"）→ 蒸馏成 **03-EXPERIMENTS 附录 A 技能库 SKILL-xx**；
- 一次定位准确率的评测数据与结论 → **REPORT-001 实验记录**；
- 结论改变了架构决策 → 在 **docs/BLUEPRINT** 对应章节改版并记录修订。

---

## 5. 八周执行路线（W1–W8）

**投入假设**：每周 15–20 小时业余时间；每周一个主目标；每项产出都有可验收形态。**本表是承诺，不是愿望**——每周收工时在 PROGRESS 卡片里对照打勾。

| 周 | 主目标 | 关键任务 | 产出物 | 验收标准 | 实验 |
|---|---|---|---|---|---|
| W1 | 环境与地基 | git init、pyproject+uv、CI 骨架（ruff/mypy/pytest 空跑）、.devcontainer、注册智谱 key、选定 golden-1 案例仓库、手动复现并采集（截图/DOM/console） | 可安装的空壳包 + golden-1 采集样本（temp/，不入库） | `uv run buglens --help` 可用；CI 全绿；VLM 对 golden-1 截图输出结构化描述 | EXP-01、02 |
| W2 | 复现官+视觉分析官 | Reproducer 节点（确定性 profile：固定视口/时区/禁动画/种子）；VisualAnalyst（VLM→JSON Schema 校验的 bbox+缺陷描述） | `graph/` 两节点 + 单测 | golden-1 自动复现 10 次成功 ≥8；VLM bbox 与人工标注 IoU ≥0.5 | EXP-03、04 |
| W3 | 定位官 | DOM 路径→组件名→tree-sitter AST 切片→BM25+bge-m3 混合检索→top-5 行级候选 | `repo/` 检索管线 + 单测 | golden-1/2 定位 top-5 命中真实修复行 | EXP-05 |
| W4 | 修复+验证+回环（M0 验收周） | Fixer 最小补丁；Verifier（像素 diff 阈值+布局断言+既有测试）；LangGraph 条件边回环 ≤3 | MVP 完整图 | **golden 3/3 端到端正确补丁；单案例成本 <¥1** | EXP-06、07 |
| W5 | 证据链+Reporter | Evidence Store（内容寻址、只增）；PR 渲染（Markdown+before/after 图+证据视图） | `evidence/` + Reporter 节点 | 生成一份真实 PR 样式的报告文件，每个断言可溯源 | EXP-08 |
| W6 | CLI 打磨+降级+发布 0.1.0 | uvx 一行装；GLM→DeepSeek→moondream 三级降级；VLM 响应缓存；发布 PyPI | v0.1.0 + 发布流程文档 | 断网/限额演练：自动降级不中断；`uvx buglens` 在干净环境可用 | EXP-09 |
| W7 | GitHub Action（M1 验收周） | action.yml+Docker 沙箱；issue 评论 `/buglens` 触发；输出 PR | Action + 测试仓库演练 | 在测试仓库 issue 贴截图端到端出 PR（≥2 个真实开源 repo 演练） | EXP-10 |
| W8 | 缓冲+复盘+双语启动 | 补 W1–7 欠账；M1 阶段复盘写入 REPORT；README 英文化；M2 基准挖掘查询语句设计 | M1 复盘报告 + 英文 README 草稿 | 八周表逐项核对；复盘含"是否正收益"结论 | EXP-11 |

### 5.1 双周检查点与止损规则（不达标怎么办，先说清楚）

| 检查点 | 判据 | 不达标的止损动作 |
|---|---|---|
| W2 末 | golden-1 自动复现 ≥5/10 | 复现范围收窄为"带 devcontainer 的仓库"；重选 golden 案例；仍 <5/10 则触发 §5.2 重大调整评审 |
| W4 末 | M0 验收（3/3、<¥1） | 追加 1 周缓冲（占用 W8）；砍范围：golden 降为 2 个、Verifier 简化为像素 diff 单通道 |
| W6 末 | 成本 <¥1/案例且降级可用 | 主力切全免费档（GLM-4V-Flash only）；检索降级为纯 BM25 |
| W8 末 | M1 验收 | 复盘决定：M2 按期启动 / 延后一周 / 暂停并重新评估（学业优先） |

### 5.2 重大调整评审

任何想改变"截图→复现→定位→修复→验证→PR"主链路或新增大依赖的冲动，必须先写一页"调整提案"放进 PROGRESS，48 小时后（冷静期）再决定。**防止小白最常见死法：第 3 周开始加"顺便做个 Web UI/顺便支持 Vue"导致主线崩盘**。

### 5.3 八周之后（M2–M4 展望）

八周完成 M0+M1。随后：M2 基准（+6 周，2027-01 前挂 arXiv）→ M3 v1.0 发布日（+4 周，周二发布、集中导流）→ M4 云 Pro+论文投稿（+8 周）。详见 [BLUEPRINT §8 路线图](../docs/PROJECT_BLUEPRINT.md)。

---

## 6. 前端·后端·全栈管理

本项目"端"的定义与普通 Web 应用不同，先对齐再动手：

| 层 | 内容 | 优先级 | 时间 |
|---|---|---|---|
| **内核引擎（后端核心）** | LangGraph 图、九智能体、Evidence Store、检索、oracle——纯 Python，与界面无关 | P0（唯一真相源） | W1–W5 |
| **CLI（第一交付面）** | Typer，包装内核 | P0 | W1 骨架、W6 打磨 |
| **GitHub Action（第二交付面）** | YAML + Docker，包装内核 | P1 | W7 |
| **MCP server（第三交付面）** | 官方 MCP Python SDK 适配，蹭生态分发 | P1 | M3 |
| **Web UI（美观漂亮的门面）** | 只读消费 Evidence Store 的证据链视图 | P2（延后） | v0.3 之后 |

**全栈纪律**：①先内核后皮肤——任何 UI/美化工作不得早于 W8（约束 S09）；②UI 永远只是证据链的只读视图，不写业务逻辑；③三种交付面共享同一内核，任何"只在 Action 里加的逻辑"都是架构违规（依赖方向见 02-MANUAL §7.2）。

---

## 7. 会话工作法：每次做什么、有什么成果、下一步

- **一次工作会话 = 一个实验或一个欠账**。开头在 03-EXPERIMENTS 找到对应卡片，收工必须留下三样东西之一：代码+测试、REPORT 里的实验记录、或 PROGRESS 里的问题记录。
- **成果定义**（什么算"做完"）：验收命令通过 + 记录落盘 + git commit。三者缺一不算完成。
- **下一步从哪来**：每日卡片的"明日入口"字段永远写清下一个动作（精确到实验号或文件名），消灭"今天不知道干啥"的状态。

---

## 8. GitHub 项目日常管理

### 8.1 开仓第一天（W1）基建清单

- [ ] `git init` + 首 commit（README、LICENSE、pyproject、.gitignore、现有文档区）；
- [ ] 分支保护：main 禁止直推（设置 require PR，单人项目也开——养成习惯）；
- [ ] CI：`.github/workflows/ci.yml`（ruff → mypy → pytest，全绿才可合并）；
- [ ] Issue 模板：bug 报告含"请贴截图"引导（吃自己的狗粮）；
- [ ] PR 模板：关联实验号 + 约束核查清单（引 02-MANUAL §2 的约束 ID）；
- [ ] Labels：`area:core / vision / repro / delivery`、`type:exp / bug / doc`、`good first issue`；
- [ ] Milestones：M0、M1、M2、M3、M4。

### 8.2 分支与提交规范

- 分支：`feat/xxx`、`fix/xxx`、`exp/EXP-03-reproducer`（实验分支以实验号命名）；
- Commit：Conventional Commits——`feat:` / `fix:` / `exp:` / `docs:` / `chore:`；一行说清，禁 "update"；
- 每次 commit 前 `make check`（ruff+mypy+pytest）本地过一遍——CI 红是事故，不是常态。

### 8.3 Issue / PR 治理

- 实验也开 issue（标题 = 实验号+名称），做完关 issue，形成第二条时间线；
- issue 首响 <48h（哪怕只回"已排期"）；good first issue 从 W8 起每月至少 2 个（Vue/Flutter 适配器）。

### 8.4 日常运营节奏（star 是运营出来的）

| 频率 | 动作 |
|---|---|
| 每天 | 看 issue/通知；PROGRESS 记录 |
| 每周五 | "对表日"：八周表逐项核对 + 02-MANUAL 约束自查（§2）+ 目录清洁（02-MANUAL §12） |
| 每两周 | checkpoint（§5.1）+ 阶段复盘写入 REPORT |
| 每月 | 竞品/论文月扫（EXP-12 例行）+ 一篇"用 BugLens 修真实 bug"内容 |
| M3 起 | social 文件：CONTRIBUTING.md、FUNDING.yml、CODEOWNERS、讨论区 |

---

## 9. 进展日志制度（PROGRESS-NNN 滚动规则）

- 文件：`plan/PROGRESS-001.md` 起，**只追加不修改**；
- 单卷超过 1500 行 → 开 `PROGRESS-002.md`，旧卷末尾写"接 PROGRESS-002"，新卷开头写"承接 PROGRESS-001"；
- 每条记录 = 一张每日卡片（模板在文件内）；当天多次工作可写多张卡片，同日编号 a/b；
- 严禁删除历史卡片——错了就在新卡片里更正并引用旧卡片编号。

---

## 10. 当前状态与下一步（Next Actions）

- [x] 2026-10-28 两轮调研与证伪深查（定稿区两份文档）
- [x] 2026-10-28 管理体系建立（本手册 + 02/03/04 + PROGRESS/REPORT 卷一）
- [x] 2026-10-29 W1/EXP-01 完成：命名核查（保留 buglens，PyPI 空闲）、`git init -b main`、仓库基建、conda lumin 安装验收全绿（详见 REPORT EXP-01 / PROGRESS #003）
- [ ] W1 剩余：注册智谱 key（GLM-4V-Flash 免费档）→ 选定 golden-1 案例仓库并截 3 张 bug 图 → EXP-02 VLM 摸底
- [ ] 待用户操作：GitHub 建远程仓库并推送（CI 首跑）；两台挂钟：2027-01 前基准 arXiv 占坑（M2）；每月最后一个周五 EXP-12 月扫
