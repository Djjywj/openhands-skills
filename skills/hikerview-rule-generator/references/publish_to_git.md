# 把技能库/规则仓库推送到 Git 远端

> 场景：本 skill 的成品（`output/*.rule.json`）与技能库本身需要备份/分享到 Git 远端。
> 本文记录一套**可复用**的「生成令牌 → 建仓 → 推送 → 免密」流程，以及本机（agent 容器）实测的坑。

## 0. 先决条件（关键认知）

- **GitHub 已禁用「账号密码」做 git 认证**（2021-08-13 起）。`git push` 用密码会失败，
  必须用 **Personal Access Token (PAT)** 或 **SSH key**。同理 `curl -u user:password` 调 API 返回
  `401 Requires authentication`。
- **PAT 页面是 React 动态页**：`Generate token` 按钮在表单**最底部**，无障碍快照里要**先滚动到页面底部**
  才会出现。直接用 `curl` POST 该表单通常失败（缺 JS/CSRF/风控）。
- **无 SSH 环境**：本机若没有 `ssh` / `ssh-keygen`，且 `apt-get install` 无权限，就走 **HTTPS + PAT**，
  别在 SSH 上耗时间。
- **`gh` 的坑**：`gh auth login --with-token` 要求 token 至少含 `repo`、`read:org`、`gist`。
  只勾 `repo` 的 classic token 会报 `missing required scope 'read:org'`。
  但 **`git push` 本身只需要 `repo`** —— 所以可以**不依赖 gh**，直接用 git 凭据存储。
- **device flow（设备码）**：`POST https://github.com/login/device/code` 拿 `user_code`，
  在 `https://github.com/login/device` 输入并授权。授权确认页 `/login/device/confirmation`
  **刷新会 404**，别反复刷新；一次走完。

## 1. 推荐流程（HTTPS + classic PAT）

### ① 浏览器登录，生成 PAT

1. 浏览器打开 `https://github.com/login`，用账号登录（登录成功后直接跳到首页即成功）。
2. 打开 `https://github.com/settings/tokens/new`（Tokens classic）。
3. 填 **Note**（如 `openhands-push`）、选 **Expiration**（默认 30 天足够）。
4. 勾选 **`repo`**（推送私有/公开仓库只需它；要改 Actions workflow 再勾 `workflow`）。
5. **滚动到页面底部**，点 `Generate token`。
6. 复制形如 `ghp_xxxxxxxx` 的令牌——**只显示一次**，刷新即不可见。

> 若是首次生成后停留在 `/settings/tokens` 列表页，页面上会出现一个 `clipboard-copy` 元素，
> 其文本就是新令牌，可用浏览器快照/`get_content` 读出。

### ② 校验令牌 & 建仓（API）

```bash
export GHTOKEN='ghp_xxx'            # 仅本次会话使用，不要写进任何文件

# 校验身份
curl -sS -H "Authorization: Bearer $GHTOKEN" https://api.github.com/user \
  | python3 -c "import sys,json;print('登录身份:',json.load(sys.stdin)['login'])"

# 建私有仓库（已存在会 422，可先 GET 判断）
curl -sS -X POST https://api.github.com/user/repos \
  -H "Authorization: Bearer $GHTOKEN" -H 'Accept: application/vnd.github+json' \
  -d '{"name":"REPO_NAME","private":true,"has_wiki":false,"has_projects":false}'
```

### ③ 配置 remote 并推送

```bash
git remote add origin https://github.com/<用户名>/<仓库名>.git
# 一次性推送（内联凭据，不回写磁盘）：
git -c credential.helper='!f() { echo username=<用户名>; echo password='"$GHTOKEN"'; }; f' \
    push -u origin master
```

### ④ 配置免密（后续直接 `git push`）

```bash
git config --global credential.helper store
printf 'https://<用户名>:%s@github.com\n' "$GHTOKEN" > ~/.git-credentials
chmod 600 ~/.git-credentials
git fetch origin && echo OK    # 验证免密可用
```

> ⚠️ `~/.git-credentials` 是**明文**。若要改用系统 keyring，装 `libsecret` 后
> `git config --global credential.helper libsecret`。
> 可选：`echo "$GHTOKEN" | gh auth login --with-token`（需 token 含 `read:org`、`gist`）。

## 2. 抓取远端文件清单核对（确认推全、排除项生效）

```bash
curl -sS -H "Authorization: Bearer $GHTOKEN" \
  "https://api.github.com/repos/<用户名>/<仓库名>/git/trees/master?recursive=1" \
  | python3 -c "import sys,json;[print(t['path']) for t in json.load(sys.stdin)['tree'] if t['type']=='blob']"
```

对照本地 `git ls-files` 与 `.gitignore`，确认备份 zip / `__pycache__` 等**没有**被推上去。

## 3. 本机（agent 容器）实测结论

| 项 | 结果 |
|----|------|
| `git` | 有（`/usr/bin/git`） |
| `gh` | 有但未登录；`--with-token` 需 `read:org`+`gist` |
| `ssh` / `ssh-keygen` | **无**，`apt-get install` 无权限 → 放弃 SSH 方案 |
| 密码 Basic 认证 API | `401`（GitHub 已禁用） |
| 浏览器登录 GitHub | 可用；用户名示例 `Djjywj` |
| PAT 表单 `Generate token` | 需滚动到底部才出现；可用 |
| 网络 | github.com / gitee.com 均可达（gitee 登录需图形验证码，脚本过不去） |

## 4. 安全红线

- **聊天里发过的密码视为已泄露**：只用于一次登录，**绝不写入任何文件/仓库**；提醒用户事后改密 + 开 2FA。
- 令牌只存环境变量或 `~/.git-credentials`（600），**不要提交进 git**；`.gitignore` 里可加 `*.token`。
- 令牌有有效期（默认 30 天），到期需重新生成并更新凭据；泄漏时到
  `Settings → Developer settings → Tokens (classic)` 立即撤销。
- 仓库默认建 **private**；要公开需用户明确同意。
