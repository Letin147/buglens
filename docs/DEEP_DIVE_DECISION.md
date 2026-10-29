# BugLens 深度调查与唯一立项决策报告（Deep-Dive Decision Report）

> **决策结论：在全部候选中，唯一高价值项目 = BugLens（截图→复现→定位→修复→像素验证→证据链 PR 的多智能体系统）。**
> 本轮为第二轮"证伪式"深查（2026-10-28）：第一轮找支持证据，本轮专门找推翻证据。

| 项 | 值 |
|---|---|
| 决策日期 | 2026-10-28 |
| 决策方式 | 三路独立证伪调查（竞品存在性 / 学术空白核验 / 经济性与决赛对比）+ 撞车监视项定向定位 |
| 输入文档 | [PROJECT_BLUEPRINT.md](PROJECT_BLUEPRINT.md)（v1.0 → 已随本轮修订为 v1.1） |
| 决策结果 | **立项 BugLens，否决 MCPForge 及其余候选**；学术定位收窄为窄口径空白；投稿主战场改为 ASE 2027 + NeurIPS 2027 D&B |

---

## 0. 最终裁决

**决赛裁决矩阵**（深查③，数据见第 2 节）：

| 维度 | A BugLens | B MCPForge |
|---|---|---|
| 受众规模 | **5**（全球 JS 开发者约 2800 万） | 2（MCP server 作者约 10⁴–10⁵） |
| 需求频次 | **4**（"只贴截图的 bug 报告"是社区公认常态） | 3 |
| demo 传播力 | **5**（同基因先例 screenshot-to-code 一周破万星） | 2 |
| 变现天花板 | **4**（Devin $20/月起验证付费） | 3 |
| 防御性（被大厂吸收风险） | 3（Devin/Antigravity 可跟进，但闭环工程深度可筑墙） | 2（**已被吸收**：Anthropic 官方 Inspector 免费 11.2k★ + 官方 Registry 上线） |
| **总分** | **21/25** | **12/25** |

