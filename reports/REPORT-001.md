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
