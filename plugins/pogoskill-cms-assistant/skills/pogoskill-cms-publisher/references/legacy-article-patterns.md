# 两篇旧文章的结构参考结论

本参考从“皮克敏稀有森林饰品”和“圆陆鲨／烈咬陆鲨”旧 HTML 中提取可复用手法。旧代码本身不是模板；只学习内容组织，不复制其中的技术债。

## 可以复用的手法

- 导语之后放主图，再进入单层 `ul.list-filled-dot.nav-list1` 目录。
- 每个目录项对应一个 `section#partN` 和该 section 的首个 H2。
- 一个 H2 下有多个真正独立的解释主题时，使用 `h3.h3-triangle`；每个 H3 后必须有完整正文、列表、表格或图片，不能只当视觉标签。
- 活动时间、坐标、技能、属性或多对象比较适合表格。普通表格使用当前标准 `div.table-box > table` 并合理居中；只有实际文字过长、在正文宽度内确实会挤压时才使用 `div.table-box.overflow-auto > table[data-table-layout="wide"]`，不能仅因列数多或横向排列就启用滚动。
- PoGoskill 章节先说明读者问题、产品作用和优势，再放标准下载区，然后用一个 `h3.h3-triangle` 引出完整 `ul.step-cont`。单个步骤只使用 `li > p > span`，不再创建 H3。
- 每个步骤的 Guide 图片紧跟对应步骤文字，使用 WebP `source` 与 JPG/PNG fallback。
- FAQ 作为独立 H2 章节，问题统一使用 `h3.h3-faq.faq1`，答案紧随其后。
- 结语结束后只放一个标准 Buy Box。

## 旧代码中禁止继承的问题

- 禁止复制 `<style>`、`.rare-forest-article`、`.gible-article`、`.auto-tool-card`、`.table-cont`、`.table-list` 或任何文章专属 class。
- 目录只能有一层 `<ul class="list-filled-dot nav-list1">`；禁止旧代码中的 `<ul class="..."><ul>...` 双层列表。
- `.tit-tips` 只用于语义判断后的两个目录项；禁止旧森林文章一次放三个。
- 正文下载 CTA 最多一组，且必须复制 `assets/download-cta.html`；禁止旧步数文章的三组 CTA。
- “PoGoskill 操作步骤”使用一个 H3 作为模块标题；禁止把“步骤 1／2／3”分别写成 H3。
- 禁止 CTA 后直接进入 `step-cont` 而缺少“PoGoskill 操作步驟”H3。
- 禁止把 `<strong>` 直接放在 `step-cont` 的步骤徽标后；这会被站点 CSS 拆成第三个布局列，使短标题逐字换行。固定使用 `p > span + label`，并在 `label` 内写 `<strong>短標題：</strong>普通正文`；图片盒放在段落之后。
- 禁止跳号、缺失 section、目录锚点与 section 不一致，以及未闭合标签。

## 选择 H3 的判断

先问：该标题下面是否有一个需要独立解释的主题，并至少包含一段完整说明或一个结构化内容块？

- 是：可使用 `h3.h3-triangle`。
- 只是人物名、奖励名、短提示、表格行、步骤编号或一句强调：不用 H3，改为段落、列表、表格或 `step-cont`。

旧文章展示的是内容如何分组，不代表它的 CSS、class、目录嵌套或下载按钮数量仍然正确。当前 `luna-html-contract.md`、资产文件和校验器始终优先。
