# Historical owned reject lists · Option A

> **Legacy compatibility directory.** Use [surge-V3.0.0.conf](../../profiles/surge-V3.0.0.conf), [current rule order](../../docs/RULES_OVERVIEW.md) and [current maintenance](../../docs/MAINTENANCE.md). The V3.0.0 profile consumes `dist/v4`; it does not mount these lists.

This directory preserves curated reject resources previously used by v6.1 profiles. The old pipeline filtered upstream reject candidates through app-interest seeds, tracker mappings and tombstones. It excluded broad short-substring matches and kept a restricted phishing-brand scope. Those historical rules and source maps remain for old consumers; they do not establish complete app coverage or current upstream freshness.

The legacy app inventory and its former 121-app scope have been superseded for current maintenance by the [160-record manifest](../../rulekit_v4/apps.json) and [coverage matrix](../../docs/APP_POLICY_MATRIX.md). Do not combine the two counts or present the older snapshot as the present catalog.

Scripts associated with this directory remain archived in the repository for traceability. Do not run the legacy owned-list rebuild as the V3.0.0 publication process. Current business-protection history, advertising conflict removal, per-source locks and static probes belong to `rulekit_v4` and its canonical pipeline.
