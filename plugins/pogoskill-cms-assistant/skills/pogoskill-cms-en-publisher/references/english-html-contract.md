# English V2 HTML contract

## 0. Required source package

Before writing HTML, record at least one layout reference supplied in the DOCX: a reference article URL, CMS page ID, or existing HTML. Load the referenced CMS HTML when a URL or page ID is supplied, then reuse only its approved V2 module structure. Do not invent a layout when no reference is present.

Images that need a new CMS upload must be embedded in the DOCX exactly where they belong; their surrounding paragraphs define placement. Guide images are different: the DOCX must state the exact CMS `guides` filename, including extension, at the corresponding step or paragraph. Reuse only the exact-name fallback/WebP pair. Do not infer a screenshot from the prose, substitute a similar image, or upload a new Guide image.

This contract is derived from three supplied English production examples and normalized to remove malformed legacy nesting and one-line output. Copy the established component structure; do not imitate accidental markup defects.

## Non-negotiable rules

- Write natural English only. Do not insert Traditional Chinese labels, Taiwanese links or Taiwan product IDs.
- Do not output an H1; CMS renders it from `subject`.
- Do not add `<style>`, article-specific wrapper classes, custom cards, colored notice boxes or new visual components.
- Keep HTML readable with one logical tag per line and consistent indentation. Never compress the article into one line.
- Preserve the complete source article. Do not omit late sections, tables, FAQ, conclusion, images, download CTA or Buy Box.
- Every class must already exist in the supplied English examples or an English reference page selected through CMS.

## Canonical order

1. Two or more introductory paragraphs.
2. Main image in the standard `img-wrap > picture > source + img` structure.
3. One table of contents: `<ul class="list-filled-dot nav-list1">` containing the `<li>` items directly. Do not create a bare nested `<ul>`.
4. Main sections in source order. Each linked section uses `id="partN"`, begins with one H2, and has exactly one matching TOC link.
5. If the article recommends PoGoskill: complete product explanation, approved feature list, `How to Use PoGoskill` subheading, one centered exact download CTA, then one `step-cont` list.
6. FAQ section using the established FAQ heading structure.
7. Conclusion section.
8. Exactly one complete Buy Box copied from `assets/buybox.html`, after the conclusion text.

Do not add a TOC entry for a section that does not have a matching ID. Do not leave duplicate IDs. The Conclusion may be assigned the next `partN` and included in the TOC; choose one consistent approach for both TOC and section.

### Required HOT / NEW markers in the table of contents

- Every English article TOC contains exactly two `tit-tips` icons: one on the article's most important/key section and one on the section that introduces or recommends PoGoskill.
- Select the entries by meaning, not by a fixed Part number. The PoGoskill section may be Part 3, Part 5, or another position depending on the source.
- Use only the existing site assets `https://images.pogoskill.com/hot-tips.png?w=100&amp;h=38` or `https://images.pogoskill.com/new-tips.png?w=100&amp;h=38`, with `class="tit-tips"` and `width="50"`.
- Place the icon inside the matching TOC `<a>`, immediately after its visible title. Do not place it in the H2, article body, or outside the link.
- Do not mark every entry. If the key section is also the PoGoskill section, choose the next most useful substantive section for the second marker so two different TOC links are marked.

```html
<li>
  <a href="#partN">
    Part N. How to Use PoGoskill
    <img class="tit-tips"
         src="https://images.pogoskill.com/hot-tips.png?w=100&amp;h=38"
         width="50"
         alt="Hot">
  </a>
</li>
```

## Heading hierarchy

- H2: major article parts, FAQ and Conclusion.
- H3: genuine subtopics only. Approved observed variants are `h3-triangle`, `h3-orange-local`, `h3-red-local`, `h3-num`, and `h3-faq faq1`.
- H4: only a real subsection nested beneath an H3/H2 when the selected English reference already uses `h4-filled` for the same content role.
- Never use headings merely to enlarge text. Never place consecutive headings without explanatory content.
- Individual operation steps are list items, not separate H3 headings.

## Lists, tables and links

