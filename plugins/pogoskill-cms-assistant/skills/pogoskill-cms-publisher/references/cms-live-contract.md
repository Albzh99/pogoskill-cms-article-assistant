# PoGoskill 台湾站 CMS 实测约定

核验日期：2026-09-20。调用前仍需以实时 API 响应为准。

## 已确认对象

- 生产网关：`https://gw.afirstsoft.com`
- 台湾站：`site_id = 324`，`site_name = pogoskilltw`，`url = https://tw.pogoskill.com`
- 图片根目录：`pogoskilltw_images`
- 主要文章模板：`template_id = 9916`，名称“文章内容页面模板-v2”，类型 `3`
- 组件示范页：`page_id = 240801`，状态 `5`，只供学习，禁止覆盖或删除
- 近期 V2 已发布页面约 531 篇；抽查 10 篇均能通过 `/cms/page/info` 读取完整 HTML，且每篇有一个 Buy Box
- 当前常用作者实例：`author_id = 244`，黃韋樂；使用前重新查询 `/cms/author/list`
- 文章产品固定使用 CMS 主键 `6333`（PoGoskill / Windows）与 `6332`（PoGoskill(Mac) / Mac），写入格式必须是 `"product_id": ["6333", "6332"]`。
- `7925` 与 `7926` 是这两个产品的 DCC 下载 PID，不是 CMS `product_id`，禁止写进文章产品字段。
- 2026-09-29 实时核验：产品列表 request `537129b5-4ce7-4642-8d0b-7ace45422126`；产品 6333 详情 request `10613565-a4c8-450a-84c6-73b829570076`；产品 6332 详情 request `58ade540-445d-42a3-b749-3719f6e66cf5`。

## V2 自定义字段

通过 `/cms/template/fields` 实时确认。2026-09-20 返回：

- `author_cont`：作者模块，editor
- `css`：页面 CSS，editor
- `application`：结构化数据，editor
- `adsense_show`：AdSense 开关

不要把 `page/info` 中 fields 数组的中文 `name` 当作写入 key；写入使用模板接口返回的 `field_key`。

## 分类与关联

- V2 实际文章常以 `classify_page_id` 表示分类聚合页，`classify_id` 可能为 `null`。
- 从 `/cms/classify/displayclassifylist` 取得 `id` 与 `classify_id`，不要互换。
- `related_id` 是页面 ID 数组。写入前用 `/cms/page/list` 按 IDs 回查标题、URL、站点和状态。

## 已验证读取接口

- `/cms/site/list`
- `/cms/picture/dirs`
- `/cms/file/list`
- `/cms/template/list`
- `/cms/template/fields`
- `/cms/module/list`
- `/cms/product/list`、`/cms/product/info`
- `/cms/page/list`、`/cms/page/info`
- `/cms/search/index`
- `/cms/author/list`，可用 `id` 参数取得单一作者资料
- `/cms/classify/displayclassifylist`

## 当前接口限制

- 图片处理已恢复，但仅处理用户提供且能确认属于当前文章的真实 JPG/PNG；双格式流程见同级 `../../pogoskill-cms-image-pipeline/SKILL.md`。
- `/cms/picture/dirs` 已于 2026-09-20 再次实测成功；台湾站根目录返回 23 个子目录。
- `/cms/picture/list` 已上线且当前 API Key 已获授权。2026-09-20 实测可读取 `pokemon-ios` 中的 PNG/WebP 文件明细、尺寸与线上 URL；图片上传后必须回查。
- `/cms/author/info` 与 `/cms/author/select` 未上线；使用 `/cms/author/list`。
- `/cms/sidebar/*`、`/cms/module/info` 与侧边栏别名未上线；可用 `/cms/module/list` 搭配 `type = 3` 读取侧边栏元数据，但无法读取其完整 HTML。

## 写接口边界

以下路由已通过缺少必填参数的无副作用请求确认可访问，但未执行实际写入：

- `/cms/picture/upload`
- `/cms/file/createdir`
- `/cms/file/upload`
- `/cms/page/add`
- `/cms/page/update`
- `/cms/page/make`
- `/cms/pagepublish/publish`

HTTP 200 不等于成功；必须验证响应 `code === 0`，批量发布还要确认 `data.failed` 为空，并保留 `request_id`。
