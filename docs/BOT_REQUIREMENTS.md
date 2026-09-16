# 机器人规则更新要求（App 清单兴趣源）

规格级文档。时区：**Asia/Shanghai**。  
配套：`patches/app_catalog.yaml`、`patches/interest_seed_from_apps.json`、`docs/APP_POLICY_MATRIX.md`、`docs/INTEREST_MODEL.md`、`docs/MAINTENANCE.md`、`patches/upstream_watch.yaml`、`patches/selectors.yaml`。

本文描述**规划交付**：以 iPhone App 分类清单为兴趣种子来源，驱动每日上游增量吸收与 PR。**不是**要求本回合完成自动推仓实现。

---

## 0. 输入假设（MUST 对齐）

| 输入 | 状态 | 用法 |
|------|------|------|
| Surge / HAR 长期请求日志 | **不可用** | 用户无法提供；已导出 zip 经核实为 **PacketTunnelProvider / SGLog 应用日志**，**不可作域名种子** |
| iPhone App 分类清单 | **可用**（2026-09-16 截图识别） | 主兴趣源 → `app_catalog.yaml` → 种子草案 |
| 现有 `profiles/MESL-Surge-V6.0.conf` + `patches/*.list` + `manifest.json` | **可用** | 补全 vendor/suffix、策略组、finance 兴趣；**不改业务规则行**（本规划阶段） |
| `upstream_watch.yaml` / `selectors.yaml` | **可用** | 限定 watch 面与选择器阈值 |

**结论一句话**：请求日志 zip 仅含隧道/SGLog 应用日志，不能推导业务域名；种子以 App 目录 + 现有 conf/patches 为准。

---

## 1. 目标

1. 每天 **09:00** 与 **21:00**（Asia/Shanghai）仅拉取 `upstream_watch.yaml` → `frequent` 上游，diff **新增行**。
2. 只吸收与 **已安装 App（catalog 中 `surge_interest=true`）** 或 **已启用策略组** 相关的增量，写入自有 curated lists（`patches/*.list` 草案）。
3. 默认 **直接推送到 main 更新 patches**（主人不审 PR）；仅在冲突/异常时停止并通知；高置信自动合并仅 Phase3 可选且默认关闭。
4. 判定链路：App catalog → vendor / keyword / suffix 种子 → 映射上游文件类别 → 兴趣过滤（见 INTEREST_MODEL P1–P5）。

---

## 2. 非目标（MUST NOT）

- **禁止**整包同步 SKK、`reject.conf`、Loyalsoldier、blackmatrix7 AllInOne。
- **禁止**无种子 / 无兴趣命中时自动放行或自动写入业务 list。
- **禁止**修改、提交或泄露用户订阅 token / `policy-path` 真实地址。
- **禁止**把系统自带 App（查找、日历、邮件等）写入兴趣种子。
- **禁止**把 `tiktokpangle*` / pangle 类广告域写入任何 TikTok 或业务放行 list。
- **禁止**把 STUN / iCloud Private Relay 等主配置 pre-matching 段迁入 `ads-patch.list`。
- **禁止**把整个国内直连大段塞进 `direct-patch.list`。
- **禁止**在规划/日常维护中改写 `profiles/MESL-Surge-V6.0.conf` 业务规则（除非另开明确变更单）。

---

## 3. App → 策略组映射原则

| 原则 | 说明 |
|------|------|
| 国内 App 默认 | `region=cn` → 兴趣偏 **DIRECT / domestic**；目标 list 多为 `direct-patch.list`（仅防误杀精确项），日常靠 SKK domestic/direct |
| 国外 AI | ChatGPT / Claude / Gemini / Grok / Cursor 等 → **🤖 AI住宅** → `ai-critical.list` + watch `skk-ai` |
| TikTok | 国际版 TikTok → **🎵 TikTok**；抖音（国内）→ DIRECT 兴趣，**勿**与 TikTok 放行混淆 |
| YouTube / Netflix / Viki | → **🎬 流媒体**；watch `stream` / `stream_us`；默认不自建大 list，强相关仅 review |
| Google 系 | Chrome / Gmail / Google / Maps / Drive → 现有 **Google / AI / 国际** 规则面；登录共享端点与 YouTube 顺序约束保持主配置既有逻辑 |
| 加密 / 跨境金融 | 清单若未出现但 conf 已有（OKX / Bybit / PayPal 等）→ **保留 finance 兴趣**（见 catalog `from_config_not_on_homescreen`） |
| 系统自带 App | `region=system`，`surge_interest=false`，**不进种子** |
| 国内/国际版并存 | 微信≠WhatsApp 类；抖音≠TikTok；QQ≠海外社交 —— 映射必须按 App 名与 folder 区分 |

