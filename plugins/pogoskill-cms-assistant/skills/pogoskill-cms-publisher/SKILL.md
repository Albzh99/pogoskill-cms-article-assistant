---
name: pogoskill-cms-publisher
description: 将 PoGoskill 台湾站 SEO 文稿转换为文章内容页面模板-v2 的可读 HTML，并在明确授权后创建或更新 CMS 草稿。适用于文章 HTML 制作与 CMS 草稿上传，不用于直接发布。
---

# PoGoskill CMS Publisher

为 PoGoskill 台湾站制作文章，并把经过校验的内容保存为 CMS 草稿。

## 输入契约

- DOCX 必须提供参考文章 URL、CMS 页面 ID 或现有 HTML中的至少一项。先读取并记录参考来源，再复用其现有结构；没有参考样式时不得自行设计新模块。
- 需要上传的普通正文图必须直接嵌入 DOCX 的实际出现位置。只给路径、文件夹或无位置说明的附件不能用于自动回填。
- Guide 图无需嵌入；DOCX 必须在对应步骤或段落写出 CMS `guides` 中的准确文件名（含扩展名）。只按该名称精确检索并复用，不按语义猜图、不换相似图、不重新上传 Guide 图。

开始前读取总助手的 [CMS 真实执行与证据契约](../pogoskill-cms-article-assistant/references/execution-contract.md)、[references/cms-live-contract.md](references/cms-live-contract.md) 和 [references/cms-api-contract.md](references/cms-api-contract.md)。制作或修改正文 HTML 时，必须先完整读取 [Luna HTML 固定执行契约](references/luna-html-contract.md) 和 [两篇旧文章的结构参考结论](references/legacy-article-patterns.md)，逐模块复制当前 V2 结构；单图位置使用 [assets/image-box.html](assets/image-box.html)，源稿／参考样式明确要求并排双图时使用 [assets/paired-image-box.html](assets/paired-image-box.html)，普通表格使用 [assets/responsive-table.html](assets/responsive-table.html)，确实过宽的表格才使用 [assets/wide-table.html](assets/wide-table.html)，正文下载区原样使用 [assets/download-cta.html](assets/download-cta.html)，正文结尾原样使用 [assets/buybox.html](assets/buybox.html)。不得靠记忆重写图片、表格、下载区或 Buy Box，也不得复制旧文章的自定义 CSS 或专属 class。

## 授权和安全

- API Key 只从安全环境变量或会话 Secret 读取，不写入 HTML、文件、日志或回复。
- 默认允许只读查询和本地 HTML 转换。创建或更新 CMS 草稿前，确认用户已明确要求该篇文章写入 CMS。
- 绝不执行 `/cms/page/make`，也绝不把页面 ID 或文章生成所得 ID 传给 `/cms/pagepublish/publish`。图片 Pipeline 必须把当前图片上传响应中的 `publish_id` 传给该接口，以单独发布图片资源；这不等于发布文章。
- 不删除文章、图片、文件或目录，不覆盖无法确认归属的页面。

## 写入前发现

实时查询 CMS，不依赖猜测或示例 ID：

1. 用站点列表确认台湾站仍为目标站点。
2. 用页面列表按 URL 与标题查重；命中时选择更新，不重复创建。
3. 查询文章 V2 模板及其自定义字段。
4. 查询并确认作者、分类页、产品和相关文章；相关文章必须存在且属于正确站点。产品必须通过 `/cms/product/list` 与 `/cms/product/info` 实时核验，并严格写成 `"product_id": ["6333", "6332"]`，即 PoGoskill/Windows 与 PoGoskill(Mac)/Mac；`7925`、`7926` 是下载 PID，不得写进 `product_id`。
5. 读取同类近期已发布文章，选择符合当前站点的 HTML 组件。

任何关键字段无法确认时，停止在 CMS 写入前并报告缺失项。

## HTML 转换

