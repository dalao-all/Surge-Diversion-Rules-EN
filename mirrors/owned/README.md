# mirrors/owned — V6.1 自建精简 reject（Option A）

运行时 Surge 的 `reject*` DOMAIN-SET / RULE-SET 指向此处（`mirrors/owned/List/...`），**不是**完整 SKK。

## 本次策略变更（精简误删 / 误留修复）

- **停止**使用短裸子串 needle 做 keep 判断：禁止 `meta` / `wise` / `viki` / `grok` / `qwen` / `okex` / `plasma` / `venmo` 等（长度≤5 或显式黑名单）。 由此 `metalex.io` / `metamx` 一类噪声不再因 `meta` 误留。
- **Keep 条件**（从空集合重建）：
  1. `patches/app_tracker_map.yaml` 中的 tracker 后缀/域名（整标签匹配）；
  2. `interest_seed.json` 的 domains / suffixes（整标签 equals / ends-with）；
  3. `reject_interest` 精确/后缀，或无点关键词的整标签级匹配（如 `pangolin`）；
  4. non_ip 的 `DOMAIN-KEYWORD` / 类关键词 `DOMAIN-WILDCARD`：仅当关键词长度≥6 且命中安全长词 allowlist（如 alipay、tiktok、facebook、bilibili）。
- **Tombstones**（永不进 owned reject，并写入 `direct-patch` → DIRECT）： `amdc.alipay.com`, `dualstack-logs.amap.com`, `logs.amap.com`, `umdc.aliapp.org`, `ynuf.aliapp.org`。
- **reject_phishing**：仅保留金融/AI/社交品牌仿冒（alipay、paypal、taobao、google、facebook、apple、microsoft、amazon、binance、okx、bybit、chatgpt、openai、claude），整标签级匹配；文件显著变小。
- **Tracker map 后缀**：`ad.qq.com`, `alimama.cn`, `alimama.com`, `amap.com`, `amemv.com`, `biliapi.com`, `biliapi.net`, `bilibili.cn`, `bilibili.com`, `byteoversea.com`, `ctobsnssdk.com`, `dftoutiao.com`, `dianping.com`, `ele.me`, `elemecdn.com`, `gdt.qq.com`, `gifshow.com`, `isnssdk.com`, `jd.com`, `jingdong.com`, `ksapisrv.com`, `kuaishou.com`, `kuaishouzt.com`, `l.qq.com`, `meituan.com`, `meituan.net`, `mmstat.com`, `pangle-ads.com`, `pangle-b.io`, `pangle.cn`, `pangle.io`, `pglstatp-toutiao.com`, `pinduoduo.com`, `sgsnssdk.com`, `snssdk.com`, `tanx.com`, `tiktokpangle-b.us`, `tiktokpangle-cdn-us.com`, `tiktokpangle.us`, `tobsnssdk.com`, `toutiao.com`, `weibo.cn`, `weibo.com`, `xhscdn.com`, `xiaohongshu.com`, `yangkeduo.com`。
- 重建命令：`python3 scripts/slim_owned_reject_by_apps.py`（幂等）。

## 范围外

Owned 只覆盖下方 catalog `surge_interest: true` 的 App 及相关 tracker。其他 App / 完整广告列表请用上游 SKK：

- https://ruleset.skk.moe
- 或本地缓存：`mirrors/skk/List/domainset/` 与 `mirrors/skk/List/non_ip/`

`mirrors/skk` 仍作上游缓存，供 diff / 刷新 — **不要删除**。

## Catalog 覆盖范围（`surge_interest: true`）

合计：**115** 个 App。

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

## 注意

- 兴趣吸收 / daily bot **不得**把 tombstone 主机写回 owned reject 或 ads-patch。
- **禁止**在未跑本精简脚本的情况下整包覆盖 owned。
- 旧脚本 `apply_tombstones_owned.py` 仅剥 tombstone；V6.1 请用本脚本。
