#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rebuild mirrors/owned reject* from mirrors/skk with tombstones stripped (Option A).

Idempotent. Reads patches/tombstones.yaml; writes mirrors/owned/List/{domainset,non_ip}/reject*.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOMB = ROOT / "patches" / "tombstones.yaml"
SKK = ROOT / "mirrors" / "skk" / "List"
OWNED = ROOT / "mirrors" / "owned" / "List"

REJECT_FILES = [
    ("domainset", "reject.conf"),
    ("domainset", "reject_extra.conf"),
    ("domainset", "reject_phishing.conf"),
    ("non_ip", "reject.conf"),
    ("non_ip", "reject-drop.conf"),
    ("non_ip", "reject-no-drop.conf"),
]

HEADER = (
    "# owned curated reject for V6.1\n"
    "# source was SKK mirror; tombstones applied\n"
    "# do not whole-replace from upstream without tombstone filter\n"
)


def load_tombstone_hosts(path: Path) -> set[str]:
    hosts: set[str] = set()
    if not path.exists():
        raise SystemExit(f"missing {path}")
    in_ds = False
    for ln in path.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if s.startswith("reject_domainset:"):
            in_ds = True
            continue
        if in_ds:
            if s.startswith("-"):
                # - ".ynuf.aliapp.org" or - ynuf...
                v = s[1:].strip().strip('"').strip("'")
                if v:
                    hosts.add(v)
            elif s and not s.startswith("#") and not s.startswith("-"):
                # next top-level key
                if ":" in s:
                    break
    return hosts


def strip_line(line: str, hosts: set[str], is_ruleset: bool) -> bool:
    """Return True if line should be stripped."""
    s = line.strip()
    if not s or s.startswith("#"):
        return False
    if s in hosts:
        return True
    bare = {h.lstrip(".") for h in hosts}
    if not is_ruleset:
        return False
    m = re.match(r"^(DOMAIN|DOMAIN-SUFFIX),([^,\s]+)", s, re.I)
    if not m:
        return False
    host = m.group(2).strip()
    if host in hosts or host.lstrip(".") in bare:
        return True
    return False


def rebuild() -> int:
    hosts = load_tombstone_hosts(TOMB)
    total_stripped = 0
    for kind, name in REJECT_FILES:
        src = SKK / kind / name
        dst = OWNED / kind / name
        if not src.exists():
            print(f"SKIP missing {src}", file=sys.stderr)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        is_ruleset = kind == "non_ip"
        out = [HEADER]
        stripped = 0
        for line in src.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True):
            raw = line.rstrip("\n\r")
            if strip_line(raw, hosts, is_ruleset):
                stripped += 1
                continue
            out.append(line if line.endswith("\n") else line + "\n")
        dst.write_text("".join(out), encoding="utf-8")
        total_stripped += stripped
        print(f"{kind}/{name}: stripped={stripped} -> {dst}")
    print(f"total_stripped={total_stripped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(rebuild())
