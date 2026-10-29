# BugLens 实验指令手册（03-EXPERIMENTS）

> **文档角色**：Vibe Coding / AI 编码智能体（ZCode、Codex、Claude Code、Trae 等）的**实验指令集**——每个实验一张卡片：目的、前置、可直接粘贴的指令块、人工步骤、验收标准、记录要求。
> **纪律**：一次只跑一个实验；AI 产出的代码必须人工 review（方法见 [04-AGENT-PLAYBOOK](04-AGENT-PLAYBOOK.md) §6）并过 `make check`；验收通过 + REPORT 落盘 + commit 三件齐才算完成（02-MANUAL §E05）。
> **记录**：所有实验结果追加写入 [reports/REPORT-001.md](../reports/REPORT-001.md)，禁止一实验一文件（02-MANUAL §14）。

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-28 | 建立（EXP-01–11 + 例行 + 远期池） |

---

## 1. 实验总表（与 01-PLAN 八周路线对齐）

| 实验 | 名称 | 周次 | 类型 | 一句话目标 |
|---|---|---|---|---|
| EXP-01 | 仓库基建与环境基线 | W1 | 工程 | git init 到 CI 全绿 |
| EXP-02 | VLM 摸底 | W1 | 探索 | GLM-4V-Flash 对 bug 截图输出结构化描述 |
| EXP-03 | 复现官确定性 profile | W2 | 工程 | 同一仓库连跑 10 次截图逐像素一致 |
| EXP-04 | 视觉分析官 | W2 | 工程 | VLM→bbox+缺陷描述，JSON Schema 校验 |
| EXP-05 | 定位官 | W3 | 工程 | 截图异常区域→top-5 行级代码候选 |
| EXP-06 | 修复工程师 | W4 | 工程 | 最小补丁生成 |
| EXP-07 | 验证 oracle 与回环 | W4 | 工程 | 像素/布局/测试三通道判定 + ≤3 次回环 |
| EXP-08 | 证据链与 Reporter | W5 | 工程 | 五环证据相扣的 PR 报告 |
| EXP-09 | CLI·降级·发布 | W6 | 工程 | uvx 一行装 + 模型降级演练 + v0.1.0 |
| EXP-10 | GitHub Action | W7 | 工程 | issue 贴截图→PR 端到端 |
| EXP-11 | M1 复盘与双语启动 | W8 | 管理 | 阶段复盘 + 英文 README |
| EXP-12 | 竞品/论文月扫 | 每月 | 例行 | 撞车监视（DECISION §6 风险） |
| EXP-13+ | 远期池 | M2+ | 见 §5 | 基准挖掘/模型横评/成本压测 |

---

## 2. 指令块通用约定（先读这段再复制指令）

