# BugLens 实验报告 · 卷一（REPORT-001）

> **滚动规则**（02-MANUAL §14）：所有实验记录追加进本卷，**禁止一实验一文件**；总行数 >1500 → 开 `REPORT-002.md`（旧卷末尾写"承接 REPORT-002"，新卷开头写承接行与索引）。实验指令见 [manual/03-EXPERIMENTS.md](../manual/03-EXPERIMENTS.md)。
>
> **实验记录模板**（每条必填，真实可靠不造假——负结果照记）：

```
## EXP-NN 标题（YYYY-MM-DD）
- 目标/预期指标：
- 配置：环境指纹（Python/uv/lock 哈希）；模型指纹（provider/model/版本/参数）；输入指纹（案例版本/数据哈希）；seed。
- 结果：（真实数字+证据工件号 ev-xxx）
- 结论：是否达到成功目标 / 是否正收益：
- 问题与归因：（四步法：trace→输入→提示词版本→模型原始输出；分类 A/B/C/D）
- 下一步：
```

## 卷内索引

| 实验 | 日期 | 一行结论 |
|---|---|---|
| EXP-00 | 2026-10-28 | 立项调研完成，BugLens 唯一立项，窄口径学术定位确立 |
| EXP-01 | 2026-10-29 | 仓库基建验收全绿（ruff/mypy/pytest/CLI）；毒 .pth 事件解决并沉淀 SKILL-03 |
| EXP-02 | 2026-10-29 | VLM 摸底未达验收但目的达成：免费档长限流+遮挡类三连漏检→双通道/分块检测为必须（补测：溢出类命中） |
| EXP-03 | 2026-10-29 | 真·10 连跑验收通过（DOM 十跑一致/SSIM=1.0/约4s 每次）；发现并修复"孤儿服务器假复现"风险 |
| EXP-04 | 2026-10-29 | 视觉分析官落地：遮挡类区域命中（DOM 事实通道翻盘三连漏检）+溢出命中+缓存实证；bug3 待配额补测 |
| EXP-05 | 2026-10-29 | 定位官 3/3 全部 top-1 三通道全亮（bug1 精确到修复行）；covers 遮挡因果线索闭环；真实运行抓出 identifier 连字符 bug |

---

## EXP-00 立项调研与决策（2026-10-28）

- 目标/预期指标：从 6 个候选中选出唯一高价值项目，且关键假设全部经过证伪核验。
- 配置：两轮调研（首轮支持性调研 + 深查证伪式调研），检索范围 GitHub / arXiv / YC / Product Hunt / Gitee / 魔搭 / Trae / 社区论坛；模型指纹不适用（无模型实验）；输入=各平台实时检索（来源清单见 docs/DEEP_DIVE_DECISION.md 附录）。
- 结果：
  - 竞品存在性：核心闭环存在 6+ 个仓库但全部 0–6★（ReproSight、visual-bug-hunter、BugPack 等），GUIRepair 官方仓库 0★；赛道占用度约 30%；
  - 学术空白存活度：宽口径 4 条中 2 条被部分关闭（ReBug RSR 49.96% 关闭"复现未量化"宽口径；SVRepair 开源 VLM 关闭"全闭源"），窄口径 3 条成立（修复循环内可执行 oracle / 管线内复现保真度 / 行级视觉定位 GT 完全成立）；
  - 决赛数据：BugLens 21/25 vs MCPForge 12/25；受众 2800 万 JS 开发者 vs 10⁴–10⁵；单案例成本 $0.005–0.01；GLM-4V-Flash 免费（含新增免费 4.6V-Flash 128K）；
  - 撞车监视项：SWE-PolyVision 定位为 arXiv:2609.29754（跨图像溯因推理），与窄口径空白相邻不重叠，解除转向警报。
