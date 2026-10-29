# BugLens 推送前脱敏与放行清单（PRE_PUSH_CHECKLIST）

> **用途**：任何 `git push` 到公开远程仓库之前，逐项打勾（02-MANUAL §2.4 E06 强制）。当前仓库尚无远程——首次推送前必须完整执行一遍。

## A. 脱敏（不可跳过）

- [ ] **密钥历史扫描**：`git log -p --all | grep -c "<密钥前8位>"` 输出必须为 `0`（2026-10-29 审计基准：已为 0）；
- [ ] **入库文件白名单**：`git ls-files` 中不得出现 `.env`、`1.txt`、`temp/`、`node_modules/`、`dist/`、截图原图（>500KB 媒体走 release 附件）；
- [ ] **个人信息扫描**：`git grep -nE "1[3-9][0-9]{9}|身份证|学号"` 无命中；文档中无手机号/住址/证件号；
- [ ] **提交作者邮箱决策**（需项目所有者拍板）：当前为个人 QQ 邮箱，推送后永久公开于提交历史。二选一：
  - 保留（个人仓库常见做法）；
  - 改用 GitHub noreply：`git config user.email "<数字ID>+<用户名>@users.noreply.github.com"`，然后趁无远程重写 8 个提交的作者：
    `git rebase -r --root --exec "git commit --amend --reset-author --no-edit" --no-verify`（仅未推送时安全，推送后禁做）。

## B. 质量放行

- [ ] `make check` 三绿（ruff / mypy strict / pytest）；
- [ ] 推送后 CI 首跑为绿（`.github/workflows/ci.yml`）；
- [ ] README 的状态徽章与里程碑表和 PROGRESS 一致；
- [ ] `git status` 干净、REPORT/PROGRESS 编号连续、无游离文件。

## C. 语义（防幻觉）

- [ ] 最新 EXP 记录中的验收数字与测试原始输出一致（对照 pytest 控制台，不凭记忆誊写）；
- [ ] 对外文档表述过 N01–N04 红线自查（02-MANUAL §2.3）；
- [ ] 引用的关键外部数字（论文指标/竞品 star）在首次使用时已回源核验（EXP-00 与 2026-10-29 审计已核 GUIRepair 175、ReBug 49.96%）。

---

*2026-10-29 首次全库审计记录：A1=0 ✓、A2 白名单 33 文件 ✓、A4 待所有者决策、B 全绿 ✓、C 双引用回源属实 ✓。详见 plan/PROGRESS-001.md 卡片 #006。*
