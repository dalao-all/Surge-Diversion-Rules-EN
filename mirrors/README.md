# Legacy mirrors and compatibility data

**Current installation:** [surge-V3.0.0.conf](../profiles/surge-V3.0.0.conf). **Current runtime rules:** [dist/v4](../dist/v4). **Current maintenance:** [MAINTENANCE.md](../docs/MAINTENANCE.md).

This directory preserves older URLs and historical inputs for existing v6.x consumers. It is not the active routing layer for the V3.0.0 profile. Do not replace the new profile's resource URLs with these archived mirrors.

## Preserved directories

- `skk/`: historical upstream SKK snapshots, retaining their upstream relative paths and source maps. A cached file is not evidence of a fresh successful upstream fetch.
- `owned/`: the older curated reject layer produced by the Option A interest/tombstone pipeline. Its counts and app scope belong to that historical pipeline.
- `scripts/`: helper scripts used by archived AdBlock modules. V3.0.0 does not require installing those modules.
- `blackmatrix7/`: historical list references retained for comparison and compatibility.

Source-map files record provenance where available. Retaining a legacy URL does not mean the legacy updater remains an active scheduled publisher. The current canonical build and verified English mirror are described in the maintenance guide.

The active engine tracks app/source/dependency manifests and publishes 15 `dist/v4` resources with source locks, provenance and static probes. It does not interpret this directory's old lists as the current 160-app coverage matrix.
