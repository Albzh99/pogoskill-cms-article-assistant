---
name: pogoskill-cms-en-publisher
description: Convert English PoGoskill SEO drafts into the English site's fixed V2 article HTML and, when explicitly authorized, save a verified CMS draft. Use only for site `pogoskill` / www.pogoskill.com; do not use for Traditional Chinese content or publishing.
---

# PoGoskill English CMS Publisher

## Input contract

- The DOCX must include at least one verifiable layout reference: a reference article URL, CMS page ID, or existing HTML. Read and record it before composing the page; never invent a new visual module when the reference is absent.
- Every ordinary article image that must be uploaded must be embedded at its intended position in the DOCX. A loose folder, local path, or unattached image set is not enough for automatic placement.
- Guide images are not embedded or re-uploaded. The DOCX must state the exact CMS `guides` filename, including extension, at the relevant paragraph or step. Search and reuse only that exact filename and its matching fallback/WebP pair; never guess by meaning or substitute a similar screenshot.
- Guide and operation-step wording is immutable source copy. HTML may wrap an existing source lead phrase in `<strong>`, but must preserve every following word and the original order. Never rewrite, polish, shorten, expand, merge, split or invent a bold lead. If the DOCX has no explicit lead phrase, keep the full step in `<label>` without `<strong>`.

Use this skill only for English articles on `https://www.pogoskill.com`. Traditional Chinese articles must use `pogoskill-cms-publisher`; never mix the two sites' wording, IDs, product links, image roots, or component assets.

默认用中文向团队成员汇报进度、异常和最终结果；只有文章正文、HTML 文案与英文站固定组件保持英文。除非用户明确要求英文回复，否则不要因为源稿是英文就改用英文沟通。

Before any CMS request, read the shared [execution evidence contract](../pogoskill-cms-article-assistant/references/execution-contract.md). Before writing HTML, read:

1. [English V2 HTML contract](references/english-html-contract.md);
2. [English CMS live contract](references/cms-en-live-contract.md);
3. `assets/download-cta.html`, `assets/buybox.html`, `assets/paired-image-box.html`, `assets/responsive-table.html`, and `assets/wide-table.html` in full.

Use `assets/paired-image-box.html` when the DOCX or reference article explicitly groups two images side by side with descriptions. Preserve their left/right order; each image must remain responsive, independently captioned, and no wider than 400px on desktop.

## Fixed boundary

- Read-only discovery and local HTML conversion are allowed by default.
- Create or update a draft only when the user explicitly asks to save that English article in CMS.
- Use CMS POST API only; never use browser forms.
- Never call `/cms/page/make`, publish an article page, call delete endpoints, or modify an unrelated page. The image pipeline must call `/cms/pagepublish/publish` only with a `publish_id` returned by the current `/cms/picture/upload` response, solely to publish image resources.
- Never claim upload success without `page/add` or confirmed `page/update` evidence followed by successful `page/info` readback.

## Required workflow

1. Read the complete English source, including every paragraph, table, FAQ and image marker.
2. Query the English site, V2 template, fields, author, classification, products, sidebar, related pages and exact URL in real time.
   For products, verify live `/cms/product/list` and `/cms/product/info` records, then submit exactly `"product_id": ["4987", "4988"]`: `4987` is PoGoskill/Windows and `4988` is PoGoskill(Mac)/Mac. Never substitute PoGo Wizard, MHN Wizard, iOS Assistant, Android App or IPA records. The shared request script rejects a non-canonical English product payload.
3. Build readable, indented V2 HTML using only approved structures from the English contract.
   The TOC must include exactly two existing `tit-tips` markers: one on the most important content section and one on the PoGoskill recommendation section. Choose by section meaning rather than assuming Part 4/5 or any fixed number, and keep each icon inside its matching TOC link.
   Every English table must use the site's bordered V2 component `table-cont > table-list table3/table4 > ul > li`; never replace it with a native `<table>`. Ordinary tables start from `assets/responsive-table.html`: keep the template border classes and center only the inner `table-list` at a reasonable content-driven width, about 90% by default. Only tables whose actual content is too long to fit comfortably use `assets/wide-table.html`, `data-table-layout="wide"`, and the overflow wrapper; column count alone is not enough.
4. For supplied JPG/PNG article images, create the same-basename WebP and upload both with the image pipeline using `-SiteId 286`. Article HTML must use `https://images.pogoskill.com/<folder>/<semantic-name>.<ext>` public URLs, never the CMS `upload` host. For Guide images named in the source, search the English `guides` library by that exact name; do not guess substitutes.
   If the exact fallback/WebP pair already exists in `/cms/picture/list`, reuse it instead of uploading again. If its public URL returns 404, recover the original image-upload `publish_id`, publish that image resource, and wait until both public URLs are readable before updating the draft. Never substitute a page ID or guess a publish ID.
5. Copy the English download CTA and Buy Box byte-for-byte from this skill's assets. Do not translate, shorten, restyle or reconstruct them. The operation heading may use an approved existing H3 style such as `h3-triangle`, or the verified `h4-filled` variant, according to the selected English reference. Keep the main CTA in its established position after that `How to ... PoGoskill` heading and before the `step-cont` steps; its desktop button group must remain centered. A second CTA is allowed inside FAQ only when that exact source answer explicitly introduces or recommends PoGoskill; otherwise do not add one.
   In the final Conclusion paragraph, link the natural homepage keyword phrase supplied by the source, such as `best Pikmin planting assistant` or `best Pokémon GO location changer`, and keep the following brand name `PoGoskill` outside the link. Never use `PoGoskill` itself as the Conclusion homepage anchor, and never invent a keyword absent from the source.
   Treat English phone screenshots as height-limited vertical media: use `max-height` with `width:auto;height:auto`, not a fixed pixel `max-width` that enlarges the screenshot across the article body.
6. Run the shared validator with the English profile:

```powershell
python scripts/validate-article-html.py <html-path> --profile en --assets-dir skills/pogoskill-cms-en-publisher/assets
```

7. Fix every validator error before any CMS write.
8. Before any draft write, run the plugin-root `scripts/validate-image-coverage.py` against the source structure, image manifest and final HTML. Every DOCX image occurrence, including repeated references to the same media file, must have one manifest item and both public URLs in HTML; all three counts must match and `pass` must be true. On authorization, save only a draft, then immediately call `/cms/page/info` and run the same image coverage check on the readback. Also run `scripts/compare-docx-to-cms-page.py`; `missing_step_blocks` must be empty, and any nonzero result blocks completion. Save the response and run `scripts/assert-cms-page-products.ps1 -ResponsePath <page-info-response.json>`; any product mismatch blocks completion.

## Completion

`Draft ready for review` requires the page ID, write `request_id`, readback `request_id`, `status = 5`, `sync_status = 1`, exact readback products `4987`/`4988`, complete HTML comparison with `missing_step_blocks = []`, exact English CTA, exactly one English Buy Box, published and publicly readable image resources, and confirmation that no page make or article publication occurred.
