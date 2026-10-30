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


## #004 2026-10-29
- 今日目标：EXP-02 VLM 摸底（W1 第二项）。
- 做了什么：智谱 key 入库（.env，gitignore 验证；删除明文 1.txt；新增 .env.example）；搭 golden-1 案例仓库（Vite5+React18+TS，3 个 bug 页面）；补装 Playwright chromium v1200；三轮探测（v1×原案例 → ground truth 核验 → 案例重构 → v2×新案例）；独立视觉分析工具核验全部 ground truth。
- 结果与证据：v1 解析 2/3（命中皆吹毛求疵）；v2 解析 2/3（bug3 部分命中=专业版卡片错位；bug1 三连漏检；bug2 限流无数据）；免费档限流窗口 >10 分钟。详细三轮对照与五条结论见 REPORT EXP-02。
- 问题与坑：① SKU 含连字符即可断行——溢出案例必须用无断点长串；② "约 90% 隐藏"的缺陷对人对模型都不可检，案例要"明显但不极端"；③ 免费档长限流：探测类任务改天再跑或切付费档；④ python 后台跑脚本要加 -u 否则 stdout 缓冲看不到进度；⑤ probe 脚本读 .env 是相对路径，必须从项目根运行。
- 明日入口：W2/EXP-03 复现官确定性 profile（ReproProfile：固定视口/时区/禁动画/种子 + golden-1 连跑 10 次 dom 哈希一致、SSIM≥0.999）；bug2 补测窗口恢复后顺带跑。

## #005 2026-10-29
- 今日目标：W2/EXP-03 复现官确定性 profile。
- 做了什么：src/buglens/repro/ 三模块（profile/launcher/reproducer，localhost-only 路由守卫先行落地 T10）；tests/test_repro_determinism.py（块 SSIM+DOM 哈希，BUGLENS_REPRO_RUNS 可调）；pyproject dev extras 增 numpy/pillow；两轮验收（第一轮被孤儿服务器污染→修复端口断言→第二轮真 10 连跑）；顺带完成 EXP-02 的 bug2 补测（命中）。
- 结果与证据：第二轮 10 连跑 DOM=d3d48e44f397 全一致、SSIM=1.000000×9、采集 2.2–2.5s/次（含启动 ~4s/次）、总 83s；ruff/mypy 绿；bug2 补测 symptom 正确识别溢出。详见 REPORT EXP-03 / EXP-02 补测。
- 问题与坑：① Git Bash 下 taskkill 的 /F /T 会被 MSYS 转成路径，须用 //F //T 形式（或 Python subprocess 数组传参不受影响）；② 后台 dev server 绝不能靠"杀 bash 任务"停止（不杀进程树留孤儿）——一律经 DevServerLauncher（现在有端口占用/释放双断言兜底）；③ vite dev 的 HMR websocket 使 networkidle 不可达，确定性锚点=固定 settle 时间；④ 第一轮"13 连跑全绿"是假复现——指标全绿≠语义正确，端口占用断言就是为这类静默错误设计的。
- 明日入口：EXP-04 视觉分析官（models/ Provider 抽象 + GLMProvider + agents/visual_analyst，提示词版本化进 prompts.py；遮挡类走 DOM+分块）。

## #006 2026-10-29
- 今日目标：首次全库安全与一致性审计（用户指令：脱敏/防幻觉/一致性/卫生/深度核查，推送 GitHub 前必须干净）。
- 做了什么：六项安全扫描（密钥历史/入库白名单/工作区密钥/作者信息/文件清单/TODO 与硬编码）；门禁三连复跑；两项承重研究数字回源核验（arXiv 原文摘要）；文档状态同步（README 徽章与里程碑、01-PLAN §10）；新增 plan/PRE_PUSH_CHECKLIST.md（A 脱敏/B 质量/C 语义三段）并升级 02-MANUAL 至 v1.2（新约束 E06：推送前清单强制）。
- 结果与证据：密钥在全部 8 个提交的历史中出现次数=0；`git ls-files` 白名单 33 文件与 §7.1 设计一致；`1.txt`/`.env` 从未入库；ruff/mypy/pytest 全绿（3 passed/29s）；GUIRepair 摘要原文 "solve 175 instances"（o4-mini）与 ReBug 原文 "average RSR of 49.96% / 667 real-world bug reports" 均与文档表述精确一致——无幻觉；README/01-PLAN 状态已同步至 W2 进行中。
- 问题与坑：① `grep -r` 对 `.env` 点文件在本机 Git Bash 下未列出（直接 `ls`+`grep .env` 复核通过）——点文件扫描一律显式点名复核，不依赖通配；② 提交作者为个人 QQ 邮箱，推送后将永久公开——已列入推送前清单 A4 交所有者决策（保留 or noreply+重写，仓库尚无远程，重写安全）。
- 明日入口：EXP-04 视觉分析官开工（models/ Provider 抽象 + GLMProvider + agents/visual_analyst，提示词版本化进 prompts.py，遮挡类配 DOM 通道）。

