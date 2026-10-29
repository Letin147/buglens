# BugLens 📷🔍

> **从一张报错截图，到一条可合并的修复 PR。**
> 证据链驱动的多模态多智能体 UI 缺陷修复系统（Evidence-Chained Multimodal Bug-Fixing Agents）

[![Status](https://img.shields.io/badge/status-W1--pending-orange)](plan/01-PLAN.md)
[![Platform](https://img.shields.io/badge/platform-CPU--only-blue)]()
[![License](https://img.shields.io/badge/license-Apache--2.0-green)]()

## 这是什么

给 BugLens 一张 UI 缺陷截图（可选：报错文本、issue 链接），它会：

1. **复现** — 在沙箱中拉起你的仓库，用 Playwright 确定性复现缺陷；
2. **定位** — VLM 视觉锁定异常区域，跨模态检索（DOM ↔ 组件树 ↔ AST）定位到代码行；
3. **修复** — 多智能体生成最小补丁；
4. **验证** — 修复循环内可执行视觉 oracle：像素 diff + 布局断言 + 既有测试（不是"LLM 觉得修好了"）；
5. **交付** — 一条带完整证据链（截图 ↔ 代码行 ↔ diff ↔ before/after GIF）的 **draft PR**（只提建议，绝不自动合并）。

## 文档地图（本项目的管理体系）

```
plan/     【计划区】01-PLAN.md 总规划·八周路线·资源·GitHub 管理    PROGRESS-001.md 进展日志(滚动)
manual/   【手册区】02-MANUAL.md 操作手册·约束·一致性              03-EXPERIMENTS.md 实验指令(vibe coding)
                    04-AGENT-PLAYBOOK.md AI Agent 工程方法论
reports/  【报告区】REPORT-001.md 实验报告(滚动，>1500 行开新卷)
docs/     【定稿区】PROJECT_BLUEPRINT.md 策划书 v1.1              DEEP_DIVE_DECISION.md 深查决策
src/ 等   【代码区】W1 按 02-MANUAL §7 建立
```

| 你想找 | 去哪里 |
|---|---|
| 行业分析 / 前景 / 增长打法 / 商业模式 | docs/PROJECT_BLUEPRINT.md |
| 竞争分析 / 空白点 / 证伪记录 | docs/DEEP_DIVE_DECISION.md |
| 八周路线 / 每次做什么 / 资源清单 | plan/01-PLAN.md |
| 约束条件 / 数据集 / 包结构 / 命名规范 / 成功指标 | manual/02-MANUAL.md |
| 实验指令（可直接粘贴给 AI） | manual/03-EXPERIMENTS.md |
| 与 Agent 协作开发的方法 | manual/04-AGENT-PLAYBOOK.md |

## 当前状态与里程碑

🚧 **W1 待启动**（2026-10-28 立项，策划与管理体系已就绪）

| 里程碑 | 内容 | 状态 |
|---|---|---|
| W1–W4 = M0 | MVP：React + Playwright + GLM-4V-Flash，golden 3/3，<¥1/案例 | 待启动 |
| W5–W8 = M1 | 证据链 PR + GitHub Action + v0.1.0 发布 | 待启动 |
| M2 | VisBugBench-Pro 基准（2027-01 前 arXiv 占坑） | 规划 |
| M3 | v1.0 发布日（MCP 形态 + 中英双语 + 集中导流） | 规划 |
| M4 | 云端 Pro（GitHub App）+ ASE 2027 / NeurIPS D&B 投稿 | 规划 |

## 约束与原则

- **CPU-only**：视觉推理走 API（GLM-4V-Flash 免费档），本地仅跑嵌入与浏览器，零 GPU 依赖；
- **单人可维护**：插件化框架适配器（React 首版，Vue/Flutter 社区贡献位）；
- **工程红线**：只提 draft PR 不自动合并；用户代码沙箱执行默认禁网；非标准仓库优雅降级；
- **干净仓库**：五分区隔离（plan/manual/reports/docs/code），中间产物只进 `temp/`（不入库）。

---

*BugLens 是一个独立的新项目，与工作区内其他项目无关。*