`policy_hint` 取值应对齐主配置已启用组：`DIRECT`、`🤖 AI住宅`、`🎵 TikTok`、`🎬 流媒体`、`🪙 数字资产`、`💳 Bybit 全球`、`🇩🇪 Bybit 欧洲`、`💰 PayPal`、`🌍 国际网络`、`REJECT` 等。

---

## 4. 「如何判定需要」落地步骤

```
App catalog (surge_interest=true)
  → 提取 vendors[] / 名称关键词 / 已知 suffix
  → 合并 conf + patches/*.list + manifest（补 finance / AI / TikTok / DIRECT 例外）
  → 生成/维护 interest_seed（正式：interest_seed.json；溯源：interest_seed_from_apps.json）
  → 按 policy_hint / policy_tags 映射到 upstream_watch 的 category
       ai → skk-ai / gitlab
       stream* → stream / stream_us / …
       reject/ads → reject*（仅兴趣命中）
       direct/domestic → direct / domestic / apple（frozen 为主）
       finance → 主要靠自有 list + 主配置内联；上游无独立 finance 文件时不臆造整包
  → 对 frequent 上游新增行跑 selectors（P1–P5）
  → auto_pr_high → curated list 草案 + PR；review → candidates；else ignore
```

**覆盖率声明**：App 清单种子 **非 HAR**，域名覆盖有限；宁可漏吸也不要无关联海量写入。

---

## 5. 规则更新要求（MUST / SHOULD）

### MUST

1. **Watch 面**：仅 `patches/upstream_watch.yaml` 中主配置已引用的路径；frequent 每日两次；frozen 不每日全量同步。
2. **选择器阈值**：遵守 `selectors.yaml` 的 P1–P5 与 `budgets`（`max_auto_per_file≤15`，`max_auto_per_day≤40`，`max_review_per_file≤50`）；无关联 reject 默认 `ignore`。
3. **冲突门禁**：拟进 ads/reject 但命中 `allow_policy_hosts`（AI / TikTok / 金融 / DIRECT 业务域）→ 强制 `review`，标注 `conflict_with_allow`；`reject_interest`（pangle 等）不得进放行 list。
4. **单次新增上限**：单文件 / 单日 auto 写入不得超过 budgets；超额降级为 review 或只报告；**禁止**「同步整个 reject」。
5. **PR only（默认）**：`--mode pr`；不得无条件覆盖生产 raw/CDN；`auto_merge_high_confidence` 默认 `false`。
6. **manifest 字段**：每条真实规则至少含 `id, file, rule, policy, source, evidence_type, first_seen, last_verified, expires, notes`；兴趣自动吸收用 `evidence_type=interest-auto`（或等价）；占位条可 `status=placeholder`。
7. **回归 App 子集**：每次候选/PR 至少对照高频 App（从清单挑选）：微信、支付宝、哔哩哔哩、酷安、小红书、淘宝/京东、Claude、ChatGPT、TikTok、YouTube、招商银行/云闪付（银行类代表）、以及 conf 保留的 OKX/Bybit 回归项；pangle → REJECT 不放行。
8. **种子来源标记**：运行产物与 PR 说明须注明「当前种子：App 清单（2026-09-16）；请求日志暂缺」。

### SHOULD

- 财务第 2 页已在 V6.0 catalog 补全（OKX/Bybit/…/Wise/Authenticator）；银行类仍保守 DIRECT，Authenticator 不编造未核实域名。
- Google / YouTube 规则顺序变更需人工审阅，机器人不重排主配置段落。
- 流媒体强相关默认 `review`，不默认新建大型自有 stream list（与 `category_target` 一致）。
- 国内 AI（DeepSeek / 豆包 / 千问等）默认 DIRECT/domestic 兴趣，**不要**自动并入 `ai-critical.list`（该 list 面向海外 AI 住宅出口冲突例外）。