- 结论：**达到成功目标，正收益**——唯一立项 BugLens；学术与宣传一律采用窄口径表述（02-MANUAL §2.3 红线 N01–N04）。
- 问题与归因：首轮 v1.0 报告存在 3 处宽口径表述风险（已修订 v1.1），归因=初轮调研未读原文（类 C 幻觉的文档版：未挂证据的强断言），教训=强断言必须回原文核验后才能落稿。
- 下一步：W1 启动（01-PLAN §10 Next Actions）。

## EXP-01 仓库基建与环境基线（2026-10-29）

- 目标/预期指标：可安装空壳包 + 质量工具链全绿（EXP-01 卡片验收：`buglens --help` 可用、ruff/mypy/pytest 通过）。
- 配置：环境指纹 = Windows / conda env `lumin` / Python 3.11.14(conda-forge) / pip 26.0.1 / setuptools 82.0.0（TUNA 镜像）；依赖指纹 = langgraph 1.2.18、langchain-core 1.7.1、pydantic 2.12.5、typer 0.24.1、playwright 1.57.0；输入指纹 = 空仓库首版（无案例）；seed 不适用。
- 结果：ruff 全过；mypy strict 0 issue（2 files）；pytest 2 passed（0.18s）；CLI `--help`/`--version` 正常输出 `buglens 0.1.0`；editable `.pth` 经字节校验为 GBK 编码（`\xbf\xaa\xd4\xb4` = GBK「开源」），site 加载正常。
- 结论：**达到成功目标，正收益**。偏离记录（均已按约束变更流程修订 T06）：① Python 3.12+ → 3.11+（lumin 实为 3.11.14）；② 构建后端 hatchling → setuptools（中文路径 PEP 660 兼容性，SKILL-03）；③ 本地未装 make，验收逐命令执行（Makefile 保留供 CI/Linux）；④ CI 未首跑（无远程仓库，待推送）。
- 问题与归因：毒 .pth 事件归因 = 对工具链编码的无证据默认假设（"pip 全链 UTF-8"，类 C 问题）；教训 = 中文 Windows 上一切跨进程文本传递必须先验证编码。完整排障时间线见 PROGRESS #003。另修复 lumin 预存的 langgraph/langchain 无 RECORD 堆叠 dist-info 腐坏（SSL 断连所致）。
- 下一步：EXP-02 VLM 摸底（智谱 key → golden-1 截图 → 指令块执行）。

## EXP-02 VLM 摸底（2026-10-29）

- 目标/预期指标：验证 GLM-4.6V-Flash（免费档）对 UI 缺陷截图的结构化输出可用性底线。验收：3/3 解析成功 + bbox 人工粗评大致正确 ≥2/3（EXP-02 卡片）。
- 配置：模型=glm-4.6v-flash（免费，128K 上下文）；输入=golden-1 三页截图（1280x800 PNG，Playwright chromium 143/build v1200 截取）；提示词两版：v1（开放找缺陷）/v2（枚举功能缺陷类型：遮挡/溢出/错位/破碎，并明确排除配色边框类品味问题）；脚本=temp/exp02/{shoot,probe,probe_one}.py（不入库）；seed 不适用（视觉输入）。
- 结果（三轮，全部真实记录）：
  1. v1 × 原始案例：解析 2/3（bug2 撞 429）；bug1/bug3 的"命中"均为吹毛求疵（"间距过小"/"蓝色边框不一致"），注入缺陷全部漏检；
  2. ground truth 独立核验（视觉分析工具 + CSS 坐标计算交叉）发现**案例自身设计缺陷**：bug2 的 SKU 含连字符可断行→实际未溢出（设计失败）；bug1 标题约 90% 藏于导航栏后→"不可见的缺陷"无从检出。据此重构：bug1=提交订单按钮约 60% 被导航栏遮挡（y35–80）；bug2=无断点纯字母数字长串（实测从 x≈212 延伸至 x≈850，溢出约 340px 压过右卡）；bug3=中间卡片下沉 54px（顶边 y138 vs 84）；
  3. v2 × 重构案例：解析 2/3（bug2 因限流重试 5 次未恢复，无数据）；bug1 **三连漏检**（本轮报出"价格列对齐不一致"想象缺陷，confidence 0.9）；bug3 **部分命中**（正确指出专业版卡片垂直错位，但成因描述不精确、bbox 偏粗）。
  限流实测：当日累计成功约 5 次调用后进入长 429 窗口（静默 5 分钟 + 60s×5 重试后仍全灭）。
