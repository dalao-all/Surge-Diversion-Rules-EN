# Your Subscription Surge V6.0 — Getting started

Timezone: “09:00 / 21:00 daily” means **Asia/Shanghai (UTC+8)**.  
GitHub Actions cron (UTC): `0 1,13 * * *` = 09:00 / 21:00 Beijing time.

> Disclaimer: for technical exchange and personal study only — not a proxy service. Follow local law and platform terms.

## What you need

1. **Surge iOS / Mac** installed
2. A Surge-compatible node subscription **you already own**
3. (Optional) a GitHub account to fork this project or enable Actions

## Install

### 1. Import the main profile

Download and import [`profiles/Your-Subscription-Surge-V6.0.share.conf`](../profiles/Your-Subscription-Surge-V6.0.share.conf) that I provide.

### 2. Replace the subscription placeholder (required)

The main profile contains:

```text
📦 Your Subscription = select, policy-path=https://subscription.example.invalid/REPLACE_WITH_YOUR_SUBSCRIPTION, update-interval=-1
```

Replace that URL **in full** with your own subscription. Replace `your-subscribe-host.example` with your subscribe host if needed.

**Security:**

- **Never** commit configs that contain real tokens to public GitHub
- Share profiles in my public repos always stay desensitized
- After forking, keep real subscriptions local or private — do not push tokens in PRs

Then manually refresh「📦 Your Subscription」in Surge and confirm the node list is non-empty.

### 3. Install the AdBlock module

Enable [`profiles/Your-Subscription-AdBlock-V6.0.sgmodule`](../profiles/Your-Subscription-AdBlock-V6.0.sgmodule).  
It covers precise Bilibili/Coolapk splash and Taobao/JD/Xiaohongshu/Amap rewrites; it does **not** expand to “MITM all hostnames”.

### 4. Trust the CA (only if the module must decrypt HTTPS)

Do not leave “Capture traffic” or “MITM all hostnames” on for daily use.

### 5. Confirm patches RULE-SET

The main profile references six owned lists **before** SKK reject bases (default raw → `patches/` on the canonical public repo, `update-interval=86400`).  
You may switch to local relative paths, e.g. `RULE-SET,patches/ai-critical.list,"🤖 AI住宅",update-interval=86400`.

Run Surge’s config check and fix any errors.

### 6. Optional: GitHub Actions

Enable `your-subscription-interest-bot` (see `docs/github-actions/` example): runs at 09:00 / 21:00 Asia/Shanghai for interest-driven patch candidates. Review before merge.

## Daily notes

| Do | Why |
|----|-----|
| Avoid global MITM | This design is light MITM |
| Avoid always-on traffic capture | Battery / certificate pain |
| Never commit real subscription tokens | Leak = stolen nodes |
| Do not vendor entire upstream mega-lists | This project only maintains small owned patches |
| Do not manually allowlist pangle ad hosts | Let the ad sets reject them |

More: [`RULES_OVERVIEW.md`](RULES_OVERVIEW.md) · [`MAINTENANCE.md`](MAINTENANCE.md) · [`INTEREST_MODEL.md`](INTEREST_MODEL.md) · [`APP_POLICY_MATRIX.md`](APP_POLICY_MATRIX.md)

Chinese twin repo: https://github.com/dalao-all/Surge-Diversion-Rules