- 使用繁体中文和台湾用语，保持 `PoGoskill` 大小写。
- 正文不写 `<h1>`；H1 由 CMS `subject` 和模板渲染。
- 输出按标签和逻辑区块换行、缩进，确保人工可读；禁止把 HTML 压成一整行。
- 保持正确 heading hierarchy，使用带稳定 `id` 的 `<section>` 与目录锚点。
- 写 HTML 前先列出章节大纲：每个 H2 对应一个目录项；H3 只用于真正的子主题，且后面必须有完整段落、列表或表格。禁止连续 H3、把单个步骤做成 H3，或为了视觉效果拆出大量小标题。
- 参考模板文章 `240801` 学习可用组件，并优先读取同分类近期已上线文章作为实际结构基准。只复用基准中确实存在且适合当前内容的目录、列表、表格、步骤、图片、视频、FAQ、下载模块和产品模块。
- 禁止自行新增文本框、提示框、卡片、彩色背景框、引用框、CSS class、内联/页面 CSS 或新的 HTML 层级；不得因为内容重要或希望页面更丰富而创造视觉模块。
- 保持所选参考文章的标题、正文、段落间距、按钮、下载框架及模块结构；内容无法自然放入现有组件时，使用普通段落、H2/H3、列表或表格，或停止并报告模板缺口。
- 普通表格复制 `assets/responsive-table.html`，按内容使用合理宽度并居中，默认约为正文的 90%，不强制铺满正文，也不启用横向滚动。只有实际内容过长、在正文宽度内必然明显挤压时才复制 `assets/wide-table.html`，标记 `data-table-layout="wide"` 并在移动端横向滚动；列数本身不构成启用滚动的理由。两类表格都使用自动列宽、居中文字，禁止固定窄列。图片使用站点现有 `picture`、lazy-load 与 `img-wrap` 规则。
- 当源 DOCX 或参考文章明确显示两图并排且图下有说明时，保留左右顺序并套用 `assets/paired-image-box.html`。必须恰好两个 `col-12 col-md-6` 子项，每项含完整 WebP/fallback `picture` 和紧随其后的说明段落；桌面单图最大显示宽度不得超过 400px，移动端由 `col-12` 自动上下排列。不得用固定总宽度、绝对定位或自定义 CSS 强行并排。
- 每篇文章正文最后必须且只能出现一个标准 Buy Box，使用资产文件中的完整 HTML，不自行简化或重设计。
- 结语最后一次导向首页时，必须把 DOCX 实际提供的自然关键词短语设为链接锚文本，例如“最佳皮克敏種花助手”“最佳寶可夢飛人工具”或“最佳自動種花助手”；紧随其后的品牌名 `PoGoskill` 保持为普通文字。禁止把 `PoGoskill` 本身设为结语首页链接，也不得自行发明文稿中没有的关键词。

## 版式复用规则

- PoGoskill 主介绍模块的桌面下载 CTA 只放一组，并必须逐字复制 `assets/download-cta.html`。完整结构必须含 `dev-desktop > btn-groups > 两个 secure-btn`，每个按钮下保留 `secure-download` 安全下载框；桌面按钮组固定居中，缺任一层都禁止上传。必须先写完 PoGoskill 的介绍、适用情境、操作思路、作用与优势，再放下载 CTA；不得在第一段介绍后立刻插入按钮。若 DOCX 的某个 FAQ 答案明确介绍或推荐 PoGoskill，可在该答案后额外复制一组繁中 CTA；没有明确推荐则不放。
- PoGoskill 模块固定顺序为“完整介绍与优势文字 → 下载 CTA → 较大的现有 H3『PoGoskill 操作步驟』→ `step-cont` 步骤”。操作步骤标题不得做成普通 `section-label`、H4 或自创标题样式，必须使用 `h3-triangle` 或同分类已验证等价组件；单独的每个步骤不再使用 H3。
- `step-cont` 每一步固定为 `<li><p><span>步驟 N</span><label><strong>步驟短標題：</strong>完整說明。</label></p>圖片盒</li>`。`label` 必须无 class，并把加粗短标题和普通正文完整包在一起；`strong` 不能直接成为 `p` 的子元素，否则站点的横向步骤布局会把标题和正文拆成多列，造成逐字换行。图片盒必须放在该 `<p>` 之后，不能塞进段落。
- Guide／操作步骤只允许改变 HTML 包装，不允许改变 DOCX 文字。`strong` 只能包住源文开头已经存在的短标题或冒号前原文；其后的说明必须逐字保留原顺序。禁止为了套格式自行概括标题、改写、润色、缩写、扩写、合并、拆分或重排任何步骤文字。源文没有独立短标题时，整段放入 `label` 且不加 `strong`，不得编造标题。
- FAQ 默认不放下载 CTA。只有某个问答的源文确实解释并推荐 PoGoskill 时，才可在该答案之后额外放一组繁中 CTA；不得因为文章关联产品而自动加入，也不得误用英文 CTA。
- 标准 Buy Box 内部自带的 `dev-desktop` / `dev-mobile` 属于产品组件，不计入正文下载 CTA 数量，也不得删改。
- 同一章节出现多个并列对象时，不要为每个对象创建 H3。优先使用参考文章已有的列表或表格；只有参考文章存在对应卡片组件时才能原样复用，H3 只表示真正的逻辑子章节。
- 文章底部、相关文章上方的面包屑使用 V2 模板的 `.content-navlinks`；其中 `.tit` 包含“主頁 → 分类”，当前文章标题是父级下的 `a.text-primary`。必须让父级纵向排列、`.tit` 可换行、当前标题独占一行。
- 正文中不重复创建面包屑，也不新增局部 CSS 修补。必须复用已验证正常的 V2 `.content-navlinks` 结构与 class；若仍挤压、覆盖或横向溢出，退回修改 HTML 结构或报告模板问题，不自行改样式。

## 图片规则