- 结论：**未达验收标准；但摸底目的完全达成，负结果如实入档**。五条结论：① 免费档限流窗口极长（>10 分钟不恢复），只能承担冒烟/演示用途，批量任务默认走付费低价档（DeepSeek flash ≈$0.15/百万输入或 GLM-4.5V 档），缓存与降级链（T03）由"建议"升级为"必须"；② GLM-4.6V-Flash 对"顶部固定栏遮挡"类缺陷连续三轮漏检，且以高置信度报出无证据的"对齐/间距"缺陷（典型幻觉）→ **单图整体检测路线不可靠**，EXP-04 必须实现视觉+DOM/console 双通道交叉验证与分块裁剪检测（架构决策被实测提前验证）；③ "错位"类缺陷经 v2 提示词枚举后可命中正确对象，但描述与 bbox 粗 → EXP-04 的 IoU≥0.5 验收宜降级为"区域级命中"或由 DOM 通道精化坐标；④ golden 案例必须经 ground-truth 工具核验后方可定稿（两条教训：连字符是合法断行点；过度隐藏=不可检）；⑤ 请求/解析/pydantic 校验/原始输出留存的完整链路按设计工作。
- 问题与归因：bug1 漏检 = 模型对"元素被固定栏裁切"的感知弱点 + 幻觉性高置信（类 C）；bug2 无数据 = 免费档长限流，退避重试无效（类 D：窗口超出重试上限）；案例设计两处失误 = 我的 CSS 断行规则假设错误（已修复并核验）。
- 下一步：W2/EXP-03 复现官确定性 profile（10 次一致性）；EXP-04 设计吸收结论②③（双通道+分块+区域级评分）；bug2 溢出类补测挂起至限流窗口恢复（不阻塞主线，可在 W2 初顺带补）。

### EXP-02 补测（2026-10-29，EXP-03 期间，限流窗口恢复后）

bug2（溢出类）v2 单测**命中**：symptom="文字内容（SKU编号）超出容器边界，部分信息被截断"（正确识别溢出+截断）；region=[151,102,381,262] 覆盖第一张卡片与溢出起点（真实溢出带 x≈212–850，bbox 偏保守仅含左半）；15.7s / 2369 tokens。**EXP-02 最终格局：溢出类命中、错位类部分命中、遮挡类三连漏检** → EXP-04 双通道的攻坚重点是遮挡类。免费档限流窗口实测约 1.5 小时恢复。

## EXP-03 复现官确定性 profile（2026-10-29）

- 目标/预期指标：同一仓库同一缺陷连续复现 10 次，DOM 哈希一致 + 截图 SSIM≥0.999 + 单次 ≤3 分钟（确定性是下游定位/修复/验证的地基）。
- 配置：环境=lumin / Python 3.11.14 / Playwright 1.57.0（Chromium 143 build v1200）；案例=golden-1 `#/bug1`；profile=ReproProfile 默认（1280x800、DSF=1、Asia/Shanghai、zh-CN、reduced-motion、禁动画 CSS 注入、settle 800ms、networkidle 5s 超时兜底——dev server 的 HMR websocket 会使 networkidle 不可靠，settle 时间才是真正的确定性锚点）；网络守卫=仅放行 loopback（T10 精神的先行落地）；产物=temp/exp03/run-01..10（不入库）。
- 结果（两轮，如实记录）：
  1. 第一轮 3+10 连跑"全绿"（DOM f0104ad578d3×13、SSIM=1.0）——**但为假复现**：事后发现 EXP-02 遗留孤儿 vite（PID 70680）常驻 5173，每轮新起的 vite 因 strictPort 端口冲突静默退出，就绪探测被旧服务器答到，13 次捕获全部打在旧服务器上（server 启动耗时 0.0–0.1s 即为铁证）；
  2. 修复：杀孤儿（taskkill //F //T //PID，Git Bash 下 /F 会被 MSYS 转成路径需双斜杠）+ DevServerLauncher 加双重断言（启动前端口必须空闲，停止后必须释放，否则抛错）；
  3. 第二轮真·10 连跑（每次真实重启服务器，启动 1.5s/次）：DOM sha256=d3d48e44f397 十跑一致；SSIM=1.000000×9；采集 2.2–2.5s/次、含启动约 4s/次，总 83s；ruff/mypy 绿（6 source files）。
