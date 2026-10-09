---
name: pogoskill-cms-reviewer
description: 独立审查 PoGoskill 台湾站 CMS 草稿的元数据、HTML、来源覆盖和图片双格式；当前不执行 AI 页面预览，默认只读，不修改或发布。
---

# PoGoskill CMS Reviewer

独立于发布 Agent 验收草稿。先回读 `/cms/page/info`，确认站点 `324`、模板 `9916`、页面版本和正文，再执行 HTML、图片与来源覆盖的机械审查。

同时核对交稿输入：DOCX 至少提供一种参考样式（参考 URL、CMS 页面 ID 或现有 HTML）；普通新图嵌入在实际位置；Guide 图在对应位置写明含扩展名的 CMS 准确文件名。缺少参考来源、普通图位置不明，或 Guide 图经过语义猜测、相似图替换或重新上传，均不得判定通过。

## 数据与 HTML

- 核对 subject、SEO 字段、URL、作者、分类、相关文章、产品和自定义字段。
- 按 Publisher 的 [Luna HTML 固定执行契约](../pogoskill-cms-publisher/references/luna-html-contract.md) 审查正文骨架：目录必须使用 `nav-list1`，不得出现 `article-toc`；section/H2/目录锚点一一对应；普通 H3 必须使用 `h3-triangle`，FAQ 必须使用 `h3-faq faq1`；拒绝裸列表和未包入 `table-box` 的表格。普通表格必须合理宽度、居中且不滚动；只有确实过宽并标记 `data-table-layout="wide"` 的表格可使用 `overflow-auto`。
- CMS 回读后的正文不得含可见换行转义残留，例如 `` `n ``、字面 `\n`、`‘n`、`’n`、`&#96;n` 或 `&grave;n`。请求 JSON 中合法的换行编码不算问题，必须审查解码后的 `content`。
- 正文不得有 H1；目录锚点与 section ID 一一对应；标准 Buy Box 必须恰好一个。
- 最后一个结语 section 必须包含正确站点首页链接；锚文本是 DOCX 实际提供的“最佳／最好……”自然关键词，不能是 `PoGoskill`。链接后面的 `PoGoskill` 必须保持普通文字。英文结语同样使用源文的 `best ...` 关键词作为首页锚文本。
- PoGoskill 模块必须先完整写完介绍、适用情境、操作思路、作用与优势，再原样放入对应站点的 `assets/download-cta.html`；下载区必须有两个 `secure-btn` 和两个 `secure-download` 安全下载框，桌面按钮组固定居中。按钮下方必须紧接较大的现有 H3“PoGoskill 操作步驟”或英文站已验证的 `How to Use PoGoskill` 标题，随后才进入 `step-cont`。若下载区被简化、未居中、按钮过早出现或步骤标题层级错误，判定为结构不合格。FAQ 只有在 DOCX 对应答案明确介绍或推荐 PoGoskill 时才允许额外一组对应语言 CTA；繁中与英文下载资产不得混用。
- 每个 `step-cont > li` 必须以 `<p><span>步驟 N</span><label><strong>短標題：</strong>普通正文。</label></p>` 开头。`p` 只能直接包含步骤徽标和一个无 class 的 `label`；加粗标题只能位于 `label` 开头。图片盒必须是该 `<p>` 后面的同级元素。把 `strong` 或正文直接放在 `p` 下时，判定为会产生多列挤压的结构错误。
- 逐项对照 DOCX 的 Guide／操作步骤原文。允许的唯一变化是 HTML 标签和对源文已有开头短标题的 `strong` 包装；普通正文必须逐字、原序一致。新增短标题、同义改写、润色、缩写、补写、合并、拆分或重排任一项都判定为 `FAIL`。`compare-docx-to-cms-page.py` 的 `missing_step_blocks` 必须为空。
- 将同分类正常上线文章作为结构基准；拒绝基准中不存在的新文本框、提示框、卡片、彩色背景框、引用框、CSS class、局部 CSS、标题样式或下载框架。
- 每个已完成图片盒必须是 `img-wrap text-center > picture > source[type=image/webp] + img`，两者同 basename、同尺寸，fallback 为 JPG/PNG，ALT 为自然繁体中文。
- 必须取得源 `structure.json`、图片 manifest 和 `/cms/page/info` 回读，运行 `validate-image-coverage.py` 三方对账。源 DOCX 的每个图片出现位置都必须有唯一 manifest 项并在回读 HTML 中同时出现 fallback/WebP；三个数量不一致或任何缺图列表非空时直接判定 `FAIL`。重复引用不得按唯一文件名去重。
- 并排双图必须来自源 DOCX／参考样式的明确分组，使用 `row justify-content-center[data-image-layout="pair"]`，且恰好两个 `col-12 col-md-6` 子项。每项只能有一个完整 picture，图下紧跟非空说明；桌面横图最大宽度不超过 400px，竖图最大高度不超过 520px，移动端必须能上下排列。左右顺序、ALT、说明和真实画面逐项对应；不得裁切、拉伸或用自定义 CSS 修补。
- 手机截图和其他竖图必须用 `max-height` 限高并保持 `width:auto;height:auto`；英文手机截图若用固定像素 `max-width` 作为主要限制，判定为 `FAIL`。
- 图片 `data-src/data-srcset` 必须使用 `https://tw.pogoskill.com/images/` 前台地址；出现 `site.p.cms.afirstsoft.cn`、`attachment=1`、错误站点域名或哈希结尾文件名时直接判定 `FAIL`。
- 图片发布前，正确前台 URL 返回 404 只是中间状态，不得要求重复上传，但不能据此判定图片完成。必须用原图片上传响应的 `publish_id` 单独发布图片资源，并等待 fallback/WebP 前台 URL 均可读。
- 对每对图片核对 manifest、图片上传 `request_id`、图片 `publish_id`、图片发布 `request_id`、CMS 返回 URL、尺寸和文件名；确认发布接口成功 ID 完整且无失败。禁止使用页面 ID 或文章生成所得 ID。
- 任一 `IMAGE_PENDING`、本地路径、假 URL、坏图、单格式图片、尺寸不一致或标签未闭合均为发布阻断。
- 审查前先运行 Publisher 要求的 `validate-article-html.py`，并读取 DOCX/CMS 完整度比较结果；脚本失败或存在未解释缺失区块时直接判定 `FAIL`。

## 页面预览状态

当前暂不执行 AI 桌面／手机页面预览，也不要求截图或 DOM 视觉检测。不得为了预览而打开浏览器、登录 CMS、生成页面或发布。只根据 CMS API 回读、确定性 HTML 校验、图片 manifest 与来源覆盖结果作出审查结论。

## 判定

- `PASS`：数据、HTML、来源覆盖和所有图片检查全部通过。
- `PASS WITH IMAGE HOLD`：只有已知图片占位未补；仍禁止生成或发布文章页面。
- `FAIL`：存在字段、HTML、来源覆盖或图片问题。
