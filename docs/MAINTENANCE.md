# Maintenance and publication

Current release: **surge-V3.0.0.conf**. Internal compiler: `rulekit_v4`. Published resources: `dist/v4`. The [Chinese repository](https://github.com/dalao-all/Surge-Diversion-Rules) is the only upstream-fetching authority; this English repository mirrors verified canonical releases.

## Scheduled responsibilities

All times here are **Beijing time / Asia-Shanghai, UTC+8**.

- Canonical build: **05:37 daily**. Fetch locked upstream inputs, compile, validate and publish only a valid result.
- English mirror: **06:07 daily**. Pull the verified canonical data and validate it before updating this repository; do not independently reinterpret upstream rules.
- Health check: **21:17 daily**. Inspect recent successful workflow activity, including the 36-hour freshness threshold used by the health workflow.

Each repository writes only to itself with its own `GITHUB_TOKEN`. No PAT and no cross-repository write are required. Legacy interest-bot schedules are superseded. Check the actual workflow files and [Actions runs](https://github.com/dalao-all/Surge-Diversion-Rules-EN/actions) when investigating failures; a schedule is not evidence that a run succeeded.

GitHub may delay scheduled runs. A health check on the same scheduler cannot detect every shared scheduler/account failure. Failure visibility depends on Actions and account notification settings; no email-delivery guarantee is made.

## Update app records, not duplicate arrays

`rulekit_v4/apps.json` is the app inventory: **164 records, 132 CN and 32 international**. It also declares **28 shared dependencies**; `sources.json` declares **114 sources**. Stable IDs preserve identity and ordering even when a display name changes.

For an addition, record the real identity/version, category, sources or dependencies, evidence and known business endpoints. With no reliable source, record the gap; do not invent domains. Turning an app's `enabled` field off removes rules used only by that app, but other apps may retain shared dependencies and FINAL still handles unknown destinations. It does not block that app from the network.

Make manifest and compiler changes in the canonical repository, then let this repository consume the verified release. An urgent phone-local change needs a later canonical evidence record so the two do not drift.

## Business exceptions and source checks

Add the smallest evidence-backed host or suffix to the appropriate category in `protection.json`. Keep `protected-history.json` so mixed generations of downloaded resources remain compatible. Do not use a whole cloud provider, bare brand keyword, or entire group as a substitute for a precise business exception.

The canonical pipeline locks one commit per upstream repository, verifies input shape and semantic changes, checks public suffixes, advertising conflicts and probes, then publishes an internally consistent artifact set. Source failure, malformed data, empty required sources, suspicious set replacement or failed critical probes stop publication. A failed run leaves the previously published files available; a phone may still need a manual resource refresh after a later success.

Review intentional large migrations through a normal audited change to the semantic baseline. Do not bypass syntax, suffix or business-protection checks. Avoid commits that only churn runtime timestamps when rule content has not changed.

## Reproduce the checks

From the repository root:

```sh
python3 -m unittest discover -s rulekit_v4 -p test_build.py -v
python3 rulekit_v4/build.py --offline
python3 rulekit_v4/validate_release.py
```

Offline rebuilding requires a previously verified complete local cache; that cache is not committed. For an initial online build, use `python3 rulekit_v4/build.py` in a suitable canonical checkout. The engine uses the Python standard library and git.

The current validation suite contains **64 engine/health tests, 9 mirror tests and 210 static probes**; export validation covers 25 data files. Read the current [report](../dist/v4/report.json) for changing counts and probe evidence. These tests check static routing semantics, not phone behavior, account eligibility, actual residential exits or app completeness.

## Inspect release evidence

- `dist/v4/report.json`: probe results, exclusions and category shadowing.
- `dist/v4/sources.lock.json`: source revisions and hashes.
- `dist/v4/source-rules.json`: per-source semantic comparison baseline.
- `dist/v4/provenance.ndjson.gz`: compressed rule-level attribution.
- `rulekit_v4/data/psl-source.json`: pinned public-suffix reference.
- `repository-status.json`: published project summary for the English landing pages.

The app matrix contains **13 unresolved** and **5 local-only** records. All 164 records still have `complete = false` and `device_validated = false`. Plan phone checks by app ID and real business action rather than interpreting the list count as acceptance.

## Rollback and device acceptance

Choose a verified release from Git history and restore its complete `dist/v4` artifact set in a new commit. Merge current protection history into that earlier state and rebuild before publication, so an old advertising file cannot reintroduce a fixed false block. Do not rewrite shared history with a forced push.

Refresh external resources on the phone and inspect all 24 downloads. Multi-file downloads are not atomic: preserve compatible protection across old/new advertising generations. Test login, payment, messaging, media, maps and AI flows on Wi-Fi and cellular, recording real hosts, first matches and exits. Static validation, publishing a commit and passing phone acceptance are separate outcomes.

## Legacy archive

The older interest model, bot specification, workflow example, v6.x profiles/modules, `patches/` and `mirrors/` are retained for compatibility and historical reference. They do not prescribe the current schedule or installation steps. [Historical bot note](BOT_REQUIREMENTS.md) · [Historical interest model](INTEREST_MODEL.md).

The dedicated `ads-storm.list` uses `REJECT-DROP,pre-matching` before every ordinary allow rule; changing ordinary rule order cannot override it. Generation retains exact hosts still covered by the final advertising data and excludes all current and historical protection; new protection automatically removes intersecting storm entries. The main profile mounts 24 resources, while export validation covers 25 data files.
