# 你的订阅 Surge V6.0 维护手册

> ## 当前种子来源（2026-09-16）
>
> App 清单（`patches/app_catalog.yaml` / `interest_seed_from_apps.json`）为兴趣主源；请求日志暂缺（SGLog zip 不可作域名种子）。机器人要求见 `docs/BOT_REQUIREMENTS.md`。

可执行流程。默认时区：**Asia/Shanghai**。  
兴趣判定细则见 **[INTEREST_MODEL.md](INTEREST_MODEL.md)**（本文只交代日程、上下游分工与发布门禁）。

机器人默认只开 PR；高置信可配置 auto-merge，禁止无条件覆盖生产。

---


## GitHub Actions 时区

仓库工作流 `docs/github-actions/your-subscription-interest-bot.yml.example`：

```yaml
on:
  schedule:
    - cron: "0 1,13 * * *"   # UTC → Asia/Shanghai 09:00 & 21:00
  workflow_dispatch:
```

换算：UTC 01:00 = CST 09:00；UTC 13:00 = CST 21:00。  
作业步骤：`actions/checkout` → `python3 scripts/daily_patch_bot.py --mode pr --fetch-upstream` → 使用 `GITHUB_TOKEN` 开 PR；无候选则 no-op 成功退出。

正式种子文件：`patches/interest_seed.json`（`interest_seed_from_apps.json` 仅溯源可选）。

## 原则

1. **仓库只存自有 list**：`patches/*.list` + `manifest.json` + watch/seed/selectors 配置。不整包复制 SKK / Loyalsoldier / blackmatrix7 AllInOne。
2. **兴趣驱动增量**：只吸收「与用户种子相关」的上游新增；海量无关联 reject/全球域默认丢弃。
3. **频繁 vs 固化**：
   - **频繁更新**（`upstream_watch.yaml` → `frequent`）：每天 **09:00** 与 **21:00**（Asia/Shanghai）拉取 → diff 新增 → 兴趣筛选 → 写入自有 list 候选并推仓库（默认 PR）。
   - **不怎么更新**（`frozen`）：一次性抓全 → 固化为手动维护 list（或极少更新）；日常 bot 不整包同步。
4. 自有规则集可多个，但应覆盖当前在用上游职责中的**关键例外**（AI 冲突前置、金融、DIRECT 防误杀、ads 缺口），不是第二套通用底座。
5. `finance-bybit-eu.list` / `finance-bybit-global.list` 与 `finance-critical.list` 同属 **finance-critical 家族**（因 RULE-SET 整文件一策略而拆分）。
6. 完整 Surge 配置含订阅令牌，**不进公开库**。

---

## 如何提前判定「需要哪些规则」

分层判定（摘要；完整算法与例子见 INTEREST_MODEL.md）：

1. **种子 interest_seed**：当前以 App 清单（`app_catalog.yaml`，含财务第 2 页）+ 正式 `interest_seed.json` + patches 得到已用域、后缀、关键词、VENDOR、策略组、放行/拒绝兴趣；**HAR/请求日志暂缺**。
2. **上游面 upstream_watch**：只 watch 主配置真实引用的 SKK 路径清单，不是全站 SKK。
3. **selectors 优先级**：exact/suffix/parent-suffix → 同 eTLD+1 → 关键词/厂商 → 启用类别弱关联 → 默认 ignore。
4. **动作**：`auto_pr_high` / `review` / `ignore`；预算上限；冲突则强制审阅。
5. **tiktokpangle\***：策略是交广告集拒绝 → 进 reject/ads 兴趣，**不是** TikTok 放行；放在 SKK 之后的放行规则意图无效。

配置文件：

| 文件 | 作用 |
|------|------|
| `patches/upstream_watch.yaml` | 频繁 / 固化上游路径清单 |
| `docs/BOT_REQUIREMENTS.md` | App 清单兴趣源机器人规格（MUST/非目标/分阶段） |
| `patches/app_catalog.yaml` | 结构化 App → 策略兴趣目录 |
| `patches/interest_seed_from_apps.json` | 由 catalog 推导的种子草案（非 HAR） |
| `patches/interest_seed.json` | **正式**兴趣种子（V6.0）
| `patches/interest_seed_from_apps.json` | 溯源草案（可选）
| `patches/interest_seed.example.json` | 极简示例 |
| `patches/selectors.yaml` | 选择器、预算、映射、auto-merge 开关 |

---

## 每日（两次）机器人流程

建议 cron（Asia/Shanghai）：

