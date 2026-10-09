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
3. 从当前插件根目录运行 `scripts/cms-check-api-key.ps1`。已有 Key 则直接继续，不要重复索取。只有确实无 Key，才运行不带 `-Prompt` 的 `scripts/cms-save-api-key.ps1`，将**同一个等待 Enter 的进程**打开到用户可见终端。用户复制 Key 后只按 Enter；待进程退出，再运行检查脚本。不要把 Key 放在聊天、命令参数、日志或仓库中。
4. 在 Windows 使用可用 Python 运行 `scripts/verify-workstation.py`（缺少 PATH 中的 PowerShell 时给它传当前机器真实 `--powershell` 路径），实际检查已保存 Key、`/cms/site/list` 的只读 POST 与 WebP 编码能力。对插件 `scripts/test_*.py` 运行单元测试，再验证两种语言的 `validate-article-html.py` 及资产文件都可读取。检查失败必须具体报告，不能把安装称为完成。

Windows 稳定 Key 存储位于当前用户的 `%LOCALAPPDATA%\PoGoskillCMS\OpenAPI.v1.dat`，并兼容 Credential Manager；替换插件不会删除它。macOS Keychain 客户端保留用于凭据和 API 检查，但 PoGoskill 图片流水线的完整自动化尚未做 macOS 端到端验证，遇到 macOS 不要承诺完整上传。

## 运行边界

繁中使用 `$pogoskill-cms-article-assistant`，英文使用 `$pogoskill-cms-en-publisher`。完整规则在各技能的 `SKILL.md`、`references/` 和 `assets/`。文章默认只存草稿；图片上传后使用图片上传响应的 `publish_id` 单独发布图片资源。没有用户对当前文章的明确上传要求时只读 CMS 和制作本地 HTML；不生成、不发布文章页面，不删除、修改不相关的旧文章。
