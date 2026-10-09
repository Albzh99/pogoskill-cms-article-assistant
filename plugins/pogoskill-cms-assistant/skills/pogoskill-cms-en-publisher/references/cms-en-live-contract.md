# English CMS live contract

Verified through production POST APIs on 2026-09-23. Re-query before each write because IDs and availability can change.

## Confirmed English site

- Site: `pogoskill`
- `site_id`: `286`
- Public URL: `https://www.pogoskill.com`
- Static root: `pogoskill`
- Image root: `pogoskill_images`
- Site status: enabled
- Article V2 template observed on current pages: `template_id = 9831`, `文章内容页面模板-v2-rnui-202408`
- English articles must select exactly these two CMS products:
  - `4987`: `PoGoskill`, Windows (`platform = 1`, DCC PID `7144`)
  - `4988`: `PoGoskill(Mac)`, Mac (`platform = 2`, DCC PID `7145`)
- Submit the field in the canonical CMS form `"product_id": ["4987", "4988"]`. Do not send numeric IDs, a comma-separated string, or substitute PoGo Wizard, MHN Wizard, iOS Assistant, Android App, or IPA products.
- Re-query `/cms/product/list` and `/cms/product/info` before writing and verify both records still belong to `site_id = 286`, are enabled, and retain the names/platforms above. If not, stop rather than guessing replacements.
- Current example sidebar is `sidebar_module_id = 9445`; re-query it rather than assuming it is universal.
- Authors vary between pages; never copy an author ID from an example without a live author lookup.

## Confirmed access evidence

- `/cms/site/list`: `code = 0`, request `3edf7a03-da20-4bab-ba7d-67ca213a7838`
- `/cms/page/list` for site 286: `code = 0`, 856 pages, request `5be60556-5ba3-4ff9-8a0f-cab67a726286`
- `/cms/template/list` for site 286: `code = 0`, request `07d43a4d-4cf4-45e8-a781-f7d16b61a3b9`
- `/cms/picture/dirs` for site 286: `code = 0`, 33 root directories, request `83ec2465-7b08-4c87-bd76-2d18f07c6750`
- `/cms/product/list` for site 286 and keyword PoGoskill: `code = 0`, request `8f3f6a5b-dc85-4b50-bce6-f9e8f7d91e64`
- `/cms/product/info` for 4987: `PoGoskill`, Windows, request `e3640722-1195-4a44-9e9e-c320b26e42f2`
- `/cms/product/info` for 4988: `PoGoskill(Mac)`, Mac, request `efd24116-0df4-4427-b2c0-63676db1c373`

## Confirmed bordered table component

Re-verified on 2026-09-29 through `/cms/page/info` for English V2 page `464348`, request `a36be87a-2bb9-4513-b768-c372317b3288`.

The live bordered table is `div.table-cont > div.table-list.table3/table4 > ul > li`. Its borders and cell presentation come from the V2 template classes. A native `<table>` that only adds width and centering does not reproduce this component and is forbidden for English articles. Center the existing `.table-list` without removing or replacing those classes.

These values prove access at the verification time; they do not replace live checks. Do not claim the English CMS is inaccessible without following the shared three-attempt evidence contract.

## Site separation

English and Traditional Chinese are different CMS sites:

| Concern | English | Traditional Chinese |
| --- | --- | --- |
| Site name | `pogoskill` | `pogoskilltw` |
| Site ID | `286` | `324` |
| Domain | `www.pogoskill.com` | `tw.pogoskill.com` |
| Image root | `pogoskill_images` | `pogoskilltw_images` |
| V2 template observed | `9831` | `9916` |
| Download IDs | `7144` / `7145` | `7925` / `7926` |

Never transfer IDs, URLs, content language or assets across these site profiles.
