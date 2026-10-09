# CMS API 调用约定

所有接口统一使用 `POST https://gw.afirstsoft.com/cms/...`。JSON 请求携带 `X-API-KEY`、`Accept: application/json`、`Content-Type: application/json; charset=utf-8`；上传图片使用 `multipart/form-data`。HTTP 200 不代表业务成功，必须确认响应 `code === 0` 并记录 `request_id`。

API Key 只能由插件根目录 `scripts/CmsCredential.ps1` 的 `Get-CmsStoredApiKey` 读取。脚本优先读取 `%LOCALAPPDATA%\PoGoskillCMS\OpenAPI.v1.dat` 中经 Windows DPAPI（LocalMachine）保护且 ACL 限制为当前用户的稳定副本，并兼容 Windows Credential Manager 的 `PoGoskillCMS/OpenAPI`；插件升级不会删除该文件。禁止把密钥明文写入文章、脚本参数、JSON、日志或回复。JSON 请求优先调用插件根目录的 `scripts/cms-request.ps1`。

Windows Credential Manager 返回 `1312` 时继续检查受保护本地副本，不得直接索取 API Key。只有统一读取函数确认两个位置都没有有效凭据时，才运行 `cms-save-api-key.ps1`。保存脚本会写入受保护副本；Credential Manager 可用时再同时写入。不得自行绕过统一函数或从旧聊天内容恢复 Key。

页面正文先保存为包含真实换行的 HTML 原始字符串，再由 JSON 序列化器对 payload **只序列化一次**。JSON 文件中为表示真实换行而出现的 `\n` 是正常编码；但 `ConvertFrom-Json` 后的 `content` 中不得仍出现字面 `` `n ``、`\n`、`‘n`、`’n`、`&#96;n` 或 `&grave;n`。禁止手工替换换行、双重转义或把已经序列化的 JSON 再作为字符串序列化。`cms-request.ps1` 会在 `page/add` 和 `page/update` 前检查解码后的正文并阻断污染内容。

所有执行状态、失败重试、写请求防重复和“已上传草稿”的表述，必须同时遵守总助手的 `../../pogoskill-cms-article-assistant/references/execution-contract.md`。CMS 与现有权限默认视为可用；未经真实 POST、响应留档和规定重试，不得声称连接、读取或权限异常。

## 发现与读取

- 站点：`/cms/site/list`，例如 `{ "id": 324 }`
- 模板：`/cms/template/list`、`/cms/template/fields`
- 作者：`/cms/author/list`
- 分类：`/cms/classify/displayclassifylist`
- 产品：`/cms/product/list`、`/cms/product/info`
- 侧边栏：`/cms/module/list`，`type = 3`
- 页面：`/cms/page/list`、`/cms/page/info`
- 图片目录与文件：`/cms/picture/dirs`、`/cms/picture/list`

写入前实时确认站点、模板、作者、分类、产品、侧边栏、相关文章和目标 URL。URL 或标题命中现有页面时，只能在确认它就是当前草稿后调用更新；否则停止，不能覆盖。

## 页面新增

`POST /cms/page/add` 至少传入：

```json
{
  "template_id": 9916,
  "url": "category/article-slug.html",
  "title": "页面标题",
  "subject": "页面标题",
  "description": "Meta Description",
  "keywords": "关键词",
  "seo_keywords": "主关键词",
  "content": "完整 V2 HTML",
  "author_id": 244,
  "product_id": ["6333", "6332"],
  "classify_id": 0,
  "classify_page_id": 0,
  "sidebar_module_id": 0,
  "related_id": [],
  "fields": [],
  "page_image_url": "主图上传 URL",
  "is_recommend": 0,
  "is_hot": 0,
  "sort": 0
}
```

分类、作者、侧边栏、相关文章和模板字段 ID 必须来自本次实时查询，示例数字不能盲用。

## 页面更新

先调用 `/cms/page/info` 保存当前版本，再向 `/cms/page/update` 传入页面 `id`、当前 `version` 和完整页面字段。更新前必须确认目标仍是预期站点、模板、URL、草稿状态与未生成状态；禁止用部分字段覆盖未知页面。

## 写后回读

新增或更新成功后立即调用 `/cms/page/info`，确认：页面 ID、站点、模板、URL、作者、分类、产品、相关文章、`status = 5`、`sync_status = 1`，以及正文与本地 HTML 完全一致。绝不调用 `/cms/page/make` 或发布文章页面；`/cms/pagepublish/publish` 只允许由图片 Pipeline 使用当前 `/cms/picture/upload` 返回且有 request_id 佐证的图片 `publish_id`，用于图片资源上云。绝不调用删除接口。