- 指令块用 ```text 代码块包裹，`【】`内是**你每次要手工替换的参数**；
- 每次会话开头先粘贴"上下文锚"（让 AI 知道项目约束，防止跑偏）：

```text
【上下文锚——每次会话开头粘贴】
项目：BugLens（E:\26-10-28-zcode-开源项目\buglens），截图→复现→定位→修复→像素验证→证据链 PR 的多智能体系统。
必读约束：manual/02-MANUAL.md §2（T01-T10/S01-S10/E01-E05）。
当前实验：manual/03-EXPERIMENTS.md §3 的【EXP-0x】。
目录纪律：代码只进 src/ 与 tests/；中间产物进 temp/（不入库）；文档改动只限 plan/ 与 reports/ 追加。
禁止：引入 GPU 依赖；自动合并 PR；Web UI（S08）；范围外框架。
完成定义：验收命令通过 + make check 通过，然后停下等我 review，不要自行提交。
```

---

## 3. 核心实验卡片（W1–W8）

### EXP-01 仓库基建与环境基线（W1）

**目的**：从零到"可安装空壳包 + CI 全绿"。**前置**：核查 `buglens` 命名（GitHub/PyPI）。

```text
【EXP-01 指令】
在 E:\26-10-28-zcode-开源项目\buglens 下初始化 Python 项目骨架：
1. git init；确认 .gitignore 已覆盖 temp/.venv/__pycache__/.env/artifacts/node_modules/dist。
2. pyproject.toml（uv 管理，src 布局，包名 buglens，Python>=3.12）：依赖 typer、langgraph、playwright、pydantic>=2；dev 依赖 ruff、mypy、pytest、pytest-cov。
3. src/buglens/__init__.py + cli.py：Typer 骨架，仅一个命令 `buglens --help` 显示项目名与版本。
4. Makefile：check = ruff check + mypy src + pytest。
5. .github/workflows/ci.yml：push/PR 触发，ubuntu-latest，跑 make check（先 uv sync）。
6. mypy strict 配置；ruff 行宽 100。
约束提醒：遵守 02-MANUAL §7.1 目录与 §8 命名。不要创建本卡片未列出的文件。
验收后停下，列出你创建的每个文件与用途，等我 review。
```

**人工步骤**：GitHub 建远程仓库并推送；设置 main 分支保护。
**验收**：`uv run buglens --help` 正常；`make check` 本地绿；GitHub Actions 绿。
**记录**：REPORT 追加 EXP-01（环境指纹：Python/uv 版本、lock 哈希）。

### EXP-02 VLM 摸底（W1）

**目的**：验证免费视觉 API 真实可用性与输出质量底线。**前置**：智谱 key；golden-1 仓库截图 3 张（人工用 Playwright 截）。

```text
【EXP-02 指令】
写 scripts 不入库（放 temp/），直接用智谱 GLM-4V-Flash API：
1. 读 temp/ 下 3 张 golden-1 截图，调用 VLM，提示词要求输出 JSON：
   {"anomaly_region":[x,y,w,h],"symptom":"一句话中文描述","severity":"low|mid|high","confidence":0-1}
