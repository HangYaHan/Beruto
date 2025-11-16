# Contributing

感谢你希望为本仓库贡献代码！为保证高效、可审阅且安全的协作，请按下面的流程和规范来提交改动。此文档同时覆盖 GitHub Desktop 与命令行（CLI）两种常见方式，并提供故障排查与维护者提示。

> Talk is cheap, show me the code.
> 
> 言廉行贵，务实为先。

## 目录
- Quick Start（3 分钟上手）
- 项目分支与命名规范
- Commit 规范
- Pull Request 规范
- Code 规范
- 在 GitHub Desktop 的具体操作
- 命令行（CLI）常用命令
- 同步 fork 与解决冲突
- 认证与常见错误排查（Authentication failed）
- 检查清单（提交前）
- 附录：快捷命令参考

---

## Quick Start（3 分钟上手）
1. 在 GitHub 上 Fork 本仓库（右上角 Fork）。
2. 在 GitHub Desktop 选择 "To contribute to the parent project" 并克隆你的 fork（或命令行 clone 你的 fork）。
3. 基于上游（upstream）目标分支创建新分支，例如 `feature/xxx` 或 `fix/yyy`。
4. 本地开发并 commit。
5. Push 到你的 fork（origin），在 GitHub 上创建 PR，目标为上游仓库的目标分支（如 `b1` 或 `main`）。
6. 在 PR 中写清改动、测试方法与关联 issue（如有）。

---

## 项目分支与命名规范
- 基本原则：每次改动使用独立分支（不要直接在 `main` 或 `branches` 上开发）。
- 分支命名示例：
  - 功能：`feature/short-description`（如 `feature/backtest`）
  - 修复：`fix/issue-123` 或 `fix/nullpointer-crash`
  - 文档：`docs/update-readme`
  - 重构：`refactor/module-name`
- 不要使用长期与上游同名的分支（例如直接编辑 `branches`），以免混淆。

---

## 提交（commit）规范
- 使用简明的短标题（第一行不超过 72 字符），风格可选但统一。例如：
  - feature: add login endpoint
  - fix: prevent null pointer in parser
  - docs: update contributing guide
- 描述正文（必要时）说明为什么要做该改动以及如何测试。
- 将多个独立改动拆成多个 commit。

---

## Pull Request（PR）规范
- PR 标题：简明描述改动（对应 commit 标题可相同）。
- PR 描述模版（建议）：
  - 变更内容（What）
  - 变更原因（Why）
  - 如何测试（How to test）
  - 关联 issue（例如 `Fixes #123`）
- 在 PR 中添加 reviewer、label（如 `feature`, `bug`）、并指明是否需要回退或兼容性注意事项。
- 若需要多轮修改，请在同一 feature 分支上继续提交，PR 会自动更新。

---

# Code 规范
- src文件夹中不应该包含一个中文字符
- 对于feature分支的PR，必须提交一份包含主要函数摘要的md文件，至少包括参数，返回值和函数功能的描述

---

## 在 GitHub Desktop 的具体操作（图形界面）
1. Clone：File > Clone repository > 选择 “To contribute to the parent project” > 选择你的 fork。
   - 说明：此选项会把你的 fork 作为 `origin` 并自动添加 `upstream`（上游仓库）为远程，便于之后同步。
2. 新建分支：Branch > New Branch…，在 “Create branch based on” 选择 `upstream/b1` 或 `upstream/main`。
3. 做改动并 Commit 到分支（在左下写 commit message）。
4. Publish branch：将分支推送到 `origin`（你的 fork）。
5. 在 GitHub 网页上点击 “Compare & pull request” 创建 PR 到上游。
6. 如果需要从上游同步更新：Repository > Fetch origin，然后在分支创建、合并或 rebase。

---

## 命令行（CLI）常用命令
- 查看远程：
  - git remote -v
- 添加上游（如果没有）：
  - git remote add upstream https://github.com/owner/repo.git
- 从上游拉取最新：
  - git fetch upstream
  - git checkout b1
  - git merge upstream/b1
  - 或 rebase：git rebase upstream/b1
- 基于上游分支建新分支：
  - git fetch upstream
  - git checkout -b feat/xxx upstream/b1
- 推送到 fork 并设置跟踪：
  - git push -u origin feat/xxx

---

## 同步 fork 与解决冲突
- 推荐在开始新工作前同步 fork：
  - git fetch upstream
  - git checkout b1
  - git merge upstream/b1
  - git push origin b1
- 在 feature 分支上保持与 upstream 同步以减少冲突：
  - git fetch upstream
  - git checkout feat/xxx
  - git rebase upstream/b1
  - 解决冲突后继续 rebase（git rebase --continue），然后 git push --force-with-lease origin feat/xxx（慎用强推，仅用于你的 fork 中的 feature 分支）。

---

## 认证与常见错误排查（Authentication failed）
若在 GitHub Desktop 或 git push 时看到 “Authentication failed”：
1. 检查是否登录正确账号（GitHub Desktop：File > Options > Accounts 或 Preferences > Accounts）。
2. 确认你是向哪个远程 push：
   - git remote -v（确认 `origin` 指向你的 fork；若没有，添加 origin 指向 fork）
   - 如果你尝试 push 到 `upstream` 而你不是 collaborator，会报权限错误。正确做法是 push 到 `origin`，再发 PR 到 upstream。
3. 若使用 HTTPS：
   - GitHub 不再支持账户密码，需使用 Personal Access Token（PAT）。生成：GitHub -> Settings -> Developer settings -> Personal access tokens。
   - 在 Desktop 中登出再登录可刷新 token。
4. 若使用 SSH：
   - 确认已生成 SSH key 并把公钥添加到 GitHub（Settings -> SSH and GPG keys）。
   - 测试：ssh -T git@github.com
5. 检查仓库是否被 Archived（仓库设置会标记 Archived，禁止 push）。
6. 检查分支保护规则（Settings -> Branches），保护分支会拒绝直接 push，要求 PR。
7. 常见情形说明：
   - 如果你把贡献者设为 collaborator，他们就能直接 push（如果权限允许），这就是你曾经观察到的行为。
   - 若贡献者在 Desktop 中只看到 `upstream/main`、`upstream/b1`，很可能他们 clone 的不是自己的 fork，而是上游仓库。建议重新从 fork clone 或手动添加 `origin` 并修改 URL。

示例修复命令（若 remote 不正确）：
- 查看当前 remotes：
  - git remote -v
- 添加 origin（指向自己的 fork）：
  - git remote add origin https://github.com/YourUser/your-repo.git
- 或修改 origin：
  - git remote set-url origin https://github.com/YourUser/your-repo.git
- 推送分支到 origin：
  - git push -u origin feature/xxx

---

## 提交前检查清单
- [ ] Fork 并 clone 自己的 fork（或确认 remotes）
- [ ] 创建 feature 分支（基于 upstream 的正确分支）
- [ ] 本地测试通过且 lint 无错误
- [ ] Commit message 清晰、可读
- [ ] Push 到 origin（你的 fork），在 GitHub 上创建 PR
- [ ] PR 描述包含变更、测试步骤和关联 issue（如有）

---

## 附录：快捷命令参考
- git remote -v
- git remote add upstream https://github.com/owner/repo.git
- git fetch upstream
- git checkout -b feat/xxx upstream/b1
- git push -u origin feat/xxx
- ssh -T git@github.com
- git push --force-with-lease origin feat/xxx  # 仅在确认的情况下使用
