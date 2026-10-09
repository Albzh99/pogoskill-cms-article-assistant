# CMS 真实执行与证据契约

本契约用于防止 Agent 没有执行就声称失败、正在处理或已经完成。凡涉及 CMS 读取、图片上传或草稿写入，必须遵守。

## 1. 先执行，再描述

- “正在读取／正在上传／正在回读”等进度句后面必须立即出现真实工具调用；不得只发进度文字后停下。
- 上传脚本若返回运行会话 ID，必须轮询同一会话直至退出并读取最终输出。禁止把工具执行改成无人跟踪的交互式终端阶段，也不得因当前消息没有 manifest 汇总就声称未执行。
- API Key 保存是唯一需要使用者配合的交互步骤。必须从当前插件根目录创建可跟踪的终端会话，等待剪贴板提示，再把该会话实际显示到 Codex 终端面板；禁止复用旧缓存版本路径。只有显示终端工具成功后才能声称终端已打开。使用者按 Enter 后继续等待同一进程退出，并立即用同一插件根目录的 `cms-check-api-key.ps1` 回读验证。
- 只有工具或 API 已返回可核验结果，才能使用“已读取／已上传／已保存”等完成措辞。
- 本地 HTML、JSON payload、图片转换完成不等于 CMS 已执行。
- 不得凭感觉、旧对话、浏览器状态或一次命令准备过程判断 CMS、网络或权限异常。

## 2. 固定调用方式

1. JSON 接口只用插件根目录 `scripts/cms-request.ps1` 发出真实 `POST`，不得改用浏览器表单。
2. 调用前统一使用 `Get-CmsStoredApiKey`。脚本先读取 DPAPI 加密、当前用户专属的稳定本地存储，再兼容读取 Windows Credential Manager 的 `PoGoskillCMS/OpenAPI`；只要任一位置有效，就禁止再次索取 API Key。Windows `1312` 仅表示当前进程无法使用 Credential Manager，不等于备用凭据不存在。
3. HTTP 200 不是成功；只有响应 JSON 的 `code === 0` 才算业务成功。
4. 每次请求都把请求 body 与响应保存到当前文章工作目录；文件名包含顺序、接口和时间，例如 `03-page-add-request.json`、`03-page-add-response.json`。
5. 日志和回复只记录 endpoint、时间、curl exit code、业务 `code`、`msg`、`request_id`、页面 ID；不得记录 API Key。
6. 页面 payload 只序列化一次。发出 `page/add` 或 `page/update` 前，必须检查解码后的 `content` 没有字面 `` `n ``、`\n`、`‘n`、`’n` 或相应 HTML 实体；HTML 排版换行必须是真实换行。请求 JSON 文件中由序列化器生成的 `\n` 编码本身不是污染。

## 3. 禁止虚构“连不上”

在报告“读取不到、无法连接、没有权限、接口不可用”前，必须满足：

1. 已对目标 endpoint 发出真实 POST；
2. 若属于网络、超时、5xx 或不明确的瞬时错误，最多执行三次真实尝试；
3. 三次之间保留各自证据，不用同一句推测代替请求；
4. 最终报告列出三次请求的 endpoint、时间、curl exit/business code、`msg` 和可用的 `request_id`。

参数错误、业务校验错误或明确 401/403 不得伪装成网络故障。先根据返回的 `code` 和 `msg` 修正参数或鉴权路径；CMS 已知通常可用，默认判断应是“当前调用尚未满足条件”，而不是“CMS 坏了”。

## 4. 写请求的防重复规则

- `/cms/page/add` 或 `/cms/page/update` 返回明确 `code: 0` 时，禁止再次写入。
- 写请求超时、连接中断或结果不确定时，先用 `/cms/page/list` 按精确 URL 和标题查询，再用 `/cms/page/info` 核验；确认没有新草稿后才可重试写请求。
- URL 或标题命中页面但不能唯一确认归属时停止写入，防止重复草稿或覆盖旧文章。
- 对同一写请求不得无脑自动重试三次；每次重试前必须完成上述查重。
- 图片上传无最终汇总或进程中断时，先检查 manifest 断点、文章目录 `cms-evidence` 和 `/cms/picture/list`；从已保存响应恢复上传 `request_id`/`publish_id`。确认 CMS 已存在同名同尺寸图片对时禁止重传。

## 5. “已上传草稿”的最低证据

只有以下条件全部成立，才能说“已上传草稿”或 `Draft ready for review`：

1. `/cms/page/add` 或已确认目标的 `/cms/page/update` 返回 `code: 0`；
2. 获得页面 ID 和写请求 `request_id`；
3. 紧接着 `/cms/page/info` 返回 `code: 0`，并获得回读 `request_id`；
4. 回读页面 ID、URL、模板和目标文章一致；
5. 回读确认 `status = 5`、`sync_status = 1`，即草稿且未生成；
6. 回读正文与本地最终 HTML 完整比较通过，且元数据、图片、下载区与 Buy Box 均存在；
7. 未调用 `/cms/page/make`、未发布文章页面；`/cms/pagepublish/publish` 只用于有当前 `/cms/picture/upload` request_id 佐证的图片 `publish_id`；未调用删除接口，也未修改无关旧文章。

缺少任一项时，只能说明已经完成到哪个可验证阶段，不得把“payload 已准备”“请求准备发送”“本地校验通过”描述成已上传。

## 6. 允许停止的客观条件

只在以下情况停止并向用户报告 `Blocked`：

- 必要源文件确实不存在；
- `Get-CmsStoredApiKey` 已确认 DPAPI 加密本地存储和 Windows Credential Manager 中都没有凭据；
- 同一客观失败经过三次真实请求仍重复出现，并已保存证据；
- 目标页面或关键 CMS 字段无法唯一确认；
- 下一步需要用户新增授权。

用户已要求保存当前文章草稿，就已授权正常的只读发现、查重、图片处理、`page/add` 或已确认目标的 `page/update`、写后回读与完整性比较。不得为这些常规步骤逐项停下来再次询问。

若用户要求修改现有草稿，而且 `/cms/picture/list` 已确认正文所需图片对存在，则必须复用图片。图片未发布导致前台 URL 为 404 时，不得重复上传或停止；必须从原始 manifest/上传响应恢复图片 `publish_id`，单独发布图片资源并确认前台双格式可读，再继续 `/cms/page/update`。`/picture/list` 不能证明 publish ID，禁止猜测或使用页面 ID。

## 7. 最终报告格式

成功报告必须包含：页面 ID、URL、`status`、`sync_status`、写入 endpoint、写入 `request_id`、回读 `request_id`、HTML/来源比较结果、图片数量，以及“未生成、未发布”。

失败报告必须包含：实际完成阶段、失败 endpoint、每次真实尝试的证据、已保存的证据文件路径，以及仍缺少的客观条件。不得说“稍后自动继续”或声称不存在的后台任务仍在运行。
