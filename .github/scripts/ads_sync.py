#!/usr/bin/env python3
"""Weekly ads-patch sync, designed to run as a GitHub Action.

Fetches Thelongdarkorg/ad-rules-merged, converts to Surge format, and writes
patches/ads-patch.list + patches/ads-patch.domainset in the checked-out repo.
The workflow commits and pushes with GITHUB_TOKEN; no PAT needed.

Usage: python3 ads_sync.py --lang cn|en --repo DIR
Idempotency: exclusions.txt (derived from the 2026-09-27 snapshot) guarantees
the same upstream input reproduces the same output.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
UPSTREAM_RAW = "https://raw.githubusercontent.com/Thelongdarkorg/ad-rules-merged/main/merged.txt"
UPSTREAM_API = "https://api.github.com/repos/Thelongdarkorg/ad-rules-merged/commits?path=merged.txt&per_page=1"
DOMAIN = r'[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?'


def fetch(url, timeout=60):
    r = subprocess.run(
        ["curl", "-sS", "--max-time", str(timeout), "-A", "Mozilla/5.0 (surge-ads-sync)", url],
        capture_output=True, text=True, timeout=timeout + 10)
    if r.returncode != 0:
        raise RuntimeError(f"curl fetch failed for {url}: {r.stderr[:300]}")
    return r.stdout


def parse_upstream(text):
    """Parse upstream rules. Returns (block, allow, path_skipped).

    Only host-level rules (||host^, ||host/, ||host|) become blocks.
    Path-specific rules (||host/some/path) are DISCARDED: Surge cannot do
    path matching, and whole-host blocking breaks sites (e.g. turning
    ||mp.weixin.qq.com/mp/advertisement^ into a block of all mp.weixin.qq.com
    breaks WeChat article reading). Better to miss an ad than break a site.

    Hosts-format lines ("0.0.0.0 example.com", "127.0.0.1 example.com") are
    SKIPPED entirely (2026-10-13 fix): merged.txt carries ~11k of them, sourced
    from aggressive personal splash-screen hosts lists that list FUNCTIONAL
    infrastructure (0.0.0.0 apiinit.amap.com breaks Amap SDK init,
    0.0.0.0 snssdk.com suffix-expanded to nuke all of Douyin's APIs,
    0.0.0.0 img.360buyimg.com kills JD product images, etc.). Converting them
    -- even as exact-host matches -- breaks apps. Better to miss an ad than
    break a service. (The 2026-10-12 change that converted them added ~3,550
    entries and broke Douyin/JD/Amap; reverted here.)

    A || rule is only accepted when the character right after the hostname is
    a valid ABP terminator (^, |, $, /) or end-of-line. Without this,
    ||at*.doubanio.com^ truncated at "*" and produced "at", which became a
    block of the entire .at TLD (same for .az .bz .ad .ads .click .download).
    Single-label results are skipped as well.

    Partial wildcards ("log*.x.com", "beacons*.gvt3.com"), bare IPs and
    single-label names are SKIPPED -- converting "log*.aliyuncs.com" to a
    suffix of aliyuncs.com would nuke all of Alibaba Cloud. Better to miss an
    ad than break a service.
    """
    block, allow, path_skipped = set(), set(), set()
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r'^\|\|(' + DOMAIN + r')', line)
        if m:
            domain = m.group(1).lower()
            rest = re.sub(r'^:\d+', '', line[m.end():])  # strip :port
            # Hostname must be followed by a valid ABP terminator (^, |, $, /)
            # or end-of-line. ||at*.doubanio.com^ must NOT become "at".
            if '.' not in domain:
                continue
            if rest and rest[0] not in '/^|$':
                continue
            if rest.startswith('/'):
                tail = rest[1:]
                # root path ("/", "/^") -> host rule; "/real/path" -> discard
                if tail and not re.match(r'^[\^|$]', tail):
                    path_skipped.add(domain)
                    continue
            block.add(domain)
            continue
        # hosts-format lines ("0.0.0.0 x", "127.0.0.1 x"): SKIPPED, see
        # docstring. Do NOT convert them -- upstream's hosts section lists
        # functional domains and suffix-expanding them breaks apps.
        # only bare @@||domain (no $ options) counts as global allowlist;
        # scoped exceptions like @@||x^$domain=y do NOT unblock the domain
        if '$' not in line:
            m = re.match(r'^@@\|\|(' + DOMAIN + r')(?=[\^/:|$]|$)', line)
            if m:
                allow.add(m.group(1).lower())
    return block, allow, path_skipped


def load_exclusions():
    out = set()
    with open(os.path.join(HERE, "exclusions.txt"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                out.add(line)
    return out


def is_apple_service(d):
    return (d == "apple.com" or d.endswith(".apple.com")
            or d == "icloud.com" or d.endswith(".icloud.com")
            or "cdn-apple.com" in d)


def read_current_list(path):
    cur = set()
    if not os.path.exists(path):
        return cur
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("DOMAIN-SUFFIX,"):
                cur.add(line.split(",")[1].lower())
    return cur


LIST_HDR = {
    "cn": """# —— 上游状态（你的订阅，{verify} 核验）——
