# PoGoskill CMS 文章助手（独立版）

这份插件**只处理 PoGoskill 台湾繁中站与英文站**，从已经验证的 V2 HTML 规范制作文章，处理双格式图片并保存、回读 CMS 草稿。它不包含 Tenorshare 其他站点的“首次学习规范”功能，也不把两种语言的模板或产品 ID 混用。

给同事直接发[一页使用说明](START-HERE.md)。技术安装细节在[SETUP.md](SETUP.md)。

## 包含什么

- 繁中完整文章助手：`$pogoskill-cms-article-assistant`
- 英文文章助手：`$pogoskill-cms-en-publisher`
- 繁中 HTML 规范：`$pogoskill-cms-publisher`
- 图片提取、JPG/PNG + WebP、上传与图片资源发布：`$pogoskill-cms-image-pipeline`
- 草稿回读、HTML 与图片完整度检查：`$pogoskill-cms-reviewer`

所有固定下载区、Buy Box、图片盒、表格和双图组件保留在对应技能的 `assets/`；繁中与英文规范各自保留在 `references/`。普通新图必须在 DOCX 正文对应位置；Guide 图片按 DOCX 给出的 CMS 准确文件名精确复用。不能删改原文、漏图或自行创造新视觉模块。

## 安全边界

只在用户明确要求当前文章保存到 CMS 时新建或更新**该文章草稿**。新图上传后须使用该次图片上传返回的 `publish_id` 单独发布图片资源，使草稿可显示图片；这不是发布文章。默认不调用 `/cms/page/make`，不发布文章页面，不删除或修改无关旧文章。所有成功报告须有真实写入和 `page/info` 回读证据。当前不声称 AI 已完成页面视觉预览。

Windows 的完整 PoGoskill 工作流可用本包 PowerShell 和 Python 脚本执行。macOS 凭据与基础 CMS 客户端保留供检查，但 PoGoskill 图片上传脚本目前是 PowerShell/Windows 流程；未在 macOS 做端到端验证，不应宣称 macOS 可完整自动上传。

此公开仓库不包含 API Key、同事个人文章或 CMS 私有回读。API Key 保存在各自电脑的系统凭据中，插件升级不会清除它。
