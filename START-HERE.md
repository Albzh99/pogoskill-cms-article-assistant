# 给 PoGoskill 同事：三步开始

想要 Word 版逐步说明，可下载 [PoGoskill 文章助手同事使用指南](docs/PoGoskill%20文章助手同事使用指南.docx)。

1. 向 CMS 管理员取得你有权限使用的 Open API Key。**不要发到 AI 聊天或 GitHub。**如果电脑以前已经保存过 Key，先让 AI 检查，不要重新索取。
2. 把下面整段发给 Codex AI，让它自己安装、检查和打开终端；你不用输入命令：

   > 请从公开仓库 https://github.com/Albzh99/pogoskill-cms-article-assistant 安装或更新 PoGoskill 独立文章助手，按仓库 `SETUP.md` 自己操作。先检查本机旧 PoGoskill 插件与已保存的 CMS Key；只替换冲突的旧 PoGoskill 插件，不删除 Key，也不要安装 Tenorshare 其他站点学习包。Key 已可用就不要再问。若确实没有 Key，Mac 上必须由你运行当前插件的 `cms-macos.py open-save-key-terminal`，打开独立的 macOS Terminal.app，并确认窗口内脚本已启动；不可以打开 Codex 内置终端面板代替。我只会复制 Key 到剪贴板，再回到那个系统 Terminal 窗口按 Enter，不会粘贴或手输命令。安装后实际运行本机检查与只读 CMS `site/list`，若返回 403，请给出脱敏的接口路径、状态、响应 `code`、`msg` 和 `request_id`，不要直接断言 Key 没权限或反复索要。需要新对话加载插件时告诉我。

   Mac 用户也发同一句。助手必须自动识别 macOS，使用 Python＋Keychain；Windows 才使用 PowerShell。Mac 上若出现“运行 `.ps1` / `pwsh` / `.exe`”或让你在 Codex 面板里按 Enter，说明仍在使用旧流程，先按 `SETUP.md` 更新并新建对话，不要继续旧会话。

   **Mac 显示已保存，但 Codex 说找不到 Key？** 不要重新复制，也不要把 Key 发给 AI。让 AI 更新本插件，再用当前插件运行 `check-key` 和只读 `/cms/site/list`。旧 Keychain 接口若返回 `status=-50`，新版会尝试系统 `security` 读取；两个方式都失败时，让 AI 报告脱敏状态码并停止，不能说你“没填 Key”。可直接发：“系统 Terminal 已显示保存并验证成功。请更新 PoGoskill 助手并检查当前插件的 Keychain 与只读 CMS 连接；不要让我重填 Key，只报告脱敏错误。”

3. 上传一篇完整 DOCX，选择下面其中一句发送。PoGoskill 的繁中和英文 V2 规范已内置，不需要提供旧文章 URL、CMS 页面 ID、CSS 或 HTML：

   **繁中站**：

   > 使用 `$pogoskill-cms-article-assistant` 完整处理这篇 PoGoskill 繁中 DOCX。按台湾站 V2 规范保留全部文字、表格、FAQ 与图片；Guide 图只按文档中的准确文件名从 CMS 查找。新图保留原图并生成同名 WebP，上传并单独发布图片资源。通过校验后保存为 CMS 草稿，立即回读核对。不要生成或发布文章页面，不要修改无关旧文章。

   **英文站**：

   > 使用 `$pogoskill-cms-en-publisher` 完整处理这篇 PoGoskill 英文 DOCX。用中文汇报，但文章正文保持英文；严格复用英文站 V2 模板、下载区和 Buy Box，保留全部文字与图片。Guide 图只按文档中的准确文件名从 CMS 查找；新图原图与同名 WebP 成对上传并单独发布图片资源。通过校验后保存为 CMS 草稿，立即回读核对。不要生成或发布文章页面，不要修改无关旧文章。

要新上传的图片应嵌在 DOCX 中实际出现的位置；Guide 图按文档标注的准确 CMS 文件名查库。完成时 AI 必须给你页面 ID、草稿状态、写入和回读 `request_id`，并说明文字和图片是否齐全。只有“正在处理”或“已生成本地 HTML”不算上传成功。
