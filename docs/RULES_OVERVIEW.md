# Rule layers & policy intent (Your Subscription Surge V6.0)

How I layer rules in this project, what each policy group is for, and how that maps to [`rule-map.html`](../rule-map.html).

> Technical exchange and rule-design study only. Not a proxy service. No nodes.

## 1. Why layers

Surge matches **top-down** and stops at the first hit. Critical business exceptions written after a huge ad base get false-rejected; vendoring entire upstream packs into the main conf is hard to audit.  
I therefore use four layers: the main conf keeps order and policy bindings; list bodies live as GitHub raw on this project where possible.

## 2. Four layers

```text
① patches/          Critical front exceptions (before the ad base)
② mirrors/skk/      Main diversion + ad / domestic / streaming / global indexes
③ mirrors/scripts/  AdBlock module scripts (MITM / rewrite)
④ Inline in conf    Protocol-level / precise exceptions that should not be lists
```

### 2.1 `patches/` — critical front exceptions

| File | Policy binding (main conf RULE-SET) | Intent |
|------|-------------------------------------|--------|
| `ai-critical.list` | 🤖 AI住宅 | Overseas AI / login hosts — avoid reject false positives |
| `finance-critical.list` | 🪙 数字资产 | Critical finance (e.g. OKX) front rules |
| `finance-bybit-eu.list` | 🇩🇪 Bybit 欧洲 | Bybit EU (separate list: one policy per RULE-SET file) |
| `finance-bybit-global.list` | 💳 Bybit 全球 | Bybit Global |
| `ads-patch.list` | REJECT | Ad-interest increments (e.g. pangle) |
| `direct-patch.list` | DIRECT | Domestic app compatibility (biliapi, XHS, Coolapk, …; amdc extended-matching lives in main profile) |

These RULE-SET lines must appear **before** remote SKK `reject*`. The interest bot only absorbs upstream adds related to `interest_seed` / selectors.

Metadata: `manifest.json`, `selectors.yaml`, `upstream_watch.yaml`, `app_catalog.yaml`, `interest_seed.json`.

### 2.2 `mirrors/skk/` — main index mirror

Byte-for-byte mirror from `ruleset.skk.moe`, keeping `List/domainset|non_ip|ip/...`.  
Used for ad rejects, domestic DIRECT, Apple/Microsoft, streaming regions, Telegram, global lists, China IP, etc.  
I do **not** rewrite semantics here; deltas go to `patches/` or inline. See `SOURCE_MAP.json`.

### 2.3 `mirrors/scripts/` — module script mirror

Scripts formerly pulled from fmz200 / kokoryh etc. are mirrored here and referenced by `profiles/Your-Subscription-AdBlock-V6.0.sgmodule`.  
Goal: owned, stable raw URLs — **without** expanding MITM / script scope.

### 2.4 Inline exceptions in the main conf

Kept in the conf when they belong there:

- DoH/DoT / STUN and leak controls
- Subscribe-host DIRECT (share profile uses `your-subscribe-host.example`)
- Apple stability exceptions, dead-host fast fails
- Large TikTok / Google / PayPal business blocks (some previously remote blackmatrix7 lists, now inline)
- FINAL plus GEOIP / LAN

`mirrors/blackmatrix7/` keeps historical lists for reference; the V6.0 share conf no longer RULE-SET-fetches them remotely.

## 3. Match order (aligned with the rule map)

Simplified order:

1. **Protect & clean** — DoH/DoT, STUN, captive, subscribe-host DIRECT, Apple exceptions  
2. **patches front** — AI / finance / ads / direct  
3. **SKK reject\*** — ad & phishing base  
4. **Business policies** — TikTok, AI lists, finance inline, domestic DIRECT, streaming, international  
5. **IP-level rules** — ip counterparts of non_ip lists  
6. **FINAL** — fallback (`dns-failed` aware)  

[`rule-map.html`](../rule-map.html) draws this as an EN/中文 toggleable graph; the README / `index.html` preview is `assets/rule-map-preview.png`.  
**The graph is for study; the share conf’s real RULE order wins.**

## 4. Policy-group intent

| Group | Type | Intent |
|-------|------|--------|
| 📦 Your Subscription | select + policy-path | Node-pool entry (placeholder sub — replace yourself) |
| 🤖 AI住宅 | fallback | US residential preferred; sensitive identity traffic |
| 🎵 TikTok | smart | US datacenter; exclude 0.3X and residential |
| 🪙 数字资产 | fallback | TW residential preferred (OKX / wallets / Wise, …) |
| 💳 Bybit 全球 | fallback | Bybit Global |
| 🇩🇪 Bybit 欧洲 | fallback | Bybit EU (DE-tagged nodes) |
| 🇬🇧 英国专属 | fallback | UK local services |
| 💰 PayPal | fallback | US residential preferred, UK backup |
| 🎬 流媒体 | smart | High-bandwidth regional Smart |
| 🌍 国际网络 | smart | Chat / general international |
| Hidden *residential / *DC pools | fallback + hidden | For include-other-group |

Names are **sample labels** that depend on node-name patterns in your subscription — not vendor recommendations.

## 5. Docs & scripts

| Doc / script | Role |
|--------------|------|
| `GETTING_STARTED.md` | Install + security |
| `APP_POLICY_MATRIX.md` | App → exit / list / watch |
| `INTEREST_MODEL.md` | How interest seeds filter upstream deltas |
| `MAINTENANCE.md` / `BOT_REQUIREMENTS.md` | Cadence & bot spec |
| `scripts/daily_patch_bot.py` | Fetch upstream → candidates → PR |
| `scripts/regression_cases.json` | Smoke checklist |

## 6. Security boundary

- Public trees must not contain real subscription token query params, private subscribe hostnames, or subscription fetch paths  
- Share conf uses only `subscription.example.invalid` and `your-subscribe-host.example`  
- Private subscribed configs never enter this repo  

Chinese overview: https://github.com/dalao-all/Surge-Diversion-Rules (`docs/RULES_OVERVIEW.zh.md`)