- Use an observed `list-cont` variant such as `list-star`, `list-lamp`, `list-angle`, `list-flag`, `list-primary-dot` or `list-white-dot` only when its semantic role matches the reference.
- Every `<li>` must remain inside its owning `<ul>` or `<ol>`. Images belonging to a step stay inside that `<li>` after its paragraph; never place a `<div>` directly between list items.
- English V2 bordered tables are not native `<table>` elements. They must preserve the verified template hierarchy `div.table-cont > div.table-list.table3/table4 > ul > li`. The `table-cont`, `table-list` and `table3`/`table4` classes render the existing borders and cell layout; removing them produces the broken borderless result.
- Ordinary comparison tables start from `assets/responsive-table.html`. Keep `.table-cont` and `.table-list.table4`, and center only the inner `.table-list` with `width:90%;max-width:100%;margin:0 auto;`. Adjust the percentage only within 70%-100% when content requires it.
- Use `assets/wide-table.html` only when cell content is genuinely too long. Keep `.table-cont.overflow-auto`, `.table-list.table3`, `data-table-layout="wide"`, `width:100%`, and `min-width:840px`; 680px is the absolute minimum.
- Each `<ul>` is one row and each `<li>` is one cell. Every row must have the same number of cells, with the first row serving as the header row. Do not put a native `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>` or `<td>` inside this module.
- Do not convert the bordered template into a generic Bootstrap table or a centered native table. Centering is an additional inline layout adjustment, not a replacement for the site's border classes.
- Internal links use `https://www.pogoskill.com/...`; external promotional links use the supplied `rel` and `target` attributes. Do not copy `tw.pogoskill.com` into English HTML.

## Images

Use the established structure:

```html
<div class="img-wrap text-center">
  <picture>
    <source class="lozad img-fluid"
            srcset="https://images.pogoskill.com/loading.svg"
            data-srcset="https://images.pogoskill.com/<folder>/<semantic-name>.webp?w=<width>&amp;h=<height>"
            type="image/webp">
    <img class="lozad img-fluid"
         src="https://images.pogoskill.com/loading.svg"
         data-src="https://images.pogoskill.com/<folder>/<semantic-name>.jpg?w=<width>&amp;h=<height>"
         alt="accurate English description">
  </picture>
</div>
```

The WebP and JPG/PNG basenames must match. ALT describes the actual image. Keep the main image at 850×460 and do not invent URLs or claim upload success without API evidence.

Use `/cms/picture/upload` response `data.list[].url` as the public article URL; if it is absent, verify `/cms/picture/list` field `online`. The CMS `upload` URL is evidence only. Never claim that the API cannot provide a frontend URL before checking those fields, and never place `site.p.cms.afirstsoft.cn`, `attachment=1`, or another CMS backend URL in article HTML. Public English image URLs must use `https://images.pogoskill.com/`; filenames must remain readable semantic names without a trailing checksum/hash.

Before image publication, a correct public URL can return HTTP 404. This is an intermediate state, not a reason to upload again. Recover the original `/cms/picture/upload` `publish_id`, publish only that image resource through `/cms/pagepublish/publish`, and wait until both fallback and WebP public URLs are readable before inserting them into a draft. Never pass a page ID or an article-generation ID to this step.

- User-supplied article images are the primary source. Convert each JPG/PNG to a same-basename WebP and keep both formats.
- Upload against English `site_id = 286` and choose the English image directory by article topic, such as `change-location`, `pokemon-ios`, `pikmin-bloom` or another live-confirmed folder.
- Guide/product screenshots are different: when the source supplies an exact Guide filename, search the English `guides` library and reuse that exact image pair. Do not guess a visually similar screenshot.

### Paired images with descriptions

Use this module only when the DOCX or reference article clearly treats two images as one side-by-side comparison or step box. Copy `assets/paired-image-box.html` and replace its placeholders; do not invent another grid or custom CSS.

- Keep `div.row.justify-content-center[data-image-layout="pair"]` with exactly two `div.col-12.col-md-6.text-center.mb-3` children. This keeps the images side by side on desktop and stacks them on narrow screens.
- Each child must contain one complete `img-wrap > picture > source + img` followed immediately by a non-empty `<p class="text-center">description</p>`.
- A horizontal image must use `max-width` of at most `400px` plus `width:100%;height:auto;`. A phone screenshot or other vertical image must instead use `max-height` of at most `520px` with `max-width:100%;width:auto;height:auto;`.
- Preserve the source left/right order. Give each image its own matching WebP/fallback pair, accurate ALT, and description; do not stretch or crop an image to make both items look equal.
- If the source also provides one shared description, keep it as a normal paragraph after the paired module. Still fill the two short per-image descriptions so the relationship remains understandable.

Do not combine two unrelated adjacent images into this module merely to make the page look richer.
- Never upload an English image into `pogoskilltw_images`, and never silently reuse a Taiwan-site media URL as proof of an English CMS upload.
- English phone screenshots are height-limited media. Their `<img>` must use `style="max-height:520px;max-width:100%;width:auto;height:auto;"` or a smaller justified `max-height`; do not use a fixed pixel `max-width` as the main limit. Landscape article images continue to use the normal width-limited style.

