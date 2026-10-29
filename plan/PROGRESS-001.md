# BugLens 进展日志 · 卷一（PROGRESS-001）

> **滚动规则**（02-MANUAL §14）：本文件只追加不修改；总行数超过 1500 行 → 开 `PROGRESS-002.md`，旧卷末尾写"承接 PROGRESS-002"。更正历史 = 新卡片引用旧卡片编号。
> **每日卡片模板**：

```
## #NNN YYYY-MM-DD [a/b]
- 今日目标：
- 做了什么：（条目式，含文件/commit/实验号）
- 结果与证据：（数字/链接/工件号，没有就写"无，原因"）
- 问题与坑：（含解法或排查到哪一步）
- 明日入口：（精确到实验号/文件名/动作）
```

---

## #001 2026-10-28
- 今日目标：完成项目立项前的全部调研与决策。
- 做了什么：
  1. 三路并行调研（GitHub 高星规律 / arXiv 学术前沿 / 竞品与商业化）→ docs/PROJECT_BLUEPRINT.md v1.0；
  2. 证伪式深查（9 组关键词竞品扫描 / GUIRepair 与 SWE-bench M 原文精读 / 经济性与决赛对比）→ docs/DEEP_DIVE_DECISION.md，BLUEPRINT 修订至 v1.1；
  3. 决策：唯一立项 BugLens（决赛 21/25 vs MCPForge 12/25）；窄口径学术定位；投稿主战场 ASE 2027 + NeurIPS 2027 D&B；SWE-PolyVision 撞车监视项解除（arXiv:2609.29754，跨图溯因推理，相邻不重叠）。
- 结果与证据：两份定稿文档（各含来源附录）；关键数字：赛道占用约 30%、GUIRepair 175/517、VisualRepair SOTA 196/517、单案例成本估算 $0.005–0.01、GLM-4V-Flash 免费。
- 问题与坑：无（调研日）。
- 明日入口：#002 建立项目管理体系（四文档+日志体系）。

## #002 2026-10-28
- 今日目标：建立项目管理体系，形成可开工状态。
- 做了什么：
  1. 建立 plan/、manual/、reports/ 三个分区 + docs/ 定稿区 + .gitignore（五分区隔离制度见 01-PLAN §4）；
  2. 撰写四份核心文档：plan/01-PLAN.md（八周路线与项目管理）、manual/02-MANUAL.md（约束与操作手册）、manual/03-EXPERIMENTS.md（EXP-01–12 实验指令）、manual/04-AGENT-PLAYBOOK.md（Agent 工程方法论）；
  3. 开立本日志卷一与 reports/REPORT-001.md 卷一。
- 结果与证据：文档树 8 个文件全部落盘；EXP-00（立项调研）已作为首条实验记录写入 REPORT-001。
- 问题与坑：暂无。
- 明日入口：W1 启动——① 核查 buglens 命名（GitHub/PyPI，备选 FixLens/ShotFix/Viseer）；② 按 03-EXPERIMENTS EXP-01 指令粘贴给编码智能体做仓库基建；③ 注册智谱 API key。

## #003 2026-10-29
- 今日目标：W1/EXP-01 仓库基建（01-PLAN §5 W1 行 + 03-EXPERIMENTS EXP-01 卡片）。
- 做了什么：
  1. 命名核查：PyPI `buglens` → 404 空闲；GitHub 顶层同名 `seclab-ucr/BugLens` 为 42★ 的 CodeQL 安全论文附件（2025-05 建、2026-07 后未推送）、领域不同冲突低 → **决策：保留 buglens**（备选 FixLens/ShotFix 在 PyPI 亦空闲，发布前再复核）；
  2. `git init -b main`；下载官方 Apache-2.0 LICENSE（202 行）；
  3. 基建落盘：pyproject.toml（src 布局、console_scripts、ruff/mypy/pytest 配置）、src/buglens/{__init__,cli}.py（Typer 骨架）、tests/test_cli.py、Makefile、.github/workflows/ci.yml；
  4. conda lumin（用户指定环境）安装与三轮排障，验收四连全绿。
- 结果与证据：ruff "All checks passed!"；mypy strict "no issues found in 2 source files"；pytest "2 passed in 0.18s"；`buglens --version` → `buglens 0.1.0`。版本指纹：Python 3.11.14(conda-forge) / langgraph 1.2.18 / langchain-core 1.7.1 / pydantic 2.12.5 / typer 0.24.1 / playwright 1.57.0 / setuptools 82.0.0 / pip 26.0.1（TUNA 镜像安装）。CI 未验证（无远程仓库，待推送后首触）。
- 问题与坑：
  1. 【已解决·重大，沉淀 SKILL-03】中文路径 editable 毒 .pth：hatchling 后端以 UTF-8 把中文路径写入 .pth，Python 3.11 site 模块以硬编码 GBK 读取 → lumin 内所有 python 启动即崩（报错位置 20 精确对位「开」的 UTF-8 第三字节 0x80；PYTHONUTF8=1 无效）。修复：删毒 .pth → 构建后端换 setuptools（pip 以 locale/GBK 写 .pth，字节 \xbf\xaa\xd4\xb4=GBK「开源」实证）→ 重装自检通过；
  2. 【已解决】lumin 预存腐坏：pypi.org SSL 间歇断连导致 langgraph/langchain 家族堆叠多个无 RECORD 的 dist-info（langchain-core×4、langgraph×3…），pip 无法卸载。修复：外科手术清空该家族目录 + 清华 TUNA 镜像干净重装；
  3. 【遗留观察，不动用户环境】lumin 有既有残留：`~ill`/`~ltralytics` 无效分发（中断的 ultralytics 卸载）、`langchain-text-splitters 0.0.2` 与 langchain-core 1.7 声明冲突——均仅告警不影响运行；
  4. 【化妆问题】Git Bash 以 GBK 显示 UTF-8 制表符致 CLI 输出乱码，功能无损（Windows Terminal+UTF-8 可解）。
- 明日入口：EXP-02 VLM 摸底——① 注册智谱 key（GLM-4V-Flash 免费档）；② 选定 golden-1 案例仓库并人工截 3 张 bug 截图存 temp/；③ 按 EXP-02 指令块执行（脚本不入库）。