---

## 6. 风险说明

### 6.1 财务软件文件夹缺页

V6.0：财务软件第 2 页九项已写入 `finance_page2_apps`（欧易 OKX、Bybit、Bybit EU、UU Wallet、Plasma One、Bitget Wallet、PayPal、Authenticator、Wise）。  
**剩余风险**：银行/证券类仍以第 1/3 页与 DIRECT 兴趣为主；Authenticator 仅按 Google Authenticator 假设绑定 Google/AI 登录亲和，无独立未核实域名。  
**缓解**：不臆造域名；回归覆盖财务第 2 页 + 微信/支付宝等。

### 6.2 国内 / 国际版并存

| 国内 | 国际 | 风险 |
|------|------|------|
| 抖音 | TikTok | 共用字节系 CDN/归因时，误把广告域放行或把 TikTok 业务打进 reject |
| 微信 / QQ | 海外社交（Instagram / X / Facebook） | 关键词过宽（如 `qq`/`byte`）导致误匹配 |
| 网易云等 | 国际流媒体 | 勿把 domestic 兴趣写入 stream 放行 |

**缓解**：vendor 使用精确商标签；TikTok 与抖音分列；`tiktokpangle*` 固定 `reject_interest`。

### 6.3 日志不可用带来的覆盖缺口

无 HAR 时无法用真实失败域做 evidence；`evidence_type=har` 的历史条目保留，新条目以 `interest-auto` / `preventive` / 人工 `official` 为主，PR 中应标明置信度。

---

## 7. 分阶段计划

| 阶段 | 内容 | 完成标准 |
|------|------|----------|
| **Phase 0** | 本规格 + `app_catalog.yaml` + 矩阵 + 文档种子来源声明 | 文档与 catalog 入仓；conf 业务规则未改 |
| **Phase 1** | catalog（含财务第2页）→ 正式 `interest_seed.json`（from_apps 作溯源） | 种子含 vendors/keywords/suffixes/policy_tags/reject_interest；覆盖率注释明确 |
| **Phase 2** | 定时 `daily_patch_bot.py --mode pr --fetch-upstream`（09:00/21:00） | 仅兴趣命中进 candidates/PR；回归子集通过；无整包 reject |
| **Phase 3**（可选） | `auto_merge_high_confidence: true` 仅对无冲突 `auto_pr_high` | 默认仍建议人工 merge；可随时关闭 |

---

## 8. 与现有文件的对齐

| 文件 | 角色 |
|------|------|
| `docs/INTEREST_MODEL.md` | 判定算法权威说明；种子来源已改为 App 清单优先 |
| `docs/MAINTENANCE.md` | 日程、发布门禁、禁止项 |
| `docs/APP_POLICY_MATRIX.md` | 文件夹/App → 出口 → list / watch → 是否吸收 reject 增量 |
| `patches/app_catalog.yaml` | 结构化 App 兴趣目录 |
| `patches/interest_seed.json` | **正式**生产种子
| `patches/interest_seed_from_apps.json` | 溯源草案（可选） |
| `patches/upstream_watch.yaml` | watch 面 |
| `patches/selectors.yaml` | 阈值与映射 |

---

## 9. 验收清单（规划交付）

- [x] `BOT_REQUIREMENTS.md` 含输入假设、目标/非目标、映射原则、MUST/SHOULD、判定落地、风险、分阶段
- [x] `app_catalog.yaml` 含 cn/intl/system 与 `from_config_not_on_homescreen`
- [x] `interest_seed.json` 正式版 + `interest_seed_from_apps.json` 溯源「非 HAR」
- [x] 财务第 2 页九项写入 catalog
- [x] INTEREST_MODEL / MAINTENANCE 声明当前种子来源
- [x] `APP_POLICY_MATRIX.md` 一页矩阵
- [x] V6.0 主配置仅升版号/RULE-SET URL/模块名；业务分流行为对齐 V5.3


---

## 10. Actions 时区（V6.0）

- Cron（UTC）：`0 1,13 * * *` → Asia/Shanghai **09:00** 与 **21:00**
- 命令：`python3 scripts/daily_patch_bot.py --mode pr --fetch-upstream`
- 鉴权：`GITHUB_TOKEN` 开 PR；无候选 → exit 0（no-op）