# 来源：快照（Thelongdarkorg/ad-rules-merged，{snapshot}，非实时同步） ｜ 有效条目：{count}（不含注释/空行）
# 复核周期建议：自维护表随问题反馈更新；快照表每周自动同步上游。
""",
    "en": """# —— Upstream status (Your Subscription, verified {verify}) ——
# Source: Snapshot (Thelongdarkorg/ad-rules-merged, {snapshot}, not live-synced) | Active entries: {count} (excl. comments/blanks)
# Review: self-maintained tables update on feedback; snapshot tables auto-sync upstream weekly.
""",
}
LIST_HDR_COMMON = """# Your Subscription / 你的订阅 V6.1 patches/ads-patch.list
# Self-maintained ad splash-screen patch: Surge-format conversion of 浮风拦截规则 (Thelongdarkorg/ad-rules-merged)
# Source snapshot: https://raw.githubusercontent.com/Thelongdarkorg/ad-rules-merged/main/merged.txt
# Snapshot date: {snapshot} (upstream Expires: 12h; this file is a snapshot mirror, re-sync weekly)
# Conversion: host-level ||host rules (^, |, $, / terminators only) ->
#   DOMAIN-SUFFIX,REJECT. Hosts-format lines (0.0.0.0 / 127.0.0.1) are SKIPPED:
#   upstream's hosts section lists functional infrastructure and converting it
#   breaks apps (2026-10-12 incident: apiinit.amap.com, snssdk.com apex, ...).
#   Path-specific rules (||host/path) are discarded (Surge cannot match paths;
#   whole-host blocking would break sites), as are partial wildcards
#   (log*.x.com), bare IPs and single-label names. DOMAIN-SET uses leading-dot
#   form for suffix match.
# Removed: upstream @@ allowlisted domains, plus standing audit exclusions
#   (Apple system/service domains, functional domains, higher-priority overlaps).
# Reference: main profile [Rule] section 1.3, after direct-patch, before the SKK ad base
"""
DS_HDR = {
    "cn": """# ads-patch.domainset ｜ ads-patch.list 的 DOMAIN-SET 形态（同源同内容）
# 来源：Thelongdarkorg/ad-rules-merged（Adblock Plus，{snapshot} 快照，{upstream_total} 条）机械转换
# 生成日期：{verify} ｜ 条目：{count}（纯域名）
# 用法：DOMAIN-SET,https://raw.githubusercontent.com/dalao-all/Surge-Diversion-Rules/main/patches/ads-patch.domainset,REJECT,update-interval=43200
# 注意：二选一，不要同时引用 .list 和 .domainset。
""",
    "en": """# ads-patch.domainset | DOMAIN-SET form of ads-patch.list (same source, same content)
# Source: Thelongdarkorg/ad-rules-merged (Adblock Plus, {snapshot} snapshot, {upstream_total} rules), mechanical conversion
# Built: {verify} | Entries: {count} (pure domains)
# Usage: DOMAIN-SET,https://raw.githubusercontent.com/dalao-all/Surge-Diversion-Rules-EN/main/patches/ads-patch.domainset,REJECT,update-interval=43200
# Note: pick ONE of .list / .domainset, not both.
""",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", required=True, choices=["cn", "en"])
    ap.add_argument("--repo", required=True, help="checked-out repo root")
    args = ap.parse_args()

    cst = timezone(timedelta(hours=8))
    verify = datetime.now(cst).strftime("%Y-%m-%d")

    upstream_text = fetch(UPSTREAM_RAW)
    upstream_total = len(upstream_text.splitlines())
    try:
        commits = json.loads(fetch(UPSTREAM_API))
        snapshot = commits[0]["commit"]["committer"]["date"][:10]
    except Exception:
        snapshot = verify

    block, allow, path_skipped = parse_upstream(upstream_text)
    candidate = block - allow - load_exclusions()
    current = read_current_list(os.path.join(args.repo, "patches", "ads-patch.list"))
    added = sorted(candidate - current)
    removed = sorted(current - candidate)
    quarantine = sorted(d for d in added if is_apple_service(d))
    final = candidate - set(quarantine)
    net_added = len(added) - len(quarantine)

    count = len(final)
    list_content = (LIST_HDR[args.lang].format(verify=verify, snapshot=snapshot, count=count)
                    + LIST_HDR_COMMON.format(snapshot=snapshot)
                    + "".join(f"DOMAIN-SUFFIX,{d},REJECT\n" for d in sorted(final)))
    # DOMAIN-SET: leading dot = suffix match (official manual). Bare domains
    # would be exact-match only, silently dropping subdomain coverage.
    ds_content = (DS_HDR[args.lang].format(verify=verify, snapshot=snapshot,
                                           count=count, upstream_total=upstream_total)
                  + "".join(f".{d}\n" for d in sorted(final)))

    with open(os.path.join(args.repo, "patches", "ads-patch.list"), "w") as f:
        f.write(list_content)
    with open(os.path.join(args.repo, "patches", "ads-patch.domainset"), "w") as f:
        f.write(ds_content)

    print(f"SUMMARY net=+{net_added} removed={len(removed)} "
          f"(new_upstream={len(added)} quarantined_apple={len(quarantine)} "
          f"path_rules_skipped={len(path_skipped)})")
    if quarantine:
        print("QUARANTINED:")
        for d in quarantine:
            print(f"  {d}")


if __name__ == "__main__":
    main()
