# 兴趣判定模型（Interest Model）

> ## 当前种子来源（2026-09-16）
>
> - **主种子**：iPhone App 分类清单 → `patches/app_catalog.yaml` → 正式 `patches/interest_seed.json`（溯源见 `interest_seed_from_apps.json`）。
> - **补充**：现有 `MESL-Surge-V6.0.conf` / `patches/*.list` / `manifest.json`（含清单未出现的 OKX/Bybit/PayPal 等 finance 兴趣）。
> - **请求日志暂缺**：用户无法提供 Surge 长期请求记录；已核实导出 zip 为 **PacketTunnelProvider/SGLog 应用日志**，**不可作域名种子**。
> - 规格见 `docs/BOT_REQUIREMENTS.md`；矩阵见 `docs/APP_POLICY_MATRIX.md`。
> - **非 HAR，覆盖率有限** — 只吸收与已安装 App / 已启用策略组相关的上游增量。

回答核心问题：**如何提前判定「我需要的规则」**，而不是整包同步上游。

时区：Asia/Shanghai。本模型供 `scripts/daily_patch_bot.py` 与人工审阅共用。

---

## 0. 一句话

只 watch 主配置已引用的上游路径 → 对**新增行**做分层相关性打分 → 强相关进自有 list（默认开 PR）→ 中相关只报告 → 无关联丢弃。  
**禁止**同步整个 `reject.conf` / AllInOne / Loyalsoldier。

---

## 1. 分层输入

### 1.1 种子 `interest_seed`（你是谁）

来源（按优先级合并；**当前以 App 清单为主**，conf/patches 补缺；HAR 暂缺）：

| 来源 | 提取什么 |
|------|----------|
| 主配置 `MESL-Surge-V6.0.conf` 内联 DOMAIN* | 已用域名、后缀、关键词、策略组标签 |
| `patches/*.list` | 已固化自有例外（AI/金融/DIRECT/ads） |
| `patches/manifest.json` | evidence / notes / VENDOR 线索 |
| iPhone App 分类清单 → `app_catalog.yaml` | **当前主种子**（2026-09-16）；系统 App 排除 |
| 可选 HAR / Surge 请求日志导出 | **暂缺**（SGLog zip 不可用）；有则补真实域/频次 |

种子字段示例见 `patches/interest_seed.json`（正式生产种子；`interest_seed.example.json` / `interest_seed_from_apps.json` 为辅助）：

- `domains`：精确域
- `suffixes`：后缀
- `keywords` / `vendors`：关键词与厂商标签（anthropic、okx、appsflyer…）
- `policy_tags`：策略组（AI住宅、数字资产、TikTok、REJECT、DIRECT…）
- `allow_policy_hosts`：业务放行域集合（冲突门禁用）
- `reject_interest`：明确应进广告/拒绝兴趣的域（如 tiktokpangle*）

可用 `python3 scripts/export_interest_seed.py` 从主配置粗提取草案，再人工修订。

### 1.2 上游订阅面 `upstream_watch`（看哪里）

**只**列出主配置真正 `RULE-SET` / `DOMAIN-SET` 引用的 SKK（等）路径，见 `patches/upstream_watch.yaml`。

两类：

| 类别 | 含义 | 维护方式 |
|------|------|----------|
| `frequent` | 变化快、影响大（ai / reject* / stream_* 等） | 每天 09:00 与 21:00 拉取 diff |
| `frozen` | 不怎么变（apple_*、domestic、china_ip 等） | 一次性抓全 → 固化为手动 list 或极少更新；日常 bot **不**全量同步 |

IP 规则集默认不进「域名兴趣」流水线（可单独记哈希，不做域筛选）。

### 1.3 选择器 `selectors`（怎么判）

见 `patches/selectors.yaml`。按**优先级从高到低**匹配，命中即停并给出动作建议。

---

## 2. 相关性选择器（可执行）

对上游某文件的**新增规范化规则** `R`（类型 + host），依次：

### P1 — exact / suffix / parent-suffix 命中种子

- `DOMAIN,host` 且 `host ∈ seed.domains` → **强相关**
- `DOMAIN-SUFFIX,sfx` 且（`sfx ∈ seed.suffixes` 或 某 seed 域以 `.sfx` 结尾）→ **强相关**
- 新增 `DOMAIN,a.b.c` 且存在种子 `DOMAIN-SUFFIX,b.c` 或 `DOMAIN,b.c` → **强相关**（parent-suffix）
- 新增后缀覆盖了已有种子精确域 → **强相关**（需标 `covers_seed`）

**动作**：`auto_pr_high`（默认写对应自有 list + PR；可配置高置信 auto-merge）

### P2 — 同注册域（eTLD+1）新子域

- 取 host 的 eTLD+1（启发式：常见多段 TLD 如 `com.cn` / `co.uk`，否则末两段）
- 若该 eTLD+1 已出现在种子 domains/suffixes → **强～中相关**

例：种子有 `api.anthropic.com`，上游新增 `console.anthropic.com` → 同 `anthropic.com` → 高相关，目标 list=`ai-critical`（若上游文件属 ai 类）或仅报告（若来自 reject 类则进冲突审阅，见 §4）。

**动作**：默认可 `auto_pr_high`（同厂商业务文件）或 `review`（来自 reject 海量文件时降级）

### P3 — 关键词 / 厂商命中

配置项（`selectors.yaml` → `vendor_keywords`），例：