MCPForge 出局的决定性证据：受众比 BugLens 小 2–3 个数量级；其核心卖点（MCP 测试）已被协议所有者 Anthropic 用免费的官方 [MCP Inspector](https://github.com/modelcontextprotocol/inspector)（11,178★）覆盖，"MCP testing"关键词下 2026 年没有任何新千星项目——**天花板与防御性双输**。

---

## 1. 本轮深查方法

| 调查线 | 方法 | 目的 |
|---|---|---|
| ① 竞品存在性证伪 | GitHub Search API 9 组关键词（screenshot fix / visual bug fix agent / UI repair agent / fix from screenshot / visual regression agent 等）+ YC 2025–26 批次扫描 + Product Hunt + 中文生态（Gitee/魔搭/Trae）+ 插件生态（OpenHands/Cursor/Copilot Extensions）+ Argos 转型核查 | 推翻"生态位为零"假设 |
| ② 学术空白核验 | 精读 GUIRepair（[2506.16136](https://arxiv.org/abs/2506.16136)）与 SWE-bench Multimodal（[2410.03859](https://arxiv.org/abs/2410.03859)）原文；扫描 2026-07 至 2026-10 全部新论文；核验 CCF 认定规则与四大会议截稿日历 | 推翻"四大空白"宽口径表述 |
| ③ 经济性与决赛 | GitHub API 核验对标项目 star 曲线；收集开发者社区需求帖；核验 GLM/DeepSeek 当前定价；估算单任务成本；A/B 五维裁决 | 用数据裁决唯一立项对象 |

---

## 2. 证伪结果：十条假设的裁定

| # | 首轮假设（v1.0 表述） | 深查发现 | 裁定 |
|---|---|---|---|
| 1 | 开源生态位为零 | 找到 6+ 个实现大部分闭环的仓库：[ReproSight](https://github.com/toMYASDESIGNER/ReproSight)（Codex 插件，缺 PR 环）、[visual-bug-hunter](https://github.com/yitao2027/visual-bug-hunter)（缺自动复现）、[BugPack](https://github.com/duhuazhu/BugPack)（34★，MCP 出修复指令不自主修）等——**全部 0–6★、黑客松/玩具级**；GUIRepair 官方仓库亦 0★ | **字面证伪，实质存活**：赛道占用度约 30%，"有相邻者，核心闭环无有实力的占用者" |
| 2 | 商业付费意愿已验证 | Devin 2026-02 推 PR 评论 autofix+浏览器截图证据（输入是评论非截图）；Google Antigravity 在 IDE 内做修复后视觉验证；Cursor/Claude Code 支持贴图手动修——**大厂只有闭环的零件，无一键闭环产品**；Reticle/Quash/BetterBugs 只采集不修 | **证实并强化**：头部玩家都在向此收敛=方向正确；无人完整占位=窗口仍在 |
| 3 | 中文生态空白 | Gitee/魔搭/Trae 检索无同类项目（仅火山引擎 GUI 操作类文章、MarsCode 文本 APR 实践） | **证实**：中文首发优势可叠加 |
| 4 | 无像素级/可执行视觉验证 oracle | SWE-bench M 有 **69/617 实例**的测试本身用 Puppeteer/Pixelmatch 像素比对；[SWE-PolyVision](https://arxiv.org/abs/2609.29754)（2026-09，92 任务/36 组织）已是可执行多模态基准——但评测目标是**跨图像溯因推理**；而所有修复方法（GUIRepair/VisualRepair/SVRepair）的**最终裁决仍是 LLM 主观判断** | **宽口径推翻，窄口径存活**：立项目标必须收窄为"**修复循环内**统一、全量的可执行视觉 oracle" |
| 5 | 复现保真度从未被量化 | [ReBug](https://arxiv.org/abs/2608.03598)（2026-08）已量化真实浏览器复现成功率 **RSR 49.96%**（667 份 bug 报告）——但只做复现不做修复；GUIRepair 式"LLM 生成代码近似复现"在**修复管线内**的保真度仍无人度量 | **宽口径推翻，窄口径存活**："修复管线内 Image2Code 复现保真度"可辩护 |
| 6 | 无行级视觉故障定位 ground truth | SWE-bench M 全部 17 库为 JS/TS，仅文件级 F1（Agentless JS 0.142）；2026 年全部后续工作（含 SWE-PolyVision）均未提供行级标注；OmniGIRL 视觉子集仅 19 例 | **完全存活（最结实空白）** |
| 7 | 全绑定闭源大模型 | [SVRepair](https://arxiv.org/abs/2602.06090)（蚂蚁 codefuse）已微调开源 VLM 达 186/517 且[代码开源](https://github.com/codefuse-ai/CodeFuse-SVR)；[VisualRepair](https://arxiv.org/abs/2607.14075)（CUHK）以 196/517 居 SOTA（代码未放） | **部分推翻**：改述为"免费 API 开源模型 vs 闭源的系统差距与可复现管线缺失" |
| 8 | 需求真实性 | 直接证据：[r/ClaudeAI 用户贴 UI 截图让 AI 修](https://www.reddit.com/r/ClaudeAI/comments/1v3ota6/im_using_claudeai_to_fix_claudeais_ui_bugs)、[r/SaaS 开发者访谈确认"只贴截图无复现步骤"是核心痛点](https://www.reddit.com/r/SaaS/comments/1rtcw19/spent_a_week_talking_to_developers_about_bug)、HN 高赞 ["virtually all bug reports don't provide sufficient reproduction steps"](https://news.ycombinator.com/item?id=47522704) | **证实** |
| 9 | 经济性可行 | [GLM-4V-Flash 仍免费](https://docs.bigmodel.cn/cn/guide/start/model-overview.md)（另有免费 GLM-4.6V-Flash，128K 上下文）；[DeepSeek flash 支持视觉](https://api-docs.deepseek.com/quick_start/pricing)，输入 $0.15–0.30/百万 token；典型任务（5 次 VLM×2 图 + 10 次文本）成本 **≈ $0.005–0.01/bug** | **证实并强化**：可承受多次验证重试循环 |
| 10 | 增长潜力（决赛） | 对标曲线：[screenshot-to-code](https://github.com/abi/screenshot-to-code) 2 天 1k★、**1 周 10k★**（新奇玩具型，后停滞于 80.8k）；[browser-use](https://github.com/browser-use/browser-use) 2 周 1k★、3 个月 10k★、现 119k（留存基建型）；BugLens 兼具两者基因，合理天花板 30–80k★ | **证实** |

---

## 3. 为什么"被证伪"反而加强了立项信心

1. **6+ 个玩具仓库 = 需求被反复尝试、执行质量是唯一门槛。** 这些 0–6★ 的失败/半成品尝试（多数是黑客松产物）证明人们"想要这个东西"，但没有人做出工程可用的质量。BugLens 的胜负手不在创意（创意已公开存在），而在：确定性复现 profile、修复循环内可执行 oracle、证据链协议、框架适配器、CI 化交付——全部是工程深度，恰是个人开发者在 AI 辅助下可以堆出来的。
2. **学术跟进密集 = 赛道被顶会确认热门。** 2026 年 2 月至 10 月至少 6 篇新论文（VisualRepair/SVRepair/ReBug/GALA/RepoRepair/SWE-PolyVision）涌入，说明审稿人认这个方向；而它们集体留出了"**评测基础设施**"（oracle、复现保真度、行级 GT）没人做——做基建的人引用量最大（参照 SWE-bench 系列本身的引用轨迹）。
3. **GUIRepair 官方仓库 0★ = 论文影响力未转化为开源力量。** 学术界做了方法但没有做出开发者能装能用的工具；工程位（CLI/Action/MCP 三形态 + 真实仓库复现）依然完全空着。
4. **大厂只做了零件**：Devin 的输入是 PR 评论、Antigravity 在 IDE 内、Cursor 要人肉贴图——"issue 里贴张截图就出带证据的 PR"这个用户动线没有任何产品完整提供。

---

## 4. 修正后的定位声明（对外统一口径）

> **BugLens 不是"首个做截图修 bug 的"（GUIRepair 等已存在），而是首个把这件事做成"工程可信 + 学术可测"的开源系统**：
> ① 唯一在**修复循环内**使用可执行视觉 oracle（像素 diff + 布局断言 + 既有测试）而非 LLM 主观判断的开源工具；
> ② 唯一在**真实仓库环境**确定性复现（而非 LLM 生成代码近似）并量化复现保真度的开源工具；
> ③ 首个提供**行级视觉故障定位 ground truth** 的基准（VisBugBench-Pro）；
> ④ 全管线跑**免费/低价开源模型 API**（GLM-4V-Flash 主力），附带系统性的开源 vs 闭源差距评测。

**差异化对照表（深查版）**：

| 能力 | 玩具仓库(6+) | GUIRepair (ASE'25) | VisualRepair (SOTA) | SVRepair | Devin/Antigravity | **BugLens** |
|---|---|---|---|---|---|---|
| 截图输入→PR 输出闭环 | 部分 | 部分（论文内） | 论文内 | 论文内 | 零件 | ✓ 完整 |
| 真实环境确定性复现 | ✗ | ✗ LLM 近似 | ✗ | ✗ | 闭源不可知 | ✓ |
| 修复循环内可执行 oracle | ✗ | ✗ LLM 判 | ✗ LLM 判 | ✗ LLM 判 | 闭源 | ✓ |
| 行级定位 ground truth | ✗ | ✗ | ✗ | ✗ | ✗ | ✓（基准） |
| 开源免费可用 | ✓(玩具) | 0★ 存疑 | 未放 | ✓(微调系) | ✗ | ✓ 免费API |
| 证据链可审计 PR | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |

---

## 5. 修正后的学术路线（窄口径空白 + 投稿日历）

### 5.1 撞车监视项处理结果

**SWE-PolyVision 已定位**：[arXiv:2609.29754](https://arxiv.org/abs/2609.29754)、[GitHub](https://github.com/CosmosMind-ai/SWE-PolyVision)。92 任务/36 组织、48 公开 + 44 私有保留，评测焦点是**跨图像溯因推理**（多图推理能力隔离测评）——与本项目窄口径空白（修复循环 oracle / 管线内复现保真度 / 行级 GT）**相邻不重叠**。处理：不构成转向；M2 期间精读其数据构成（语言覆盖、标注粒度）并在相关工作中显式引用区分。其前身 [SWE-PolyBench](https://arxiv.org/abs/2504.08703)（Amazon）为多语言文本基准，同样不重叠。

### 5.2 投稿日历（已核验，取代 v1.0 第 5 节）

| 目标 | 会议/track | 截稿 | 备注 |
|---|---|---|---|
| 展示位（可选） | FSE 2027 Tool Demo（深圳） | **2027-01-26** | ⚠️ CCF 目录只认主会长文，demo **不自动算 A 类**——只做曝光，不当学术主目标 |
| **主投 P1 基准论文** | NeurIPS 2027 Datasets & Benchmarks | 约 2027-05 | 历史规律 5 月中下旬；VisBugBench-Pro 主投位 |
| **主投 P2 方法论文** | ASE 2027 research | 约 2027-03 下旬 | 参照 ASE 2026 节奏（research 2026-03-26） |
| 备选 | ICSE 2028（仅夏季单周期） | 约 2027-03 | ICSE 已取消春季周期 |
| 占坑 | arXiv preprint | **目标 2027-01 前** | 基准+初步结果先挂 arXiv 防撞车（该方向月均 1 篇新论文） |

**M2 里程碑据此微调**：基准数据 + 行级标注须在 2027-01 前完成首版并挂 arXiv（原计划 2026-12 前后，节奏可行）；论文写作与 M3 发布并行。

### 5.3 叙述纪律（写作红线）

以下宽口径表述**永远不要出现**在论文/README/宣传中（审稿人或社区一句即可击穿）：
- ❌ "首个/唯一的视觉修复验证 oracle"→ ✅ "修复循环内的可执行视觉 oracle"（并引用 SWE-bench M 的 69 个像素测试实例、SWE-PolyVision）
- ❌ "复现保真度从未被量化"→ ✅ "修复管线内 LLM 近似复现的保真度未被度量"（并引用 ReBug RSR 49.96%）
- ❌ "此前全部绑定闭源模型"→ ✅ "免费 API 开源模型路线的可达性与差距未被系统评估"（并引用 SVRepair）

---

## 6. 风险登记册更新（相对 v1.0 第 9 节的增补）

| # | 风险 | 概率 | 影响 | 增补对策 |
|---|---|---|---|---|
| R4′ | 学术撞车：VisualRepair（SOTA 196/517）代码"接收后开源"，其代码放出后社区可能跟进工具化 | 中 | 中 | 抢时间窗：2027-01 前 arXiv 占坑；工具位与论文位并行占 |
| R9 新 | Devin/Antigravity 把"贴截图→自主修→PR"产品化为一键功能 | 中 | 高 | 护城河=开源+免费+可本地+证据链可审计+基准中立评测（大厂不会公开失败率，我们会） |
| R10 新 | SWE-PolyVision 团队后续版本加入行级标注 | 低 | 高 | M2 期间每月重扫其 repo 一次；若发生，将基准重心移向移动端 H5/Flutter Web/桌面端（其 36 组织以 JS 为主） |
| R11 新 | 玩具仓库中某一个突然获得牵引（如 BugPack 34★） | 低 | 低 | 保持关注即可；工程质量与三形态交付是数量级差异 |

---

## 7. 对 PROJECT_BLUEPRINT.md 的修订清单（v1.0 → v1.1，已同步执行）

1. §0 执行摘要依据 1：'开源竞品为零' → '开源生态无有牵引力的占用者（占用度约 30%）'，补充玩具仓库事实；
2. §0 依据 2：'首个 reproduction-rate 指标' → 窄口径表述；
3. §1.3 已有工作：补 VisualRepair（SOTA 196/517）、SVRepair（开源 186/517）、ReBug（RSR 49.96%）、GUIRepair 仓库 0★ 等深查事实；
4. §1.3 四项空白：宽口径 → 窄口径四条 + SWE-PolyVision 监视项处理结果；
5. §4.2 创新点表：'首个' 类措辞全部收窄为可辩护口径；
6. §5 学术路线：投稿日历整体替换（FSE research 已过截稿；tool demo 不算 CCF-A；主投 ASE 2027 + NeurIPS 2027 D&B；arXiv 2027-01 前占坑）；
7. §9 R4 对策更新；
8. 附录 A 来源清单增补本轮新来源。

---

## 8. 启动指令（唯一项目已定，下一步唯一动作 = M0 开工）

1. 核查 `buglens` 在 GitHub/PyPI 的可用性（备选 FixLens/ShotFix/Viseer）→ `git init` 首 commit（README + LICENSE + pyproject 骨架）；
2. 注册智谱 API key（GLM-4V-Flash 免费档，注意账户层级并发限制），跑通第一张截图的 VLM 结构化描述；
3. 选定 3 个 golden 案例仓库（Vite/React 标准脚手架 + 已知视觉 bug），搭 Playwright 确定性复现 profile；
4. M0 四智能体（Reproducer/VisualAnalyst/Locator/Fixer+Verifier 合一先行）+ CLI，验收标准不变：3/3 案例端到端、单案例成本 < ¥1；
5. 并行月度例行：重扫 SWE-PolyVision repo + `visual repair` arXiv 新论文（防 R10/R4′）。

---

## 附录：本轮深查主要来源

**竞品存在性**：GitHub Search API 九组关键词（ReproSight、visual-bug-hunter、BugPack 等 6+ 仓库）；[Devin autofix 公告](https://cognition.com/blog/closing-the-agent-loop-devin-autofixes-review-comments)；[Google Antigravity](https://gend.co/en-ca/blog/google-antigravity)；[Argos 面向 agent 的 MCP/API](https://argos-ci.com/docs/agents/agents)；[OpenHands 视觉反馈 Issue #8372](https://github.com/OpenHands/OpenHands/issues/8372)。

**学术核验**：GUIRepair [2506.16136](https://arxiv.org/abs/2506.16136)（o4-mini 175/517，仓库 0★）；SWE-bench M [2410.03859](https://arxiv.org/abs/2410.03859)（617/619 实例、17 库全 JS/TS、69 像素测试实例、无行级标注、每库约 10 小时人工环境搭建）；VisualRepair [2607.14075](https://arxiv.org/abs/2607.14075)（SOTA 196/517）；SVRepair [2602.06090](https://arxiv.org/abs/2602.06090)（[代码](https://github.com/codefuse-ai/CodeFuse-SVR)）；ReBug [2608.03598](https://arxiv.org/abs/2608.03598)（RSR 49.96%）；SWE-PolyVision [2609.29754](https://arxiv.org/abs/2609.29754)（[代码](https://github.com/CosmosMind-ai/SWE-PolyVision)）；[FSE 2027 官网](https://conf.researchr.org/home/fse-2027)（Tool Demo 2027-01-26）；[ICSE 新闻页](http://www.icse-conferences.org/news.html)（春季周期取消）。

**经济性与决赛**：[r/ClaudeAI 截图修 bug 帖](https://www.reddit.com/r/ClaudeAI/comments/1v3ota6/im_using_claudeai_to_fix_claudeais_ui_bugs)；[r/SaaS 开发者访谈](https://www.reddit.com/r/SaaS/comments/1rtcw19/spent_a_week_talking_to_developers_about_bug)；[HN 复现步骤缺失讨论](https://news.ycombinator.com/item?id=47522704)；[browser-use Launch HN](https://news.ycombinator.com/item?id=43120005)；[screenshot-to-code Show HN](https://hn.algolia.com/api/v1/search?query=abi%20screenshot-to-code)；[Glama MCP 注册表 111,593 server](https://glama.ai/mcp/servers)；[MCP Inspector](https://github.com/modelcontextprotocol/inspector)；[GLM 模型总览](https://docs.bigmodel.cn/cn/guide/start/model-overview.md)；[DeepSeek 定价](https://api-docs.deepseek.com/quick_start/pricing)；[SlashData JS 开发者 2800 万](https://www.slashdata.co/blog/javascript-has-28-million-users-what-this-reveals-about-the-future-of-global-tech-teams)。