## #007 2026-10-29
- 今日目标：脱敏推送 + EXP-04 视觉分析官。
- 做了什么：① 脱敏：GitHub ID 259059639，git 身份改 Letin147 <noreply>，rebase 重写全部 9 提交（作者仅剩 noreply，密钥历史复扫 0）；② PRE_PUSH_CHECKLIST 全项通过后建仓推送 https://github.com/Letin147/buglens（topics×8），CI 首跑 15s 绿，main 分支保护（require PR+check，admin 可绕）；③ EXP-04：models/ Provider 层+缓存+GLMProvider、graph/state.py、agents/visual_analyst（v3-domfacts 提示词）、overlays 采集、mock 单测×5；按分支纪律走 PR #1（CI 绿）；④ 真实运行 2/3（配额窗口 2 次）。
- 结果与证据：门禁三绿（mypy 18 文件/pytest 8 passed）；**bug1 遮挡类首次区域命中**（DOM 事实通道生效，EXP-02 三连漏检被翻盘，因果仍偏差）；bug2 命中 conf 0.9；缓存 cached=True；bug3 挂起待配额。详见 REPORT EXP-04。
- 问题与坑：① 本机存在**失效的 GITHUB_TOKEN 环境变量**，会劫持 gh 与 git push 凭据（credential.helper=manager-core 下尤甚）——一律 `env -u GITHUB_TOKEN -u GH_TOKEN` 前缀绕过（已沉淀为惯用法，未改用户环境）；② 免费档配额窗口实测 2 次/窗口、当日累计约 8 次即长时间 429；③ mypy strict 抓到 get_api_key 缺 return 的真 bug（门禁价值实证）。
- 明日入口：bug3 补测（配额恢复即跑）→ EXP-05 定位官（BM25+bge-m3+tree-sitter 三路召回 RRF 融合，行级 top-5）。

## #008 2026-10-29
- 今日目标：EXP-05 定位官 + bug3 补测。
- 做了什么：repo/（tree-sitter 切片+CSS 规则切片+BM25+bge-m3 向量）、agents/locator（RRF 融合+证据挂接）、CLI index init、overlays covers 线索扩展、提示词 v4-covered；bge-m3 魔搭下载+bin→safetensors 本地转换；真实定位两轮（首轮 bug2 漏检→修 identifier 连字符 bug→3/3）。
- 结果与证据：门禁三绿（pytest 14 passed）；索引 32 切片/31.5s；**真实定位 3/3 全部 top-1 三通道全亮**（bug1=index.css:41-48 精确到修复行）；covers 实采=navbar→button.btn-primary"提交订单"。bug3 VLM 补测与 v4 验证仍被配额挡（两次 429），顺延。
- 问题与坑：① transformers CVE-2025-32434 闸门：torch<2.6 拒绝 torch.load *.bin——解法=转 safetensors（safetensors.torch 需显式 import 子模块）；embedder 兜底要广谱捕获（ValueError 漏网教训）；② sentence-transformers 走 hf-mirror 会 HEAD 校验失败，改魔搭 snapshot_download 一发入魂；③ conda run 不支持多行 -c（第二次踩，已固化直调 python.exe）；④ identifier 检索必须与索引侧同构分词（连字符），fixture 别太仁慈。
- 明日入口：配额恢复→bug3 补测+v4 因果验证；EXP-06 修复工程师（planner/fixer + 最小 diff + worktree 副本应用/回滚）。
