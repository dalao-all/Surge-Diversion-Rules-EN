[Chinese repository](https://github.com/dalao-all/Surge-Diversion-Rules) · English

# Surge V3.0.0 · Fixed routing, maintained rules

A public Surge profile and an auditable rules pipeline. Keep eleven routing categories on your device; maintain app sources, business exceptions and advertising rules in GitHub.

**Start with [surge-V3.0.0.conf](profiles/surge-V3.0.0.conf).** The public profile sets `ipv6 = false` and has an empty `[Proxy]` section. Add your own authorized nodes and check the named fallback members before importing. The download alone does not provide working proxy access.

[Download profile](https://raw.githubusercontent.com/dalao-all/Surge-Diversion-Rules-EN/main/profiles/surge-V3.0.0.conf) · [Setup guide](docs/GETTING_STARTED.md) · [Project page](index.html) · [Routing map](rule-map.html)

## What is current

- **164 app records:** 132 CN and 32 international records, with stable IDs and explicit coverage states. There are 13 unresolved identities/services and 5 local-only records. No app is marked fully covered or validated on a phone.
- **114 declared sources and 28 shared dependencies.** A source is evidence for candidate rules, not proof of complete app coverage.
- **24 runtime resources:** eleven `protect-*.list` files, `ads-storm.list`, `ads.domainset`, and eleven category lists in [dist/v4](dist/v4).
- **Eleven categories:** `paypal`, `wise`, `binance`, `okx`, `ai`, `tiktok`, `stream`, `google`, `uk`, `global`, `cn`. AI and TikTok use US residential fallback groups; Google account traffic follows the AI group by default; ordinary Meta traffic uses international Smart routing; UK uses its UK fallback; CN uses DIRECT.

The release name is **V3.0.0**. The compiler directory `rulekit_v4` and resource path `dist/v4` are internal compatibility paths, not alternate user-facing release numbers.

## One rule authority, two repositories

The [Chinese repository](https://github.com/dalao-all/Surge-Diversion-Rules) is the canonical source and builds rules daily at **05:37 Beijing time**. This English repository mirrors verified canonical data and provides English documentation; it does not independently fetch and reinterpret upstream rules. Profile RULE-SET URLs intentionally use the canonical Chinese repository so both editions consume one authority.

The English mirror is scheduled at **06:07 Beijing time**, with a **21:17** health check. Each repository uses its own `GITHUB_TOKEN`; no PAT or cross-repository write is needed. GitHub schedules can be delayed; a configured schedule does not prove a successful run. Inspect [Actions](https://github.com/dalao-all/Surge-Diversion-Rules-EN/actions) for actual results.

## Read and maintain

- [Install and validate on your device](docs/GETTING_STARTED.md)
- [Rule order and policy intent](docs/RULES_OVERVIEW.md)
- [All 164 apps and their coverage](docs/APP_POLICY_MATRIX.md)
- [Maintenance, evidence and rollback](docs/MAINTENANCE.md)
- [Compiler reference](rulekit_v4/README.md)
- [Published report](dist/v4/report.json) and [machine-readable repository status](repository-status.json)

The routing probe suite contains **210 static probes**; consult the current build output for unit-test results. Static checks do not establish app login, payments, playback, node geography, or phone performance. Rule totals change with verified source updates; use the current report rather than an old fixed total.

## Compatibility archive

Older v6.x profiles, modules, `patches/`, and `mirrors/` remain available for existing consumers. They are not the installation path for V3.0.0. Historical interest-bot documents describe a superseded design; current maintenance is documented above. Existing legacy URLs are preserved rather than silently repurposed.

This repository contains no private node credentials or subscription secrets. Upstream data retains its own licenses and attribution; see [rulekit_v4/licenses](rulekit_v4/licenses) and the source manifests.

## This audit refresh

The original 160-app list was explicitly extended with PayPal, Wise, Binance and OKX (164 total). There are 24 runtime resources: eleven protected sets, ads-storm.list, ads.domainset, eleven functional sets. Four fixed financial selects and a Google account select replace unstable generic routing. See [verified fixes and phone acceptance plan](docs/REVIEW_FIXES.md). The historical ads.list export remains compatible.

[iPhone request-burst and download troubleshooting](docs/IOS_TROUBLESHOOTING.md).
