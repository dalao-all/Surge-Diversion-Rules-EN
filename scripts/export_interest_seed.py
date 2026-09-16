#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 Your-Subscription-Surge-V6.0.conf（及可选 patches）粗提取 interest_seed 草案。

用法：
  python3 scripts/export_interest_seed.py
  python3 scripts/export_interest_seed.py -o patches/interest_seed.draft.json
  python3 scripts/export_interest_seed.py --conf /path/to/Your-Subscription-Surge-V6.0.conf

输出为草案，需人工修订后再存为 patches/interest_seed.json。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Shanghai")
ROOT = Path(__file__).resolve().parents[1]

DOMAIN_RE = re.compile(
    r"^(DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD|DOMAIN-WILDCARD)\s*,\s*([^,\s]+)(?:\s*,\s*(.*))?$",
    re.IGNORECASE,
)


def now_date() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d")


def parse_conf(path: Path) -> dict:
    domains, suffixes, keywords, wildcards = set(), set(), set(), set()
    policy_tags = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = DOMAIN_RE.match(s)
        if not m:
            continue
        rtype, host, rest = m.group(1).upper(), m.group(2).strip().lower(), (m.group(3) or "")
        # 跳过 URL 型 RULE-SET 行误伤（不应匹配）
        if host.startswith("http"):
            continue
        if rtype == "DOMAIN":
            domains.add(host)
        elif rtype == "DOMAIN-SUFFIX":
            suffixes.add(host)
        elif rtype == "DOMAIN-KEYWORD":
            keywords.add(host)
        elif rtype == "DOMAIN-WILDCARD":
            wildcards.add(host)
        # 策略标签：尾部引号或已知词
        if rest:
            # "🤖 AI住宅" or DIRECT or REJECT
            qm = re.search(r'"([^"]+)"', rest)
            if qm:
                policy_tags.add(qm.group(1))
            else:
                pol = rest.split(",")[0].strip()
                if pol and not pol.startswith("update-") and "extended" not in pol and "pre-matching" not in pol and "no-resolve" not in pol:
                    if pol in ("DIRECT", "REJECT", "REJECT-DROP", "REJECT-NO-DROP") or not pol.startswith("http"):
                        if len(pol) < 40 and "://" not in pol:
                            policy_tags.add(pol)
    return {
        "domains": sorted(domains),
        "suffixes": sorted(suffixes),
        "keywords": sorted(keywords),
        "wildcards": sorted(wildcards),
        "policy_tags": sorted(policy_tags),
    }


def absorb_patches(patches_dir: Path, draft: dict) -> None:
    domains, suffixes, wildcards = set(draft["domains"]), set(draft["suffixes"]), set(draft["wildcards"])
    for p in patches_dir.glob("*.list"):
        for line in p.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            m = DOMAIN_RE.match(s)
            if not m:
                continue
            rtype, host = m.group(1).upper(), m.group(2).strip().lower()
            if rtype == "DOMAIN":
                domains.add(host)
            elif rtype == "DOMAIN-SUFFIX":
                suffixes.add(host)
            elif rtype == "DOMAIN-WILDCARD":
                wildcards.add(host)
    draft["domains"] = sorted(domains)
    draft["suffixes"] = sorted(suffixes)
    draft["wildcards"] = sorted(wildcards)


def main() -> int:
    ap = argparse.ArgumentParser(description="Export rough interest_seed from Surge conf + patches")
    ap.add_argument("--conf", type=Path, default=ROOT / "profiles" / "Your-Subscription-Surge-V6.0.conf")
    ap.add_argument("-o", "--output", type=Path, default=ROOT / "patches" / "interest_seed.draft.json")
    ap.add_argument("--no-patches", action="store_true", help="不合并 patches/*.list")
    args = ap.parse_args()

    if not args.conf.exists():
        print(f"conf not found: {args.conf}")
        return 1

    draft = parse_conf(args.conf)
    if not args.no_patches:
        absorb_patches(ROOT / "patches", draft)

    # 启发式 vendors
    blob = " ".join(draft["domains"] + draft["suffixes"] + draft["keywords"])
    vendor_guess = []
    for v in (
        "anthropic",
        "claude",
        "openai",
        "siftscience",
        "statsig",
        "okx",
        "okex",
        "bybit",
        "appsflyer",
        "tiktok",
        "pangle",
        "bilibili",
        "coolapk",
        "xiaohongshu",
        "google",
    ):
        if v in blob:
            vendor_guess.append(v)

    out = {
        "version": "5.3",
        "updated": now_date(),
        "timezone": "Asia/Shanghai",
        "notes": "AUTO DRAFT from conf — revise before using as interest_seed.json",
        "policy_tags": draft["policy_tags"],
        "vendors": vendor_guess,
        "keywords": sorted(set(draft["keywords"] + vendor_guess)),
        "domains": draft["domains"],
        "suffixes": draft["suffixes"],
        "wildcards": draft["wildcards"],
        "allow_policy_hosts": [],
        "reject_interest": [
            "tiktokpangle-b.us",
            "tiktokpangle-cdn-us.com",
            "tiktokpangle.us",
            "pangle.io",
        ],
        "policy_map_hints": {
            "ai-critical.list": "🤖 AI住宅",
            "finance-critical.list": "🪙 数字资产",
            "finance-bybit-eu.list": "🇩🇪 Bybit 欧洲",
            "finance-bybit-global.list": "💳 Bybit 全球",
            "ads-patch.list": "REJECT",
            "direct-patch.list": "DIRECT",
        },
    }
    # allow：非 REJECT 类种子域的子集提示（人工再标）
    out["allow_policy_hosts"] = sorted(
        set(draft["suffixes"]) | {d for d in draft["domains"] if "pangle" not in d}
    )[:80]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output}")
    print(
        f"  domains={len(out['domains'])} suffixes={len(out['suffixes'])} "
        f"keywords={len(out['keywords'])} vendors={out['vendors']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
