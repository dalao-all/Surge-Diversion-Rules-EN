# 规则分层与策略意图（你的订阅 Surge V6.0）

本文说明我在本项目中如何分层组织规则、各策略组想表达什么，以及它们与 [`rule-map.html`](../rule-map.html) 的对应关系。

> 仅供技术交流与规则设定学习。不是代理服务，不提供节点。

## 1. 为什么分层

Surge 规则**自上而下**命中即停。若把「关键业务例外」写在庞大广告底座之后，会被误杀；若把整包上游塞进主 conf，又难审计、难回滚。  
因此我拆成四层，主 conf 只保留顺序与策略绑定，列表本体尽量外置到本仓库 raw。

## 2. 四层结构

```text
① patches/          关键前置例外（先于广告底座）
② mirrors/skk/      主体分流 + 广告/国内/流媒体/全球索引
③ mirrors/scripts/  AdBlock 模块脚本（MITM/改写用）
④ 主 conf 内联      协议级 / 不宜进 list 的精确例外
```

### 2.1 `patches/` — 关键前置例外

| 文件 | 策略绑定（主 conf RULE-SET） | 意图 |
|------|------------------------------|------|
| `ai-critical.list` | 🤖 AI住宅 | 外网 AI / 登录相关域，防止被 reject 误杀 |
| `finance-critical.list` | 🪙 数字资产 | OKX 等关键财务前置 |
| `finance-bybit-eu.list` | 🇩🇪 Bybit 欧洲 | Bybit EU（独立 list：RULE-SET 整文件单策略） |
| `finance-bybit-global.list` | 💳 Bybit 全球 | Bybit Global |
| `ads-patch.list` | REJECT | 广告兴趣增量（如 pangle） |
| `direct-patch.list` | DIRECT | 国内 App 兼容例外（biliapi、小红书、酷安等；amdc extended-matching 写在主配置） |

这些 RULE-SET 必须出现在远程 SKK `reject*` **之前**。兴趣机器人只吸收与 `interest_seed` / selectors 相关的上游新增，避免海量无关 reject 灌库。

配套元数据：`manifest.json`、`selectors.yaml`、`upstream_watch.yaml`、`app_catalog.yaml`、`interest_seed.json`。

### 2.2 `mirrors/skk/` — 主体索引镜像

自 `ruleset.skk.moe` **原样镜像**，路径保持 `List/domainset|non_ip|ip/...`。  
用途：广告拒绝、国内直连、Apple/Microsoft、流媒体分区、Telegram、全球列表、China IP 等。  
我在此目录**不做语义改写**；差异与例外一律进 `patches/` 或内联。映射见 `mirrors/skk` 侧 `SOURCE_MAP.json`（及总表 `mirrors/SOURCE_MAP.json`）。

### 2.3 `mirrors/scripts/` — 模块脚本镜像

AdBlock 模块曾引用的 fmz200 / kokoryh 等脚本，镜像到本仓库后由 `profiles/Your-Subscription-AdBlock-V6.0.sgmodule` 的 raw URL 引用。  
目的是自有可控、减少上游偶然失效；**不扩大** MITM / 脚本范围。

### 2.4 主 conf 内联例外

适合留在 conf 里的包括：

- DoH/DoT / STUN 等协议与泄漏防护
- 订阅 API 域名 DIRECT（`em.mesl.cloud`）；站点 `meslcloud.com` 走国际网络
- Apple 稳定性例外、死域名快速失败
- TikTok / Google / PayPal 等大块业务规则（部分曾从 blackmatrix7 远程改为内联）
- FINAL 与 GEOIP / LAN

`mirrors/blackmatrix7/` 保留历史 list 镜像，便于对照；V6.0 分享 conf **不再**远程 RULE-SET 引用它们。

## 3. 匹配顺序（与 rule-map 一致）

逻辑顺序（简化）：

1. **防护与清理** — DoH/DoT、STUN、captive、订阅域 DIRECT、Apple 例外  
2. **patches 关键前置** — AI / 金融 / ads / direct  
3. **SKK reject\*** — 广告与钓鱼底座  
4. **业务策略** — TikTok、AI 列表、金融内联、国内 DIRECT、流媒体、国际  
5. **IP 级规则** — 对应 non_ip 的 ip 列表  
6. **FINAL** — 含 `dns-failed` 感知的兜底  

交互图 [`rule-map.html`](../rule-map.html) 把上述节点画成可切换 EN/中文的拓扑；README / `index.html` 中的预览图来自 `assets/rule-map-preview.png`。  
**图是学习用可视化，以分享版 conf 实际 RULE 顺序为准。**

## 4. 策略组意图

| 策略组 | 类型 | 意图 |
|--------|------|------|
| 📦 Your Subscription | select + policy-path | 节点池入口（占位订阅，需自行替换） |
| 🤖 AI住宅 | fallback | 美国家宽优先，机房备选；敏感身份业务 |
| 🎵 TikTok | smart | 美国机房；排除 0.3X 与家宽 |
| 🪙 数字资产 | fallback | 台湾家宽优先（OKX / Wallet / Wise 等） |
| 💳 Bybit 全球 | fallback | Bybit Global |
| 🇩🇪 Bybit 欧洲 | fallback | Bybit EU（德国标签节点） |
| 🇬🇧 英国专属 | fallback | 英国本地服务 |
| 💰 PayPal | fallback | 美国家宽优先，英国备选 |
| 🎬 流媒体 | smart | 高带宽区域 Smart |
| 🌍 国际网络 | smart | 通讯与一般国际 |
| 隐藏 *家宽池 / *机房池 | fallback + hidden | 供上层 include-other-group |

组名是**样例标签**，依赖订阅节点命名中的地区/家宽字样；不构成对任何服务商的推荐。

## 5. 与文档、脚本的关系

| 文档 / 脚本 | 作用 |
|-------------|------|
| `GETTING_STARTED.zh.md` | 安装与安全注意 |
| `APP_POLICY_MATRIX.md` | App → 出口 / list / watch |
| `INTEREST_MODEL.md` | 兴趣种子如何筛选上游增量 |
| `MAINTENANCE.md` / `BOT_REQUIREMENTS.md` | 维护日程与机器人规格 |
| `scripts/daily_patch_bot.py` | 拉取上游 → 候选 → PR |
| `scripts/regression_cases.json` | 冒烟对照 |

## 6. 安全边界

- 公开仓禁止出现真实订阅令牌参数、私有订阅主机名、以及订阅拉取路径  
- 分享 conf 的 policy-path 用 `subscription.example.invalid`；订阅/站点匹配域保留真实主机名（非 token）  
- 私用带订阅配置不进本仓库  

英文说明见姊妹仓：https://github.com/dalao-all/Surge-Diversion-Rules-EN （`docs/RULES_OVERVIEW.md`）