- 结论：**达到成功目标，正收益**。产出：① 确定性管线成立，含 vite 重启不变性（deps 预打包缓存使 DOM 内 ?v=hash 跨重启稳定）；② 发现并修复"静默假复现"风险类别（端口被占→捕获旧服务器→两套内容均可自洽通过一致性检查）——比确定性本身更重要的可观测性教训，已固化为 launcher 前置/后置断言；③ Docker 沙箱按计划延至 EXP-10（golden 案例为一方可信代码，偏离已记录）。
- 问题与归因：孤儿进程来自 EXP-02 后台任务的 bash 级停止（不杀进程树）→ 教训：后台 dev server 一律经 launcher 生命周期管理；第一轮数据并非全无效（捕获管线自身确定性成立），但"服务器重启不变性"未验证——两轮已在报告中如实区分。
- 下一步：EXP-04 视觉分析官（agents/visual_analyst + models Provider 抽象；吸收 EXP-02/补测结论：遮挡类走 DOM 通道+分块检测、评分降级为区域级命中）。

## EXP-04 视觉分析官（2026-10-29）

- 目标/预期指标：视觉分析官智能体落地。原卡片验收（bbox IoU≥0.5）按 EXP-02 结论③降级为**症状级/区域级命中**；缓存命中零 API 调用；mock 单测全绿。
- 配置：模型=glm-4.6v-flash（免费档）；提示词=v3-domfacts-20261029（v2 基础上注入 fixed/sticky 覆盖层 DOM 实测事实+定向提示，版本史见 prompts.py）；输入=golden-1 三页（EXP-03 确定性采集）；架构=`models/`（BaseVLM/VLMError/extract_json_object + FileCache 内容寻址缓存 + GLMProvider 429 线性退避 + registry）+ `agents/visual_analyst`（纯函数 run + Evidence/VisualReport 证据挂接）+ reproducer 新增 `overlays.json`（DOM 通道数据源）。
- 结果：
  1. 工程验收：ruff / mypy strict（18 文件）/ pytest **8 passed** 全绿；PR CI 绿（12s，含 uv 缓存 glob 修复）；
  2. 缓存验收：单测证明同（图,提示词）二次调用 calls==1；真实运行 cache-probe `cached=True`；
  3. 真实运行（当日配额窗口仅放出 2 次成功调用，2/3 完成）：
     - **bug1 遮挡类【区域级命中——核心突破】**：region=[261,79,738,37]，symptom="顶部蓝色按钮（提交订单）部分遮挡了订单结算标题区域…覆盖痕迹"，conf 0.6。对比 EXP-02 三轮全部漏检且高置信报出幻觉缺陷，v3 的 DOM 事实把模型注意力成功引导到真实遮挡带；但因果描述偏差（称"按钮遮挡标题"，实为"导航栏遮挡按钮"，GT=[320,35,640,48]）；
     - **bug2 溢出类【命中】**：region=[151,101,386,266]，symptom="文字内容被容器截断，显示不完整"，conf 0.9（GT 溢出带 x≈212–850，区域含溢出起点）；
     - **bug3 错位类【挂起】**：免费档配额触顶（429 重试后仍拒），补测安排在配额恢复后（EXP-02 v2 已部分命中该类，预期风险低）。