2. 用 pydantic 校验每条输出；解析失败的原始响应原样保存为 temp/exp02_raw/。
3. 打印每图的解析成功率与输出，人工对照截图粗评 bbox 是否大致框住异常。
不要写正式包代码，这是摸底实验。
```

**验收**：3/3 解析成功；bbox 人工粗评"大致正确"≥2/3。
**记录**：REPORT 记录解析成功率、延迟、失败样例；若 <2/3，改写提示词重跑一轮并把两版提示词与结果都记下（这是第一次"迭代提示词"的完整记录范式）。

### EXP-03 复现官确定性 profile（W2）

**目的**：同一仓库同一 bug 连续复现 10 次，采集产物逐字节/逐像素一致——确定性是全部下游的地基。

```text
【EXP-03 指令】
实现 src/buglens/repro/：
1. ReproProfile（pydantic）：视口 1280x800、时区 Asia/Shanghai、locale zh-CN、禁用动画/过渡（注入 CSS）、禁缓存、固定 seed、等待网络空闲策略。
2. reproducer.py：给定仓库路径与启动命令 → 在 Docker/devcontainer 内拉起 dev server → Playwright 按 profile 打开目标页 → 采集 screenshot.png / dom.html / console.log / network.har。
3. 产物写 temp/exp03/<run-id>/，run-id 含时间戳。
4. tests/test_repro_determinism.py：对 examples/golden-1 连跑 10 次其中的 3 次（CI 时限），断言 dom.html 哈希一致、截图 SSIM ≥0.999。
遵守：models/ 抽象未涉及本实验不引入；沙箱默认禁网除 localhost（T10）。
```

**人工步骤**：确定 golden-1 启动命令；Docker 环境跑通。
**验收**：10 次连跑 dom 哈希一致；SSIM ≥0.999；单次复现 ≤3 分钟。
**记录**：REPORT 记录成功率、耗时、不一致时的差异定位（哪次哪个产物变了）。

### EXP-04 视觉分析官（W2）

**目的**：把 EXP-02 的摸底提示词固化为 `agents/visual_analyst/`，输出过 Schema 校验、附证据。

```text
【EXP-04 指令】
实现 src/buglens/agents/visual_analyst/（run.py + prompts.py）：
1. run(state) 为纯函数：读 state 中复现截图 → 调 models/ 的 VLM Provider → 返回 state 增量 {visual_report, evidence:[截图证据+模型原始输出]}。
2. prompts.py：EXP-02 验证过的最优提示词版本（版本号注释），要求 bbox 基于图像坐标系、输出 JSON。
3. models/provider.py：抽象 BaseVLM（complete_vision(image, prompt)->str），实现 GLMProvider（GLM-4V-Flash），带重试 2 次与 429 退避；响应缓存到 temp/cache/（key=图像哈希+提示词哈希）。
4. 单测：mock Provider 验证 state 增量与证据挂接；Schema 校验失败的输出必须抛异常而非静默。
```

**验收**：golden-1/2 的 bbox 与人工标注 IoU ≥0.5；缓存命中时零 API 调用。
**记录**：REPORT 记录 IoU 数值表（案例×3 次运行）、缓存命中率。

### EXP-05 定位官（W3）

**目的**：从视觉异常区域走到行级代码候选——跨模态检索管线。

```text
【EXP-05 指令】
实现 src/buglens/repo/ 与 agents/locator/：
1. repo/indexer.py：tree-sitter 解析 TS/TSX → 函数/组件级切片（文件路径+行号范围+标识符）；BM25 索引（rank-bm25）；bge-m3 嵌入（CPU，SentenceTransformers 或 ONNX）→ 余弦索引。
2. locator/run.py：输入 state.visual_report 的 DOM 选择器 → 提取组件名/类名/文案 → 三路召回（AST 标识符匹配、BM25、向量）→ RRF 融合 → top-5 候选（文件:行范围 + 置信度 + 每候选一条证据）。
3. 下载模型属网络操作，做成显式 `buglens index init` 子命令，进度可见。
4. 单测：对 golden-1/2 断言 gold 行号在 top-5。
```

**验收**：golden-1/2 定位 top-5 命中；索引构建 ≤5 分钟/仓库。
**记录**：REPORT 记录命中情况、三路召回各自贡献（消融雏形，M2 论文复用）。

### EXP-06 修复工程师（W4 前半）

```text
【EXP-06 指令】
实现 agents/planner/ 与 agents/fixer/：
1. planner/run.py：读定位候选+视觉报告+console 日志 → 输出假设列表（根因假设、修改方案、预期视觉变化），写入 state。
2. fixer/run.py：按首选假设生成最小补丁：对候选文件生成 unified diff；约束为"只改候选文件、每处改动需引用假设 id"；应用补丁到 worktree 副本（原仓库不动）。
3. prompts 强调最小改动（few-shot 一条正例）；diff 产物入证据。
4. 单测：mock 模型返回预置 diff，验证应用与回滚。
```

**验收**：golden-1 补丁语法正确（可 apply）；改动 ≤3 处。
**记录**：REPORT 记录每案例 diff 行数、是否命中 gold 语义。

### EXP-07 验证 oracle 与回环（W4 后半，M0 验收）

```text
【EXP-07 指令】
实现 vision/verify.py 与 agents/verifier/、graph/builder.py 回环：
1. oracle 三通道：① 像素 diff（对修复后重渲染截图 vs 期望区域）阈值判定 ② 布局断言（异常元素的 bbox 与遮挡关系重算）③ 既有测试运行（npm test，超时 10 分钟）。
2. verifier/run.py：输出 Verdict{pass/fail, per-channel 结果, 证据}；fail 时把失败证据写回 state 供 planner 再规划。
3. graph/builder.py：LangGraph 装配 intake→reproducer→visual_analyst→locator→planner→fixer→verifier，条件边：fail 且 retries<3 → planner；pass → critic（本实验先直通 END）→reporter（占位）。MAX_RETRIES=3。
4. tests/golden/：三个 golden 案例端到端测试（API 用 mock 与真实双模式，CI 用 mock）。
```

**验收（=M0）**：golden 3/3 端到端正确补丁；单案例成本 <¥1（真实模式，本地手动跑）；回环行为符合预期（故意注入坏补丁验证回环）。
**记录**：REPORT 记录 3 案例全指标（成本/时长/回环次数），M0 验收打勾，引用证据工件号。

### EXP-08 证据链与 Reporter（W5）

```text
【EXP-08 指令】
实现 evidence/store.py 与 agents/reporter/、agents/critic/：
1. store.py：内容寻址（sha8）保存工件；只增 API：put(kind, bytes, claim, produced_by)。
2. critic/run.py：非对称审查——只读证据与 diff，不读 planner/fixer 的自述；输出通过/否决+理由；否决走回环。
3. reporter/run.py：渲染 PR 描述 Markdown：概述/根因/补丁/before-after 图（内嵌压缩图）/证据链表（每个断言→ev-xxx 可点开）/复现步骤/"需人工审阅，未自动合并"声明（S03）。
4. 断言-证据完整性检查：任何断言无证据则渲染失败（把证据链做成硬约束）。
```

**验收**：golden-1 生成完整 PR 报告文件；人为删一条证据 → 渲染必须报错。
**记录**：REPORT 附报告样例链接与检查结果。

### EXP-09 CLI·降级·发布 v0.1.0（W6）

```text
【EXP-09 指令】
1. cli.py 完整化：buglens fix --shot x.png --repo . [--issue URL]；buglens index init；buglens report <run-id>。
2. models/ 降级链：GLM-4V-Flash 失败(连续3次/额度429) → DeepSeek-flash → 本地 moondream；降级事件写日志与证据；BUGLENS_PROVIDER 可强制指定。
3. 配置：环境变量 BUGLENS_* 读取（.env 支持，示例 .env.example）。
4. 发布准备：README 快速开始节、CHANGELOG.md、tag v0.1.0、PyPI 发布流程（GitHub release 触发 workflow）。
```

**验收**：干净虚拟环境 `uvx buglens --help` 可用；人为限流 mock 演练降级链不中断；PyPI 0.1.0 可装。
**记录**：REPORT 记录降级演练时间线与发布清单打勾。

### EXP-10 GitHub Action 端到端（W7，M1 验收）

```text
【EXP-10 指令】
实现 .github/action.yml 与 delivery/github_action/：
1. 触发：issue 评论 /buglens + 附图；读取截图与仓库上下文。
2. 运行：devcontainer/标准脚手架检测 → 沙箱内核跑闭环（复用同一内核，S 约束：禁止只存在于 Action 的逻辑）。
3. 输出：创建 draft PR + issue 回复证据链摘要；无 devcontainer/非标准脚手架 → 优雅降级回复（S05）。
4. 密钥走 GitHub secrets；超时 30 分钟硬上限；进度 issue 评论实时更新。
```

**验收（=M1）**：测试仓库 issue 贴截图 → draft PR 全自动产出；在 ≥2 个真实开源 React 仓库演练成功或明确降级。
**记录**：REPORT 记录每个演练仓库的结果矩阵（成功/降级/失败原因分类）。

### EXP-11 M1 复盘与双语启动（W8）

**人工为主，AI 辅助**：
```text
【EXP-11 指令】
1. 汇总 REPORT-001 中 EXP-01~10 的指标，生成 M1 阶段复盘小节：各 KPI 达成表、是否正收益结论、四类问题（A/B/C/D）badcase 统计、约束合规自查（02-MANUAL §2 逐条）。
2. 将 README.md 翻译为英文版 docs/README.en.md（保留中文版互链），术语按 02-MANUAL §8.4 统一。
3. 起草 M2 基准挖掘用的 GitHub 搜索查询语句草案（语言 JS/TS、issue 含 image、关联 PR merged、diff≤5 文件），先 dry-run 统计候选量，不抓全量。
```

**验收**：复盘小节含全部指标与结论；英文 README 完成；候选量统计 ≥1000（支撑 300 例目标）。

---

## 4. 例行实验

### EXP-12 竞品/论文月扫（每月最后一个周五，30 分钟）

```text
【EXP-12 指令（例行，直接粘贴）】
联网检索并输出简报：
1. GitHub 搜索：screenshot fix / visual bug fix agent / UI repair agent，列出 star>50 或一个月内新建的同环项目（对比上次记录）。
2. arXiv：过去 30 天 visual software repair / UI bug fix / multimodal SWE agent / visual fault localization 新论文。
3. 重点复查三个已知对象的状态：SWE-PolyVision（CosmosMind-ai）repo 动态；VisualRepair 代码是否放出；Devin/Antigravity 是否产品化"贴截图一键修"。
输出：变化点列表（新增/升级/威胁评级低中高）+ 是否触发 02-MANUAL §2 约束或叙事调整建议。结果追加进 REPORT-001 的月扫小节。
```

## 5. 远期实验池（M2+，先占位不展开）

| 编号 | 名称 | 目标 |
|---|---|---|
| EXP-13 | VisBugBench 挖掘管线 | 候选→过滤→半自动行级标注→人工抽查 20% |
| EXP-14 | 已有方法复评 | 用本 oracle 重评 GUIRepair/SVRepair 公开结果 |
| EXP-15 | 模型横评 | 免费 API 开源模型 vs 闭源在基准上的差距表（论文核心表） |
| EXP-16 | 成本/速度压测 | 全基准跑一遍的 token/时长/费用预算 |
| EXP-17 | Vue/Flutter 适配器模板 | 插件 API 定稿 + good first issue 模板 |

## 6. Vibe Coding 十条纪律

1. 一次一个实验，跑完记录再开下一个；
2. 每次会话先粘贴上下文锚（§2）；
3. 指令块里写清约束与"完成后停下等 review"；
4. AI 代码必须逐行人工 review——质量责任在你不在 AI（04-PLAYBOOK §1）；
5. 验收命令是唯一完成标准，"看起来能跑"不算；
6. 失败实验同样记录（负结果也是结果，不造假）；
7. AI 引入的每个新依赖都要过一遍 T 约束（尤其 T01/T08）；
8. 提示词改动=代码改动，版本化进 prompts.py 注释；
9. 不让 AI 大规模重构——重构走独立小步 commit；
10. 卡住 30 分钟以上：停下，把问题写进 PROGRESS，明天再说。

## 附录 A 技能库（SKILL-NN，自我进化沉淀位）

> 规则：只有"可复用的解法"才配进技能库；一次性事实回 PROGRESS/REPORT。新技能 = 一段可直接复用的指令/配置/排查流程。

| 编号 | 技能 | 状态 |
|---|---|---|
| SKILL-01 | （预留）Playwright 禁动画/确定性渲染完整配置模板 | EXP-03 后从 REPORT 蒸馏 |
| SKILL-02 | （预留）VLM 输出 JSON Schema 校验与重试模板 | EXP-04 后蒸馏 |
| SKILL-03 | 中文 Windows + 中文路径 conda 环境 editable 安装坑（完整解法） | ✅ 2026-10-29 EXP-01 沉淀 |

### SKILL-03 详情：中文路径 editable 安装与 GBK 毒 .pth（2026-10-29，EXP-01）

- **现象**：`pip install -e .` 后，该 conda 环境内**任何** python 启动即崩：`UnicodeDecodeError: 'gbk' codec can't decode byte 0x80 ...`（traceback 落在 `site.addpackage`）。
- **根因**：项目路径含中文（`…\开源项目\…`）；hatchling 等后端以 UTF-8 把源码路径写入 `site-packages/*.pth`；Python ≤3.11 的 site 模块按**硬编码 locale（GBK）**读取 .pth；「开」的 UTF-8 第三字节 0x80 不是合法 GBK 续字节 → site 初始化崩溃。`PYTHONUTF8=1` **无效**（UTF-8 模式不改变 .pth 读取编码）。
- **解法（按序）**：
  1. 删毒：删除 `site-packages/` 下本项目对应的 `*buglens*.pth`（hatchling 命名 `_editable_impl_*.pth`，pip 命名 `__editable__.*.pth`），python 立即恢复；
  2. `pyproject.toml` 构建后端改 `setuptools.build_meta`（pip 写 .pth 使用 locale=GBK，中文路径合法）；
  3. 重装后自检（必做）：`python -c "import buglens"` 通过；可选字节校验 .pth 可 GBK 解码。
- **预防**：本机 conda 环境下的项目一律 setuptools 后端；每次 editable 重装后跑自检；CI/Linux 为 ASCII 路径无此问题。
- **关联坑**：pypi.org 直连 SSL 间歇断连会产生**无 RECORD 的堆叠 dist-info**（pip 报 `uninstall-no-record-file`），解法 = 删除该包全部 dist-info + 目录后走 TUNA 镜像（`-i https://pypi.tuna.tsinghua.edu.cn/simple`）重装。
