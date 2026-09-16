# App → 策略 / 自有 list / 上游 watch 矩阵

日期：2026-09-16（Asia/Shanghai）  
种子：`patches/app_catalog.yaml`（含财务第 2 页）+ `interest_seed.json`；请求日志暂缺。  
「吸收 reject 增量」= 机器人是否允许将 **与该行兴趣相关** 的上游 reject 新增写入 `ads-patch` / 审阅队列（仍受冲突门禁与 budgets 约束；无关联海量 reject 一律 ignore）。

| 文件夹 / 代表 App | 期望出口 | 自有 list | 上游 watch 类别 | 自动吸收 reject 增量？ |
|-------------------|----------|-----------|-----------------|------------------------|
| 系统自带（查找/日历/邮件/Safari…） | （忽略） | — | apple（frozen，不每日扩写） | 否 |
| Dock：微信 | DIRECT | direct-patch（仅防误杀时） | domestic / direct | 仅强相关审阅；默认不自动 |
| 视频：哔哩哔哩 | DIRECT | direct-patch（biliapi 等） | domestic / reject | 是（命中 bili* 且冲突门禁通过 → 多 review） |
| 视频：爱奇艺 / 腾讯视频 | DIRECT | （主配置已有部分） | domestic / reject | 弱：review |
| 社交：小红书 / 酷安 | DIRECT | direct-patch | domestic / reject | 是（已有精确域兴趣） |
| 社交：抖音（国内） | DIRECT | — | domestic / reject | 弱；**勿**当 TikTok 放行 |
| 购物：淘宝 / 京东 / 拼多多 | DIRECT | direct-patch（amdc 等） | domestic / reject | 弱～中：review |
| 外卖：美团 / 点评 / 盒马 | DIRECT | — | domestic | 否（默认 ignore 无关联） |
| 财务软件：招行 / 云闪付 / 工行等 | DIRECT | — | domestic / reject | 弱：review；不臆造域 |
| 财务：支付宝 | DIRECT | — | domestic / reject | 弱：review |
| 财务第2页：欧易 OKX / UU Wallet / Plasma One / Bitget Wallet / Wise | 🪙 数字资产 | finance-critical（关键前置）+ 主配置内联 | — | 是（okx/toblog/AF 等） |
| 财务第2页：Bybit | 💳 Bybit 全球 | finance-bybit-global.list | — | 是 |
| 财务第2页：Bybit EU | 🇩🇪 Bybit 欧洲 | finance-bybit-eu.list | — | 是 |
| 财务第2页：PayPal | 💰 PayPal | （主配置内联） | — | 弱：review |
| 财务第2页：Authenticator（按 Google Authenticator 假设） | 与 Google/AI 登录亲和 | —（不编造未核实域名） | global / ai | 否新增独立域；accounts.google.com 等走主配置 |
| 国内 AI：DeepSeek / 豆包 / 千问 | DIRECT | — | domestic | 否 → **不**写入 ai-critical |
| 外网：TikTok | 🎵 TikTok | （主配置 TikTok 段 + 两条 AF） | reject / global | **广告域是**：pangle → ads；业务域冲突则 review |
| 外网：YouTube | 🎬 流媒体 | —（用 SKK stream*） | stream / stream_us | 否默认自建；强相关 review |
| 外网：Netflix / Viki | 🎬 流媒体 | — | stream_us / stream | 同上 |
| 外网：Instagram / X / Facebook | 🌍 国际网络 | — | global | 仅 P1–P3 命中才考虑 |
| 外网：Chrome / Gmail / Google / Maps / Drive | Google / 国际 /（登录共享） | — | global；Gemini 见 AI | Google OAuth 等按主配置；reject 冲突 → review |
| 国外 AI：Claude / ChatGPT / Gemini / Grok / Cursor | 🤖 AI住宅 | ai-critical.list | ai | **是**（业务域被 reject 误杀时优先前置；冲突门禁） |
| conf 保留：OKX | 🪙 数字资产 | finance-critical.list | （无独立 SKK finance） | 是（toblog/okex/AF 兴趣） |
| conf 保留：Bybit Global / EU | 💳 / 🇩🇪 | finance-bybit-*.list | — | 是（伴生 list 兴趣） |
| conf 保留：PayPal | 💰 PayPal | （主配置内联） | — | 弱：review |
| 广告兴趣：tiktokpangle* | REJECT | ads-patch.list | reject* | **是**（reject_interest；禁止放行） |

## 机器人决策摘要

1. **国内高频** → 兴趣在 DIRECT/domestic；自有 list 只补「已被广告集误杀」的精确项。  
2. **国外 AI** → 积极吸收 `skk-ai` 及相关 reject 冲突例外到 `ai-critical`。  
3. **TikTok** → 业务走 TikTok 组；pangle 走 ads；AppsFlyer 金融前缀勿自动进 TikTok。  
4. **流媒体** → 继续 SKK；机器人默认 review，不建第二套大 list。  
5. **finance 第 2 页** → catalog 已收录；仍 watch okx/bybit/paypal/wise/plasma/bitget；Authenticator 仅 Google/AI 登录亲和，不编造域名。