## PoGoskill recommendation block

- The first mention of PoGoskill in its recommendation section links to `https://www.pogoskill.com/`.
- Explain what PoGoskill does and why it solves the article's problem before showing download buttons.
- Use the reference site's existing feature heading/list. Do not create a custom feature card.
- Insert `assets/download-cta.html` exactly once in the main recommendation block. Keep it in the established position after the `How to Use PoGoskill` heading and immediately before the `step-cont` list.
- The download CTA must retain both desktop secure-download boxes and the mobile Buy Now links. Do not remove wrappers, SVG references or button classes.
- The desktop `.btn-groups` must retain `style="display:flex;justify-content:center;"` so both download buttons stay centered regardless of the approved H3/H4 heading variant above them.
- Place one clear existing-style operation heading before the CTA/steps grouping. English reference pages may use an approved H3 such as `<h3 class="h3-triangle">How to Reset &amp; Modify GPS Coordinates Smoothly via PoGoskill?</h3>` or `<h3 class="h3-orange-local">How to Use PoGoskill</h3>`, and may also use `<h4 class="h4-filled">How to Use PoGoskill</h4>`. Preserve the appropriate verified variant instead of forcing every article to H4. Do not translate it or turn each individual step into a heading.
- Each step uses this stable structure:

```html
<ul class="step-cont">
  <li>
    <p>
      <span>Step 1</span>
      <label><strong>Connect your device:</strong> Complete instruction.</label>
    </p>
    <!-- matching image box, when supplied -->
  </li>
</ul>
```

Keep the label around both bold lead text and the normal description so the layout cannot split into narrow columns.

This markup change must not edit the source wording. The `<strong>` content may only be an exact lead phrase already present at the start of the DOCX step, normally the text before its first colon. Everything after it must remain word-for-word and in the same order. Do not paraphrase, polish, shorten, expand, merge or split Guide instructions. When the source has no explicit lead phrase, omit `<strong>` and place the full original instruction in `<label>`.

## FAQ

- FAQ is a major H2 section.
- Each question uses the existing `h3-faq faq1` component, including its complete approved icon markup copied from a verified English page.
- Put one or more answer paragraphs immediately after each question.
- Do not insert a download CTA inside FAQ unless that exact source answer explicitly introduces or recommends PoGoskill. When it does, one additional centered copy of the English CTA is allowed immediately after that answer; do not add it merely because the article is product-related.

## Download CTA and Buy Box

- `assets/download-cta.html` is the only permitted English inline download CTA. It uses English download IDs `7144` and `7145` and `www.pogoskill.com` purchase links.
- `assets/buybox.html` is the only permitted English Buy Box. It includes desktop and mobile platform variants, product buttons, badges and counts.
- Copy both assets exactly. Do not hand-retype, shorten, translate, reorder, restyle or partially copy them.
- A valid article normally contains one main inline CTA. It may contain one additional FAQ CTA only when the source FAQ explicitly recommends PoGoskill, so the absolute maximum is two. Both copies must remain byte-for-byte equal to the English CTA asset and centered.
- The `dev-desktop` / `dev-mobile` inside the Buy Box do not count as a second inline CTA.

## Conclusion homepage link

The final Conclusion paragraph must contain one homepage link whose anchor is the natural keyword phrase already supplied in the source. Keep `PoGoskill` immediately after that link as plain text:

```html
<section id="partN">
  <h2>Conclusion</h2>
  <p>For a reliable option, the <a href="https://www.pogoskill.com/">best Pikmin planting assistant</a> PoGoskill can help with the workflow described above.</p>
</section>
```

- Use the actual phrase from the DOCX, such as `best Pikmin planting assistant`, `best Pikmin location changer`, or `best Pokémon GO location changer`.
- Never use `<a ...>PoGoskill</a>` for the Conclusion homepage link.
- Do not invent a keyword phrase when the source does not provide one; stop and report the missing Conclusion keyword.

## Defects seen in source examples that must be corrected

- Bare `<ul>` nested directly inside the TOC `<ul>`.
- Images or `<div>` elements placed between `<li>` siblings instead of inside the correct `<li>`.
- Entire sections compressed onto one line.
- Missing spaces around inline `<b>` elements.
- Broken words caused by adjacent text, such as `Psystrikeprovides`.
- Heading choices based only on visual size rather than document hierarchy.

The supplied articles are references for components and visual language, not permission to repeat these defects.