- PoGoskill 下载、安装、操作步骤与产品界面图只按 DOCX 对应位置写明的准确图片名称调用 `/cms/picture/list` 检索 `guides`。必须找到该名称对应的 fallback 原图与同名 WebP 后原位回填；缺失、重名或无法唯一确认时停止并报告，不自行猜图、换相似图或上传 Guide 图。
- 用户为 Pokémon GO 或 Pikmin Bloom 正文配好的图片优先作为新图上传，不用图库中的相似图片替换；上传前仍须检查同名冲突与完全重复文件，避免覆盖或重复上传。
- 有真实 JPG/PNG 素材且用户已授权当前文章写入时，调用 `$pogoskill-cms-image-pipeline` 提取、生成同名 WebP、成对上传并回填。
- 游戏内容图按产品进入 `pokemon-ios` 或 `pikmin`；PoGoskill 下载、安装、操作步骤和产品界面进入 `guides`，即使文章主题属于游戏也不改变。
- 下载/使用步骤图必须逐步理解文字操作，再从 `guides` 中匹配对应界面；步骤文字与图片功能必须一一对应。
- 主图必须为 850×460。横图适配正文宽度；手机截图等竖图保持比例并限制宽高，避免占据整个屏幕。
- ALT 描述图片真实内容，使用自然繁体中文并适度包含主题词；不同图片不得机械重复文章标题。
- 正文图片只使用繁中前台公开地址 `https://tw.pogoskill.com/images/<folder>/<semantic-name>.<ext>?w=<w>&h=<h>`。CMS 返回的 `site.p.cms.afirstsoft.cn`、`attachment=1` 或其他后台 `upload` 地址只作上传证据，禁止写进 HTML；文件名禁止追加 SHA/随机哈希。
- 新图片尚未发布时，正确前台 URL 返回 404 是正常的中间状态，不得重复上传。必须从原始图片上传 manifest/响应恢复该图片的 `publish_id`，先由图片 Pipeline 单独发布图片资源，等待 fallback/WebP 前台 URL 均可读后，才回填并保存或更新 CMS 草稿。`/cms/picture/list` 不能替代图片上传 `publish_id` 证据。
- 需要图片但资源尚未提供时，保留 `img-wrap`，并在 `IMAGE_PENDING` 中填写唯一 `image-key`、用途、繁体中文 ALT、建议尺寸与双格式要求。
- 不伪造 URL、文件名、尺寸、WebP 版本或上传成功状态；不上传 DOCX 中未被正文引用的媒体。
- 任何 `IMAGE_PENDING` 都是硬性发布阻断：可以在授权后保存草稿，但禁止 make 和 publish。

## CMS 草稿流程

获得该篇文章的明确写入授权后：

1. 组装 V2 页面字段，包括 `subject`、`title`、`description`、`keywords`、`seo_keywords`、`url`、`author_id`、`classify_page_id`、`related_id`、`fields` 与格式化 `content`。
2. URL 必须为小写 `.html` 相对路径，并已通过 CMS 查重。
3. 新建使用 `/cms/page/add`；已存在页面使用 `/cms/page/update`，更新前先读回当前版本。
   用户明确要求修改某个现有草稿时，先以页面 ID/URL 回读确认目标，再直接更新该草稿；若图片已上传但前台 URL 为 404，先用原图片上传 `publish_id` 发布图片资源，确认上云后再更新原草稿。不得改为新增页面或重复上传图片。
4. 保存前运行插件根目录 `scripts/validate-image-coverage.py`，把 DOCX structure、图片 manifest 与最终 HTML 三方对账；只有源图片出现次数、manifest 项数、HTML 回填数完全一致且 `pass: true` 才允许写入。保存后立即调用 `/cms/page/info` 回读，对回读 JSON 再运行同一图片完整度校验，并逐项比对元数据、正文、图片盒和 Buy Box；随后运行 `scripts/assert-cms-page-products.ps1 -ResponsePath <page-info-response.json>`，确认产品严格回读为 `6333`、`6332`。少一张图片或任一格式 URL 即阻断完成。
5. 将页面 ID、草稿状态、回读结果、待补图片和所有 `request_id` 交给审查 Agent。

上传前必须运行插件根目录 `scripts/validate-article-html.py <html-path> --assets-dir <publisher-assets-dir>`；返回非零时禁止调用写接口。写入后运行 `compare-docx-to-cms-page.py` 并检查缺失区块，不能只比较标题或开头几段。该比较器会把 DOCX 的步骤正文作为逐字保留门槛；`missing_step_blocks` 非空或脚本非零时必须修复草稿，不得解释为“只是润色”。

## 完成条件

只有完整正文、所有要求图片、元数据、产品 `6333`/`6332`、草稿写入和 `/cms/page/info` 回读均成功才报告 `Draft ready for review`。最终回复必须给出页面 ID、草稿状态、校验结果和回读 `request_id`；拿不到这些证据时不得说“已上传”或“正在上传”。存在图片占位时明确报告 `Image hold`，绝不报告已发布。
