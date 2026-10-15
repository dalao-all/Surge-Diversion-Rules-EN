# Historical app-interest model

> **Legacy design record — superseded.** This was the earlier v6.x patch-selection model. The current app inventory is [rulekit_v4/apps.json](../rulekit_v4/apps.json); current routing is described in [RULES_OVERVIEW.md](RULES_OVERVIEW.md), and publication in [MAINTENANCE.md](MAINTENANCE.md).

## Earlier inputs and intent

The September 2026 design used an iPhone app catalog as its main interest seed. Existing inline profile rules, `patches/`, vendor names and policy tags supplemented it. A tunnel/SGLog archive was available, but it did not contain the long-term request records needed to prove business-domain coverage.

The model asked whether an upstream addition was relevant to a known app or enabled policy group. Strong evidence could prepare a small patch; weaker associations required review; unrelated additions were ignored. Exact domains, suffixes, trusted source-path relationships and meaningful vendor identifiers carried different evidence weights. A bare short brand substring was not reliable service identity.

Shared login, payment, CDN, push and cloud domains needed special care because relevance to one app did not justify routing every tenant through that app's exit. Advertising interest was also distinct from business allow interest: Pangle remained an advertising candidate, while a verified business false block needed a precise exception.

## Limits of that model

Catalog membership was not traffic evidence. Vendor matching could include unrelated hosts. A community list could be incomplete, stale or overly broad. Browser traffic depended on destination sites, and mail traffic depended on providers and fetched content. Missing app-specific sources could not be filled by invented domains.

Earlier documents discussed scores, budgets, candidate queues and update schedules as planning tools. They should not be interpreted as current guarantees or as proof that autonomous updates completed.

## Current replacement

Stable app IDs now reference declared sources and shared dependencies. Coverage states distinguish independent candidates, shared candidates, documented services, existing-config candidates, unresolved services and local-only apps. None of the 160 records is marked complete or phone-validated. The [full matrix](APP_POLICY_MATRIX.md) preserves those distinctions.

The compiler locks source revisions, reports unsupported semantics and exclusions, checks conflicts and probes, and emits 15 auditable resources. `protection.json` plus retained protection history handles reviewed business exceptions. A deterministic canonical build and verified English mirror replace the legacy interest-only publishing design.

Historical seed and patch files are retained for old consumers. See [BOT_REQUIREMENTS.md](BOT_REQUIREMENTS.md) and Git history for the earlier proposal; use the maintenance guide for current operations.
