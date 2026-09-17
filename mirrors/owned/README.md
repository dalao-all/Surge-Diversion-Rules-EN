# mirrors/owned — Option A (V6.1) app-scoped reject

Runtime `reject*` DOMAIN-SET / RULE-SET in Surge conf point here (`mirrors/owned/List/...`), **not** at full SKK.

## What this is

- **Self-built / curated** `domainset/{reject,reject_extra,reject_phishing}.conf` and `non_ip/{reject,reject-drop,reject-no-drop}.conf`.
- **Scoped** to apps with `surge_interest: true` in `patches/app_catalog.yaml`, matched via `patches/interest_seed.json` (domains / suffixes / keywords / vendors).
- **Tombstones** from `patches/tombstones.yaml` are never included (e.g. `ynuf.aliapp.org`, `amdc.alipay.com`, `logs.amap.com`, `dualstack-logs.amap.com`). Those hosts are promoted to DIRECT via `patches/direct-patch.list`.
- Rebuild: `python3 scripts/slim_owned_reject_by_apps.py` (idempotent; reads SKK cache + seed + tombstones + catalog).

## Outside this scope

Owned rejects **only** cover the catalog apps listed below. For other apps / full ad-block lists, use upstream SKK:

- https://ruleset.skk.moe
- or local cache: `mirrors/skk/List/domainset/` and `mirrors/skk/List/non_ip/`

`mirrors/skk` remains an upstream cache for diff / refresh — do **not** delete it.

## Catalog apps in scope (`surge_interest: true`)

Total: **115** apps.

### Dock (1)

- 微信

### 主屏幕 (2)

- Grow
- 爱思全能版

### 商业 (6)

- BOSS直聘
- 企查查
- 国家网络身份认证
- 智联招聘
- 猎聘
- 贝壳找房

### 国内AI (6)

- DeepSeek
- Marvis
- TRAE
- ima
- 千问
- 豆包

### 国外AI (10)

- ChatGPT
- Claude
- Cursor
- DejaVocab
- Gemini
- Grok
- Grok Bot
- Obsidian
- Tableau
- 云端硬盘

### 外卖软件 (4)

- 大众点评
- 淘宝闪购
- 盒马
- 美团

### 外网 (12)

- Chrome
- Facebook
- Gmail
- Google
- Google Maps
- Instagram
- Netflix
- Sanas
- TikTok
- Viki
- X
- YouTube

### 家庭控制 (8)

- 个人所得税
- 中国移动
- 九号出行
- 交管12123
- 华为智慧生活
- 吉利汽车
- 无忧行
- 米家

### 教育 (1)

- 网易有道词典

### 旅行 (6)

- 哈啰
- 天府通
- 携程旅行
- 航旅纵横
- 铁路12306
- 高德地图

### 社交网络 (9)

- 剪映
- 小红书
- 微博
- 快手
- 快手极速版
- 悦通行
- 懂车帝
- 汽车之家
- 酷安

### 视频软件 (3)

- 哔哩哔哩
- 爱奇艺
- 腾讯视频

### 财务 (9)

- QQ
- UU远程
- iCost
- 上岛记
- 扫描全能王
- 抖音
- 支付宝
- 网易云音乐
- 钉钉

### 财务软件 (20)

- Authenticator
- Bitget Wallet
- Bybit
- Bybit EU
- Cookie
- MONO记账
- PayPal
- Plasma One
- UU Wallet
- Wise
- 个人手机银行
- 中国工商银行
- 中国建设银行
- 云闪付
- 京东金融
- 兴业银行
- 动卡空间
- 招商银行
- 掌上生活
- 欧易 OKX

### 购物软件 (18)

- 一淘
- 京东
- 京东AI购
- 京粉
- 山姆会员商店
- 得物
- 拼多多
- 掌上英雄联盟
- 淘宝
- 淘票票
- 猫眼
- 王者荣耀
- 省钱快报
- 转转
- 闲鱼
- 阿里巴巴
- 飞智游戏厅
- 黑猫投诉

## Notes

- Interest absorb / daily bot must **skip** tombstoned hosts (never re-add into owned reject or ads-patch).
- Do **not** whole-replace owned from upstream without running this slim filter.
- Legacy `scripts/apply_tombstones_owned.py` only stripped tombstones; prefer `slim_owned_reject_by_apps.py` for V6.1 Option A size.