- 结论：**部分达标——已跑 2/2 全部命中 + 缓存与工程验收全过；bug3 数据点挂起**。核心结论：**DOM 事实通道对遮挡类有效**（漏检+幻觉 → 区域命中+因果待精化），EXP-02 结论②的双通道路线获得正面实证；遮挡类因果归因需 DOM 通道更进一步（overlays 尚未记录"覆盖层之下被挡元素"的线索，EXP-05 定位官补齐）。
- 问题与归因：① 免费档配额窗口极小（本窗口 2 次），当日累计约 8 次成功——产品化必须配付费低价档（T03 降级链再次被验证）；② 因果偏差归因=提示词只给了覆盖层矩形，未给被覆盖内容线索（改进项已列入 EXP-05）。
- 下一步：bug3 补测（配额恢复即跑）；EXP-05 定位官（DOM↔组件↔AST 检索，行级 top-5）。

## EXP-05 定位官（2026-10-29）

- 目标/预期指标：从视觉报告+DOM 线索走到行级 top-5 代码候选；验收=golden 定位 top-5 命中真实修复行、索引构建 ≤5 分钟/仓库（EXP-05 卡片）。
- 配置：`repo/`（tree-sitter 0.26 TS/TSX 函数级切片 + CSS 规则正则切片 + BM25Okapi + bge-m3 向量通道；分词=词元+CJK 二元组）；`agents/locator/`（三路召回 RRF 融合 k=60，每候选挂 code_span 证据）；CLI `buglens index init`；embedder=bge-m3 本地（魔搭下载 2.27GB，因 transformers CVE-2025-32434 闸门拒绝在 torch<2.6 上 torch.load pytorch_model.bin，本地转换为 safetensors 后加载，sha256 前 16 位 b5e0ce3470abf5ef 已记录，文件为 BAAI 官方发布工件）；输入=真实采集（dom.html + 含 covers 的 overlays.json）+ 已存档 v3 视觉报告（bug1/2 为 EXP-04 实测，bug3 为 EXP-02 v2 记录）。
- 结果：
  1. 工程验收：ruff / mypy strict / pytest **14 passed**（含切片/分词/三 bug 定位单测）全绿；
  2. 索引：golden-1 32 切片，bge-m3 向量构建 31.5s（≤5 分钟 ✓）；
  3. 真实定位（重采含 covers 工件）：**3/3 命中且全部 top-1、三通道全亮**——bug1 top-1=index.css:41-48（含 padding-top:12px 第 45 行，即唯一修复点）；bug2 top-1=Bug2.tsx:1-23（SKU 第 9 行）；bug3 top-1=Bug3.tsx:1-38（marginTop 第 15 行）；
  4. covers 线索实采验证：bug1 的 overlays.json 结构化记录「navbar 覆盖层 covers=[button.btn-primary 文字=提交订单 rect=[345,37,590,48]]」——遮挡因果链的机器可读证据已闭环（v4 提示词的数据基础就绪）；
  5. **真实运行抓出真 bug**：identifier 通道未拆分连字符类名（spec-card vs spec/card）致 bug2 首轮漏检（单测 fixture 症状文案恰含"SKU"掩盖了该问题）→ 修复=查询侧统一 tokenize → 3/3。
- 结论：**达到成功目标，正收益**。三通道 RRF 定位在 golden-1 达到 top-1 全中；"单测过≠真实过"再次实证（fixture 过于仁慈，真实症状文案暴露缺陷）——保留教训。
- 问题与归因：① transformers CVE 闸门 × torch<2.6：embedder 兜底最初只捕 (FileNotFound/RuntimeError/ImportError/OSError) 漏了 ValueError，导致 CLI 崩溃而非降级双通道 → 已改广谱捕获（class-D 边界放宽并注明理由）；② 免费档配额当日两次尝试均 429：bug3 VLM 补测与 v4-covered 提示词真实验证顺延至配额恢复（不阻塞定位官，其输入用存档报告）。
- 下一步：配额恢复后跑 bug3 补测 + v4 因果验证（预期：模型应能说出「导航栏遮住提交订单按钮」）；EXP-06 修复工程师（planner+fixer，最小补丁）。
