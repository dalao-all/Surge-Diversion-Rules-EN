# mirrors/owned — Option A (V6.1)

Runtime `reject*` DOMAIN-SET / RULE-SET references in Surge conf point here (`mirrors/owned/List/...`), not at SKK.

- **`mirrors/skk`**: upstream cache only — for diff / refresh / comparison. Do **not** use SKK `reject*` directly at runtime if you want Alipay (and other) tombstones to stick.
- **`mirrors/owned`**: curated copy of SKK `reject*` with `patches/tombstones.yaml` hosts stripped. Rebuild with `scripts/apply_tombstones_owned.py`.
- **Never** whole-replace owned from upstream without applying the tombstone filter.
- Interest absorb / daily bot must **skip** tombstoned hosts (never re-add into owned reject or ads-patch).

Promoted hosts (e.g. `ynuf.aliapp.org`, `amdc.alipay.com`) live in `patches/direct-patch.list` as DIRECT exceptions ahead of owned reject.
