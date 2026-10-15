# Rule engine reference · internal v4 path

The current public release is **[Surge V3.0.0](../profiles/surge-V3.0.0.conf)**. `rulekit_v4` and `dist/v4` remain internal compatibility paths. Start with [setup](../docs/GETTING_STARTED.md); this directory does not provide proxy nodes.

## Manifest and outputs

- `apps.json`: 164 stable app IDs, identity/coverage evidence, category references and 28 shared dependencies.
- `sources.json`: 114 declared source inputs and attribution.
- `protection.json`: reviewed, minimal business exceptions.
- `../dist/v4/protected-history.json`: accumulated protection needed for mixed downloaded generations.
- `custom/`: explicitly registered local source lists; an unreferenced file is not automatically built.
- `probes.json`: real known hosts with expected static routing results.
- `data/` and `licenses/`: pinned parsing reference data and source notices.

The engine publishes eleven `protect-*.list` files, `ads-storm.list`, `ads.domainset` and eleven category lists under `dist/v4`, together with hashes, source locks, report, semantic baselines and compressed provenance. Categories are `paypal`, `wise`, `binance`, `okx`, `ai`, `tiktok`, `stream`, `google`, `uk`, `global`, `cn`. Google maps to its account select group, following AI by default. Ordinary business protection precedes the full advertising set. The dedicated storm list uses `REJECT-DROP,pre-matching`, which takes precedence over ordinary allow rules; generation therefore excludes all current and historical protection and retains only exact hosts still matched by the final advertising data.

## Build and inspect

```sh
python3 -m unittest discover -s rulekit_v4 -p test_build.py -v
python3 rulekit_v4/build.py
python3 rulekit_v4/validate_release.py
```

The engine uses Python's standard library and git. An initial online build needs network access. Use `build.py --offline` only with a previously verified complete local cache; the cache is not committed. First publication is subject to the bootstrap review baseline; subsequent builds compare against published per-source semantics.

The current probe suite contains 210 static probes; consult the current build output for unit-test results. Static checks do not prove device behavior or complete app coverage. The [matrix](../docs/APP_POLICY_MATRIX.md) includes 13 unresolved records and 5 local-only records; none of the 164 apps has phone acceptance or complete coverage recorded.

## Canonical maintenance and mirror

The [Chinese repository](https://github.com/dalao-all/Surge-Diversion-Rules) fetches upstreams at 05:37 Beijing time. This English repository mirrors verified canonical data at 06:07 and checks health at 21:17. It uses its own repository token and does not write to the canonical repository. Profile RULE-SET links deliberately continue to point at the canonical authority.

Required-source errors, unsafe semantic changes and failed probes stop publication. Review large legitimate migrations rather than bypassing checks. Keep protection history during rollback and restore all related artifacts together. Read [MAINTENANCE.md](../docs/MAINTENANCE.md) for source changes, evidence and device acceptance.

Upstream data retains its own licenses and attribution. Older `mirrors/`, `patches/` and v6.x artifacts are compatibility archives, not current engine inputs unless explicitly registered in the current source manifest.

[iPhone request-burst and download troubleshooting](../docs/IOS_TROUBLESHOOTING.md).