- `anthropic` / `claude` / `openai` / `siftscience` / `statsig` → AI
- `okx` / `okex` / `bybit` / `tobsnssdk` → finance
- `appsflyer` / `appsflyersdk` 前缀 → 按已有策略：金融 AppsFlyer 进 finance；TikTok 两条精确域进主配置 TikTok，**不是**自动进 finance
- `tiktokpangle` / `pangle`（广告）→ **reject/ads 兴趣**，不是 TikTok 放行

匹配方式：host 包含关键词，或 DOMAIN-KEYWORD/WILDCARD 模式命中。

**动作**：`auto_pr_high` 或 `review`（由 `confidence` 字段控制）

### P4 — 上游文件类别 ∈ 用户启用类别，且与种子有弱关联

- 文件 `category`（ai / reject / stream_us / direct / …）在 `enabled_categories`
- 「弱关联」：host 与任一种子后缀共享**至少一段非公共标签**（长度≥4 的 label，排除 `com`/`net`/`org`/`cdn`/`api` 等停用词），或同 `vendor` 标签

**动作**：`review`（只报告，不自动写入）

### P5 — 默认丢弃

- 无关联的海量 reject / global 新域
- 未启用类别
- 超过每日/每文件新增上限后的剩余项（见 §3）

**动作**：`ignore`

---

## 3. 动作分级与负担控制

| 动作 | 含义 | 仓库结果 |
|------|------|----------|
| `auto_pr_high` | 强相关新增 | 写入候选 → 合并进对应自有 `patches/*.list` 草案 + 生成 PR 说明（默认可人工 merge；`auto_merge_high_confidence: true` 时可配置直接 push） |
| `review` | 中相关 | 仅写入 `patches/candidates/review-YYYYMMDD.json`，不开自动合并 |
| `ignore` | 不相关 | 计数后丢弃；摘要里可保留 top-N 样例 |

负担控制（`selectors.yaml` → `budgets`）：

- `max_auto_per_file`（默认 15）
- `max_auto_per_day`（默认 40）
- `max_review_per_file`（默认 50）
- 超过：其余降为 `review` 或只报告；**禁止**「同步整个 reject.conf」

---

## 4. 冲突门禁（硬规则）

新增若拟进入 `ads-patch` / reject 自有集，但 host（或后缀覆盖）命中 `allow_policy_hosts`（AI / TikTok 放行 / 金融 / DIRECT 业务域）→ **不得**写入 ads/reject 自有集，强制 `review`，并标注 `conflict_with_allow`。

反向：拟写入业务放行 list，但种子明确标了 `reject_interest`（如 pangle）→ 强制改走 ads 兴趣或 `review`。

---

## 5. tiktokpangle 专例（必读）

| 域 | 正确兴趣 | 错误做法 |
|----|----------|----------|
| `tiktokpangle-b.us` | reject / ads | 放进 TikTok 放行 list |
| `tiktokpangle-cdn-us.com` | reject / ads | 放在 SKK 广告底座**之后**的放行规则 |

原因：修订 2 里放在 SKK 之后的放行意图无效——流量已先被广告集 REJECT；且业务策略本应拒绝广告域。V6.0 已删除这两条无效放行；兴趣模型将其归入 `reject_interest`，不是 TikTok。

---

## 6. 目标自有 list 映射

| 兴趣 / 上游类别线索 | 写入文件 | 策略（主配置 RULE-SET） |
|---------------------|----------|-------------------------|
| AI 强相关例外 | `ai-critical.list` | 🤖 AI住宅 |
| 金融 / okx / toblog | `finance-critical.list` | 🪙 数字资产 |
| Bybit EU / Global | 对应伴生 list | 🇩🇪 / 💳 |
| 防误杀 DIRECT | `direct-patch.list` | DIRECT |
| 广告缺口 / pangle 类 | `ads-patch.list` | REJECT |

自有规则集可多个，但应**覆盖当前在用上游职责中的关键例外**，不整包复制 SKK。

---

## 7. 判定伪代码

```
for each frequent upstream file F in upstream_watch:
  new_lines = diff(prev_snapshot(F), fetch(F))
  for rule in normalize(new_lines):
    if conflicts_with_allow(rule): action = review; continue
    if hit P1 seed exact/suffix: action = auto_pr_high; target = map(F, seed)
    elif same_etld1(rule, seed): action = auto_pr_high or review  # reject 来源降级
    elif vendor_keyword(rule): action = per selectors
    elif category_enabled(F) and weak_link(rule, seed): action = review
    else: action = ignore
    apply_budgets(action)
    emit candidate / pr body
```

---

## 8. 例子

**例 A（auto_pr_high）**  
上游 `non_ip/ai.conf` 新增 `DOMAIN,mcp.anthropic.com`。  
种子含 `anthropic.com` / vendor `anthropic` → P1/P3 → 写入 `ai-critical.list` 候选 + PR。

**例 B（review）**  
上游 `reject.conf` 新增 `DOMAIN-SUFFIX,random-tracker-xyz.com`。  
与种子无交集 → ignore。若偶然与某种子 label 弱关联 → review，**不**整文件同步。

**例 C（冲突）**  
上游 reject 新增 `DOMAIN,api.anthropic.com`。  
命中 `allow_policy_hosts` → review / `conflict_with_allow`，不进 `ads-patch`。

**例 D（pangle）**  
任意上游新增 `DOMAIN-SUFFIX,tiktokpangle-b.us`。  
`reject_interest` → 兴趣归 ads/reject；若有人想写进 TikTok list → 门禁拒绝。
