# surge-V3.0.0 routing and exits

[Profile](../profiles/surge-V3.0.0.conf) · [App matrix](APP_POLICY_MATRIX.md) · [Audit fixes](REVIEW_FIXES.md) · [Maintenance](MAINTENANCE.md)

The v4 namespace is retained by compiler 4.1.1. There are 24 mounted resources: eleven protection RULE-SETs, one dedicated storm RULE-SET, one ad DOMAIN-SET, and eleven functional RULE-SETs. ads.list remains a compatible legacy export and must match ads.domainset exactly.

Dedicated ads-storm.list uses REJECT-DROP,pre-matching before all ordinary rules, including allow rules. Physical exclusion of all current and historical protection is the safeguard; ordinary whitelist order cannot override it. Ordinary first-match order: local foundation → protected business → ads.domainset (REJECT) → app functions → CN/GEOIP/FINAL. Categories: paypal, wise, binance, okx, ai, tiktok, stream, google, uk, global, cn.

- PayPal: fixed select, original US residential node by default.
- Wise/Binance/OKX: separate fixed selects, original Taiwan residential node by default.
- AI/TikTok: separate US residential fallback groups.
- Streaming: streaming Smart.
- Google: account select, following the actual AI group by default, aligning login/OAuth/Gmail/Drive/search. AI Studio has a precise AI exception; YouTube media remains streaming.
- UK: UK fallback. Global/Meta: international Smart. CN: DIRECT.

Proxy is empty and IPv6 disabled; add authorized nodes and check actual geography. Node labels do not prove the exit. A manual change to the Google select changes default identity consistency.

The inventory contains 164 records: original 160 plus four user-requested financial additions, 114 sources and 28 dependencies. Thirteen unresolved and five local-only records retain explicit gaps. Sources do not prove full app coverage.

All 67 legacy allow entries have a migration check. Historical protections remain compatible with asynchronous downloads. The 233 WeChat numeric substring rules intentionally become exact /24 networks; source text and corrections remain in provenance. Output correction is separate from the accepted raw-source change baseline.

report.json holds 210 static probes, correction and migration evidence. sources.lock.json pins sources; source-rules.json holds their semantic baseline. SHA256SUMS covers 25 data files: 24 RULE-SET exports, including compatible ads.list and dedicated ads-storm.list, plus the ad DOMAIN-SET. 64 engine/health and 9 mirror regression checks do not replace phone validation.

Legacy v6.x profiles, modules, mirrors and patch scripts remain for compatibility. Their automatic writers are manual-only and no longer the installation path.