```cron
0 9,21 * * * cd /path/to/your-subscription-surge-v6.0 && python3 scripts/daily_patch_bot.py --mode pr --fetch-upstream >> /var/log/your-subscription-patch-bot.log 2>&1
```

### 1. 拉取频繁上游快照

- 按 `upstream_watch.yaml` 的 `frequent` 列表拉取（`--fetch-upstream`）。
- 记录内容哈希、ETag/Last-Modified、拉取时间（Asia/Shanghai）。
- 与 `patches/cache/` 上次快照 diff，得到**新增行**（默认不做整包替换）。

### 2. 规范化

- 域名小写、简易 IDNA、统一规则类型字段。
- 去掉空行噪声；保留有意义的 `#` 头注释。

### 3. 兴趣筛选（核心）

- 加载 `interest_seed.json`（若无则回退 example + 现有 patches 推导）。
- 按 `selectors.yaml` 对新增行分级：`auto_pr_high` / `review` / `ignore`。
- 写出候选到 `patches/candidates/`（不默认改生产 list，除非 `--mode apply` 且门禁通过）。

### 4. 语义去重

- 同策略下：`DOMAIN,x.y` 已被 `DOMAIN-SUFFIX,y` 覆盖 → 删除更窄条目。
- 跨策略冲突写入报警。

### 5. 冲突门禁（硬）

- 拟进 REJECT/ads 的新增若覆盖业务放行域（AI / TikTok / 金融 / DIRECT）→ **不进** ads 自有集，进审阅。
- 拟进业务放行但属 `reject_interest`（如 pangle）→ 进审阅或改 ads。

### 6. 固定回归表

对照 `scripts/regression_cases.json`，至少：

- Claude 相关域 → AI
- Google OAuth → 预期策略（主配置 scope 可跳过 patches 命中检查）
- TikTok 主域 → TikTok；**pangle 广告域 → REJECT（不放行）**
- App Store / Apple → DIRECT（SKK apple 段）
- Bilibili / 酷安关键域 → DIRECT
- 金融：`toblog` / `tobapplog` / `okex` → 数字资产；Bybit 伴生 → 对应组

### 7. 异常阈值（不发布，只报告）

- 每文件 / 每日 `auto_pr_high` 超过预算
- 删除回归表关键域
- 规则量增幅 ≳ 10%
- 试图「同步整个 reject」类操作 → 直接拒绝

### 8. 发布策略

- **默认 `--mode pr`**：写 report + PR 说明 + candidates；不改远程生产。
- `--mode apply`：显式；仍建议人工 approve 后原子发布自有 list。
- `auto_merge_high_confidence`（selectors 配置）：仅对无冲突的 `auto_pr_high` 可配置直接 push；默认关闭。
- 禁止无条件覆盖生产 raw / CDN。

### 9. 固化上游（非每日）

对 `frozen` 列表：

```bash
python3 scripts/daily_patch_bot.py --mode pr --fetch-upstream --include-frozen
# 人工挑选少量例外写入 patches/*.list 后，不再每日全量 diff（或极低频率）
```

### 10. 明确禁止

- 禁止整包拷贝 SKK / Loyalsoldier / AllInOne 入仓。
- 禁止把 STUN / iCloud Private Relay 等主配置 pre-matching 段塞进 `ads-patch.list`。
- 禁止把整个国内直连大段塞进 `direct-patch.list`。
- 禁止把 tiktokpangle 类域写入任何放行 list。

---

## 本地命令示例

```bash
# 跳过网络：本地门禁 + 回归 + 模拟 PR（CI/离线）
python3 scripts/daily_patch_bot.py --mode pr --skip-fetch

# 拉取频繁上游并做兴趣 diff（日程 09:00 / 21:00）
python3 scripts/daily_patch_bot.py --mode pr --fetch-upstream

# 从主配置粗提取种子草案
python3 scripts/export_interest_seed.py -o patches/interest_seed.draft.json

# 显式 apply（骨架仍拒绝无条件覆盖远程）
python3 scripts/daily_patch_bot.py --mode apply --fetch-upstream
```

查看参数：`python3 scripts/daily_patch_bot.py --help`

---

## manifest 字段

每条真实规则至少：`id, file, rule, policy, source, evidence_type, first_seen, last_verified, expires, notes`。  
`evidence_type`：`har` | `official` | `skk-conflict` | `preventive` | `inherited` | `interest-auto`。  
`ads-patch` 占位条可另加 `status=placeholder`。

---

## 主配置注释

主配置业务规则不变；可在 RULE-SET 前置段加注释指向本文与 INTEREST_MODEL.md，便于后人对齐维护模型。
