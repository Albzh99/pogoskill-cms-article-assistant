# 给 PoGoskill 同事：三步开始

想要 Word 版逐步说明，可下载 [PoGoskill 文章助手同事使用指南](docs/PoGoskill%20文章助手同事使用指南.docx)。

1. 向 CMS 管理员取得你有权限使用的 Open API Key。**不要发到 AI 聊天或 GitHub。**如果电脑以前已经保存过 Key，先让 AI 检查，不要重新索取。
2. 把下面整段发给 Codex AI，让它自己安装、检查和打开终端；你不用输入命令：

   > 请从公开仓库 https://github.com/Albzh99/pogoskill-cms-article-assistant 安装 PoGoskill 独立文章助手，按仓库 `SETUP.md` 自己操作。先检查本机旧 PoGoskill 插件与已保存的 CMS Key；只替换冲突的旧 PoGoskill 插件，不删除 Key，也不要安装 Tenorshare 其他站点学习包。Key 已可用就不要再问。若确实没有 Key，请把等待我按 Enter 的同一个终端真正打开给我看；我只会复制 Key 到剪贴板，再回到终端按 Enter，不会粘贴或手输命令。安装后实际运行本机检查与测试；需要新对话加载插件时告诉我。

3. 上传一篇有参考样式的 DOCX，选择下面其中一句发送：

   **繁中站**：

   > 使用 `$pogoskill-cms-article-assistant` 完整处理这篇 PoGoskill 繁中 DOCX。按台湾站 V2 规范保留全部文字、表格、FAQ 与图片；Guide 图只按文档中的准确文件名从 CMS 查找。新图保留原图并生成同名 WebP，上传并单独发布图片资源。通过校验后保存为 CMS 草稿，立即回读核对。不要生成或发布文章页面，不要修改无关旧文章。

   **英文站**：

   > 使用 `$pogoskill-cms-en-publisher` 完整处理这篇 PoGoskill 英文 DOCX。用中文汇报，但文章正文保持英文；严格复用英文站 V2 模板、下载区和 Buy Box，保留全部文字与图片。Guide 图只按文档中的准确文件名从 CMS 查找；新图原图与同名 WebP 成对上传并单独发布图片资源。通过校验后保存为 CMS 草稿，立即回读核对。不要生成或发布文章页面，不要修改无关旧文章。

DOCX 必须提供参考文章 URL、CMS 页面 ID 或旧 HTML 中至少一种；要新上传的图片应嵌在文章里实际出现的位置。完成时 AI 必须给你页面 ID、草稿状态、写入和回读 `request_id`，并说明文字和图片是否齐全。只有“正在处理”或“已生成本地 HTML”不算上传成功。
