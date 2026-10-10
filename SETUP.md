# PoGoskill 独立插件安装（供 AI 执行）

本仓库的 Marketplace 名称是 `pogoskill-only`，插件名称是 `pogoskill-cms-assistant`。这是**PoGoskill 专用包**；不要把原 Tenorshare 多站点包里的 `cms-site-standard-builder` 或 `tenorshare-cms-article-assistant` 复制进来。操作前先读[同事说明](START-HERE.md)。

## 安装或替换旧版

1. 检查本机 Codex CLI 和 `codex plugin list`。如果已经安装 `pogoskill-cms-assistant@pogoskill-team` 且用户要求用本独立版替换，才运行 `codex plugin remove pogoskill-cms-assistant@pogoskill-team`；**不要**删除整个旧 Marketplace、其他插件或系统凭据。若同时存在同名插件，先解决冲突，不要声称安装成功。
2. AI 执行：

   ```text
   codex plugin marketplace add "https://github.com/Albzh99/pogoskill-cms-article-assistant.git" --ref main
   codex plugin add pogoskill-cms-assistant@pogoskill-only
   ```

   已安装本独立版时，先 `codex plugin marketplace upgrade pogoskill-only`，再执行 `codex plugin add pogoskill-cms-assistant@pogoskill-only`。插件根目录从当前安装结果动态取得，禁止使用旧消息中带版本号的缓存路径。新建 Codex 对话后加载新版技能。
3. **先判断操作系统，绝不能在 Mac 运行 `.ps1`、`pwsh`、`.exe` 或引用 Windows 缓存路径。** Windows 从当前插件根目录运行 `scripts/cms-check-api-key.ps1`；Mac 运行 `python3 scripts/cms-macos.py check-key`。已有 Key 直接继续。只有确实无 Key，Windows 才运行 `cms-save-api-key.ps1`，Mac 则运行 `python3 scripts/cms-macos.py save-key`。把**同一个等待 Enter 的进程**打开到用户可见终端；用户复制 Key 后只按 Enter。进程退出后用对应平台的 `check-key` 检查，不在聊天、参数、日志或仓库中放 Key。
4. Windows 和 Mac 都运行本机 Python 的 `scripts/verify-workstation.py`，检查凭据、`/cms/site/list` 只读 POST 与 WebP 编码能力；Windows 缺少 PATH 中的 PowerShell 时才传真实 `--powershell` 路径。Mac 若缺 Pillow/WebP，由 AI 在当前用户目录建立 Python 虚拟环境、安装 Pillow，并在此后所有 Mac 脚本调用中持续使用该虚拟环境的 Python；不要要求同事手工运行命令，也不要把包装进插件仓库。对插件 `scripts/test_*.py` 运行单元测试，验证两种语言的 `validate-article-html.py` 及资产文件可读。检查失败具体报告，不得称安装完成。

Windows 稳定 Key 存储位于当前用户的 `%LOCALAPPDATA%\PoGoskillCMS\OpenAPI.v1.dat`，并兼容 Credential Manager；Mac 存在当前用户 Keychain。替换插件不应删除任一凭据。Mac 图片转换、成对上传、图片资源发布与 HTML 回填使用 `scripts/cms-macos-image-pipeline.py`；Mac CMS JSON 请求使用 `scripts/cms-macos.py request`。请先用本机自检，未经过真实 Mac 端到端执行时不得声称该机已验证成功。

## 运行边界

繁中使用 `$pogoskill-cms-article-assistant`，英文使用 `$pogoskill-cms-en-publisher`。完整规则在各技能的 `SKILL.md`、`references/` 和 `assets/`。文章默认只存草稿；图片上传后使用图片上传响应的 `publish_id` 单独发布图片资源。没有用户对当前文章的明确上传要求时只读 CMS 和制作本地 HTML；不生成、不发布文章页面，不删除、修改不相关的旧文章。
