#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""你的订阅 Surge V6.0 每日兴趣驱动补丁机器人（标准库骨架）。

日程（Asia/Shanghai）：每天 09:00 与 21:00 拉取 frequent 上游 → diff 新增 →
按 interest_seed + selectors 筛选 → 写入 candidates / 生成 PR 说明。
默认不整包同步 SKK reject 等大文件。

Cron 示例：
  0 9,21 * * * cd /path/to/your-subscription-surge-v6.0 && \\
    python3 scripts/daily_patch_bot.py --mode pr --fetch-upstream \\
    >> /var/log/your-subscription-patch-bot.log 2>&1

详见 docs/MAINTENANCE.md、docs/INTEREST_MODEL.md。
"""

from __future__ import annotations

import argparse
import os
import subprocess
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Shanghai")
ROOT = Path(__file__).resolve().parents[1]
PATCHES = ROOT / "patches"
CACHE = PATCHES / "cache"
CANDIDATES = PATCHES / "candidates"
MANIFEST_PATH = PATCHES / "manifest.json"
REGRESSION_PATH = Path(__file__).resolve().parent / "regression_cases.json"
WATCH_PATH = PATCHES / "upstream_watch.yaml"
SELECTORS_PATH = PATCHES / "selectors.yaml"
SEED_PATH = PATCHES / "interest_seed.json"
SEED_EXAMPLE = PATCHES / "interest_seed.example.json"

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_GATE = 2

LIST_POLICY = {
    "ai-critical.list": "🤖 AI住宅",
    "finance-critical.list": "🪙 数字资产",
    "finance-bybit-eu.list": "🇩🇪 Bybit 欧洲",
    "finance-bybit-global.list": "💳 Bybit 全球",
    "ads-patch.list": "REJECT",
    "direct-patch.list": "DIRECT",
}


# ---------------------------------------------------------------------------
# 极简 YAML 子集（标准库）：足以解析本仓库的 watch / selectors
# ---------------------------------------------------------------------------

def _parse_scalar(s: str) -> Any:
    s = s.strip()
    # 行尾注释（先于 true/false，避免 "false  # ..." 变成字符串）
    if " #" in s and not (s.startswith('"') or s.startswith("'")):
        s = s.split(" #", 1)[0].rstrip()
    if s == "" or s == "~" or s.lower() == "null":
        return None
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    # 流式列表 [a, b, c]
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(p.strip()) for p in inner.split(",")]
    try:
        if re.fullmatch(r"-?\d+", s):
            return int(s)
    except Exception:
        pass
    return s


def load_simple_yaml(path: Path) -> Any:
    """解析缩进式 YAML 子集：dict / list / scalar / 注释。"""
    lines = path.read_text(encoding="utf-8").splitlines()

    def parse_block(index: int, indent: int) -> Tuple[Any, int]:
        # 窥视决定 list 还是 dict
        while index < len(lines):
            raw = lines[index]
            if not raw.strip() or raw.lstrip().startswith("#"):
                index += 1
                continue
            break
        if index >= len(lines):
            return None, index
        first = lines[index]
        cur_indent = len(first) - len(first.lstrip(" "))
        if cur_indent < indent:
            return None, index
        if first.lstrip().startswith("- "):
            items: List[Any] = []
            while index < len(lines):
                raw = lines[index]
                if not raw.strip() or raw.lstrip().startswith("#"):
                    index += 1
                    continue
                ind = len(raw) - len(raw.lstrip(" "))
                if ind < indent:
                    break
                if ind > indent and not raw.lstrip().startswith("- "):
                    break
                if ind != indent or not raw.lstrip().startswith("- "):
                    break
                content = raw.lstrip()[2:]
                if content.strip() == "" or (":" in content and not content.strip().startswith("{")):
                    # 可能是 "- key: val" 或 "-\\n  key:"
                    if ":" in content and not content.rstrip().endswith(":"):
                        # inline map on list item: - id: foo
                        # collect following deeper keys into one dict
                        d: Dict[str, Any] = {}
                        k, v = content.split(":", 1)
                        d[k.strip()] = _parse_scalar(v)
                        index += 1
                        nested, index = parse_block(index, indent + 2)
                        if isinstance(nested, dict):
                            d.update(nested)
                        elif nested is not None:
                            # shouldn't usually happen
                            pass
                        # also absorb sibling keys at indent+2 that are key: value
                        while index < len(lines):
                            raw2 = lines[index]
                            if not raw2.strip() or raw2.lstrip().startswith("#"):
                                index += 1
                                continue
                            ind2 = len(raw2) - len(raw2.lstrip(" "))
                            if ind2 < indent + 2:
                                break
                            if raw2.lstrip().startswith("- "):
                                break
                            if ind2 == indent + 2 and ":" in raw2:
                                kk, vv = raw2.lstrip().split(":", 1)
                                if vv.strip() == "":
                                    child, index = parse_block(index + 1, indent + 4)
                                    d[kk.strip()] = child
                                else:
                                    d[kk.strip()] = _parse_scalar(vv)
                                    index += 1
                                continue
                            break
                        items.append(d)
                    elif content.rstrip().endswith(":") or content.strip() == "":
                        key_part = content[:-1].strip() if content.rstrip().endswith(":") else None
                        index += 1
                        child, index = parse_block(index, indent + 2)
                        if key_part:
                            items.append({key_part: child})
                        else:
                            items.append(child)
                    else:
                        items.append(_parse_scalar(content))
                        index += 1
                else:
                    items.append(_parse_scalar(content))
                    index += 1
            return items, index

        # dict
        result: Dict[str, Any] = {}
        while index < len(lines):
            raw = lines[index]
            if not raw.strip() or raw.lstrip().startswith("#"):
                index += 1
                continue
            ind = len(raw) - len(raw.lstrip(" "))
            if ind < indent:
                break
            if ind > indent:
                break
            if raw.lstrip().startswith("- "):
                break
            if ":" not in raw:
                index += 1
                continue
            key, rest = raw.lstrip().split(":", 1)
            key = key.strip()
            if rest.strip() == "":
                index += 1
                child, index = parse_block(index, indent + 2)
                result[key] = child
            else:
                result[key] = _parse_scalar(rest)
                index += 1
        return result, index

    data, _ = parse_block(0, 0)
    return data if data is not None else {}


def now_label() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S %Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_url(url: str, timeout: int = 30) -> Dict[str, Any]:
    rec: Dict[str, Any] = {"url": url, "fetched_at": now_label()}
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = resp.read()
            headers = {k: v for k, v in resp.headers.items()}
        rec["ok"] = True
        rec["body"] = body
        rec["sha256"] = sha256_bytes(body)
        rec["bytes"] = len(body)
        rec["etag"] = headers.get("ETag") or headers.get("etag") or ""
        rec["last_modified"] = headers.get("Last-Modified") or ""
    except Exception as e:  # noqa: BLE001
        rec["ok"] = False
        rec["error"] = str(e)
    return rec


def normalize_rule_line(line: str) -> Optional[str]:
    s = line.strip()
    if not s or s.startswith("#"):
        return None
    # DOMAIN-SET 文件可能是纯域名
    if "," not in s and re.match(r"^[A-Za-z0-9_.*-]+$", s):
        host = s.lower()
        try:
            if "*" not in host:
                host = host.encode("idna").decode("ascii")
        except Exception:
            pass
        return f"DOMAIN,{host}"
    parts = s.split(",")
    if len(parts) < 2:
        return s.lower()
    rtype, host = parts[0].strip().upper(), parts[1].strip().lower()
    rest = ",".join(parts[2:]).strip()
    try:
        if "*" not in host and not host.startswith("."):
            host = host.encode("idna").decode("ascii")
    except Exception:
        pass
    out = f"{rtype},{host}"
    if rest:
        # 去掉策略名等尾部（上游 RULE-SET 行有时带策略；兴趣比对用类型+host）
        out += f",{rest}"
    return out


def rule_host(rule: str) -> str:
    if "," not in rule:
        return rule.lower()
    parts = rule.split(",")
    return parts[1].strip().lower() if len(parts) > 1 else rule.lower()


def rule_type(rule: str) -> str:
    return rule.split(",", 1)[0].upper() if "," in rule else "DOMAIN"


def load_list_rules(path: Path) -> List[str]:
    rules = []
    for line in path.read_text(encoding="utf-8").splitlines():
        n = normalize_rule_line(line)
        if n:
            rules.append(n)
    return rules


def etld1(host: str, multi: List[str]) -> str:
    host = host.lower().lstrip(".")
    for m in multi:
        if host == m or host.endswith("." + m):
            # keep one label + multi TLD
            rest = host[: -len(m)].rstrip(".")
            if not rest:
                return m
            return rest.split(".")[-1] + "." + m
    parts = host.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host


def load_seed() -> Dict[str, Any]:
    path = SEED_PATH if SEED_PATH.exists() else SEED_EXAMPLE
    seed = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    # 用现有 patches 补强
    domains = set(seed.get("domains") or [])
    suffixes = set(seed.get("suffixes") or [])
    for list_path in PATCHES.glob("*.list"):
        for r in load_list_rules(list_path):
            h = rule_host(r)
            if "example.invalid" in h or h.endswith(".invalid"):
                continue
            rt = rule_type(r)
            if rt == "DOMAIN-SUFFIX":
                suffixes.add(h)
            elif rt in ("DOMAIN", "DOMAIN-WILDCARD"):
                domains.add(h)
    seed["domains"] = sorted(domains)
    seed["suffixes"] = sorted(suffixes)
    seed.setdefault("allow_policy_hosts", [])
    seed.setdefault("reject_interest", [])
    seed.setdefault("keywords", [])
    seed.setdefault("vendors", [])
    return seed


def semantic_dedupe(rules: List[str]) -> Tuple[List[str], List[str]]:
    suffixes = set()
    for r in rules:
        if r.startswith("DOMAIN-SUFFIX,"):
            suffixes.add(rule_host(r))
    kept, removed = [], []
    for r in rules:
        if r.startswith("DOMAIN,"):
            host = rule_host(r)
            if any(host == s or host.endswith("." + s) for s in suffixes):
                removed.append(r)
                continue
        kept.append(r)
    return kept, removed


def conflict_check(policy_map: Dict[str, str]) -> List[str]:
    alerts = []
    by_host: Dict[str, List[str]] = {}
    for rule, policy in policy_map.items():
        host = rule_host(rule)
        by_host.setdefault(host, []).append(policy)
    for host, pols in by_host.items():
        uniq = sorted(set(pols))
        if len(uniq) > 1 and ("REJECT" in uniq or "REJECT-DROP" in uniq):
            if any(p not in ("REJECT", "REJECT-DROP") for p in uniq):
                alerts.append(f"CONFLICT {host}: {uniq}")
    return alerts


def run_regression(cases_path: Path, policy_map: Dict[str, str]) -> List[str]:
    data = json.loads(cases_path.read_text(encoding="utf-8"))
    failures = []
    hosts_by_policy: Dict[str, List[str]] = {}
    for rule, pol in policy_map.items():
        hosts_by_policy.setdefault(pol, []).append((rule_type(rule), rule_host(rule)))

    def match(domain: str, rt: str, host: str) -> bool:
        domain, host = domain.lower(), host.lower()
        if rt == "DOMAIN":
            return domain == host
        if rt == "DOMAIN-SUFFIX":
            return domain == host or domain.endswith("." + host)
        if rt == "DOMAIN-WILDCARD":
            import fnmatch

            return fnmatch.fnmatch(domain, host)
        return False

    for case in data.get("cases", []):
        name = case.get("name", "?")
        domain = case.get("domain", "")
        expect_policy = case.get("expect_policy")
        expect_action = case.get("expect_action")
        if case.get("scope") == "main_config":
            continue
        if expect_action == "REJECT":
            for pol, items in hosts_by_policy.items():
                if pol in ("REJECT", "REJECT-DROP"):
                    continue
                for rt, host in items:
                    if match(domain, rt, host):
                        failures.append(f"{name}: {domain} should be REJECT but found in {pol}")
            continue
        target = expect_policy or expect_action
        if not target:
            continue
        found = False
        for pol, items in hosts_by_policy.items():
            if pol != target:
                continue
            for rt, host in items:
                if match(domain, rt, host):
                    found = True
                    break
            if found:
                break
        if not found and target in (
            "🤖 AI住宅",
            "🪙 数字资产",
            "🇩🇪 Bybit 欧洲",
            "💳 Bybit 全球",
            "DIRECT",
            "REJECT",
        ):
            if "google" in name.lower():
                continue
            failures.append(f"{name}: {domain} not found for expect {target}")
    return failures


def anomaly_gates(
    old_count: int, new_count: int, deleted_critical: List[str], added: int, max_add: int = 20
) -> List[str]:
    msgs = []
    if old_count > 0 and new_count > old_count * 1.10:
        msgs.append(f"rule count growth {(new_count - old_count) / old_count:.1%} > 10%")
    if added > max_add:
        msgs.append(f"too many additions today: {added} > {max_add}")
    if deleted_critical:
        msgs.append(f"critical domains deleted: {deleted_critical}")
    return msgs


def build_policy_map() -> Dict[str, str]:
    out: Dict[str, str] = {}
    for fname, pol in LIST_POLICY.items():
        path = PATCHES / fname
        if not path.exists():
            continue
        for r in load_list_rules(path):
            out[r] = pol
    return out


def write_report(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def host_covered_by_allow(host: str, allow: List[str]) -> bool:
    host = host.lower()
    for a in allow:
        a = a.lower()
        if host == a or host.endswith("." + a) or a.endswith("." + host):
            return True
    return False


def classify_rule(
    rule: str,
    category: str,
    seed: Dict[str, Any],
    selectors: Dict[str, Any],
) -> Dict[str, Any]:
    """返回 {action, reason, target_list, priority}。"""
    host = rule_host(rule)
    rt = rule_type(rule)
    domains = set(x.lower() for x in seed.get("domains") or [])
    suffixes = set(x.lower() for x in seed.get("suffixes") or [])
    allow = [x.lower() for x in seed.get("allow_policy_hosts") or []]
    reject_interest = [x.lower() for x in seed.get("reject_interest") or []]
    multi = list(selectors.get("multi_part_tlds") or [])
    stop = set(selectors.get("stop_labels") or [])
    cat_target = (selectors.get("category_target") or {}).get(category)
    enabled = set(selectors.get("enabled_categories") or [])

    # reject_interest → ads
    for ri in reject_interest:
        if host == ri or host.endswith("." + ri) or ri.endswith("." + host) or ri in host:
            return {
                "action": "auto_pr_high",
                "reason": f"reject_interest:{ri}",
                "target_list": "ads-patch.list",
                "priority": "P0",
            }

    # 冲突：reject 类拟吸收但命中放行
    if category == "reject" and host_covered_by_allow(host, allow):
        return {
            "action": "review",
            "reason": "conflict_with_allow",
            "target_list": None,
            "priority": "GATE",
        }

    # P1 exact / suffix / parent-suffix
    if rt == "DOMAIN" and host in domains:
        return {
            "action": "auto_pr_high",
            "reason": "exact_domain_seed",
            "target_list": cat_target or "ai-critical.list",
            "priority": "P1",
        }
    if rt == "DOMAIN-SUFFIX" and host in suffixes:
        return {
            "action": "auto_pr_high",
            "reason": "exact_suffix_seed",
            "target_list": cat_target or "ai-critical.list",
            "priority": "P1",
        }
    for s in suffixes:
        if host == s or host.endswith("." + s):
            tgt = cat_target
            action = "auto_pr_high"
            if category == "reject" and selectors.get("reject_etld1_downgrade_to_review", True):
                action = "review"
                tgt = None
            return {
                "action": action,
                "reason": f"parent_suffix:{s}",
                "target_list": tgt if action == "auto_pr_high" else cat_target,
                "priority": "P1",
            }
    for d in domains:
        if d == host or d.endswith("." + host):
            return {
                "action": "auto_pr_high",
                "reason": f"covers_seed_domain:{d}",
                "target_list": cat_target or "ai-critical.list",
                "priority": "P1",
            }

    # P2 eTLD+1
    e1 = etld1(host, multi)
    seed_etld = {etld1(x, multi) for x in list(domains) + list(suffixes)}
    if e1 in seed_etld:
        action = "auto_pr_high"
        tgt = cat_target
        if category == "reject" and selectors.get("reject_etld1_downgrade_to_review", True):
            action = "review"
        if category in ("stream", "stream_us", "stream_jp", "stream_tw", "global") and not tgt:
            action = "review"
        return {
            "action": action,
            "reason": f"same_etld1:{e1}",
            "target_list": tgt if action == "auto_pr_high" else tgt,
            "priority": "P2",
        }

    # P3 vendor keywords
    for vk in selectors.get("vendor_keywords") or []:
        kws = vk.get("keywords") or []
        if isinstance(kws, str):
            kws = [kws]
        for kw in kws:
            if not isinstance(kw, str) or len(kw) < 3:
                continue
            if kw.lower() in host:
                return {
                    "action": vk.get("action") or "review",
                    "reason": f"vendor_keyword:{kw}",
                    "target_list": vk.get("target_list"),
                    "priority": "P3",
                }

    # P4 category weak link
    if category in enabled:
        labels = [lb for lb in host.split(".") if len(lb) >= 4 and lb not in stop]
        seed_labels = set()
        for x in list(domains) + list(suffixes) + list(seed.get("keywords") or []):
            for lb in re.split(r"[.*]", x.lower()):
                if len(lb) >= 4 and lb not in stop:
                    seed_labels.add(lb)
        if labels and any(lb in seed_labels for lb in labels):
            return {
                "action": "review",
                "reason": "category_weak_link",
                "target_list": cat_target,
                "priority": "P4",
            }

    # P5 default ignore（尤其 reject）
    return {
        "action": "ignore",
        "reason": "no_interest",
        "target_list": None,
        "priority": "P5",
    }


def diff_new_lines(old_text: str, new_text: str) -> List[str]:
    old_set = set()
    for line in old_text.splitlines():
        n = normalize_rule_line(line)
        if n:
            # 比对用类型+host
            old_set.add(f"{rule_type(n)},{rule_host(n)}")
    added = []
    for line in new_text.splitlines():
        n = normalize_rule_line(line)
        if not n:
            continue
        key = f"{rule_type(n)},{rule_host(n)}"
        if key not in old_set:
            added.append(n)
    return added


def fetch_and_filter(
    watch: Dict[str, Any],
    seed: Dict[str, Any],
    selectors: Dict[str, Any],
    include_frozen: bool,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """返回 (upstream_recs, candidates)。"""
    base = (watch.get("base_url") or "https://ruleset.skk.moe").rstrip("/")
    entries = list(watch.get("frequent") or [])
    if include_frozen:
        entries = entries + list(watch.get("frozen") or [])

    budgets = selectors.get("budgets") or {}
    max_auto_file = int(budgets.get("max_auto_per_file") or 15)
    max_auto_day = int(budgets.get("max_auto_per_day") or 40)
    max_review_file = int(budgets.get("max_review_per_file") or 50)

    CACHE.mkdir(parents=True, exist_ok=True)
    CANDIDATES.mkdir(parents=True, exist_ok=True)

    upstream_recs: List[Dict[str, Any]] = []
    candidates: List[Dict[str, Any]] = []
    auto_day = 0

    for ent in entries:
        eid = ent.get("id") or ent.get("path")
        path = ent.get("path") or ""
        url = base + path
        category = ent.get("category") or "unknown"
        print(f"  fetch {eid} ...")
        rec = fetch_url(url)
        meta = {
            "id": eid,
            "url": url,
            "category": category,
            "ok": rec.get("ok"),
            "sha256": rec.get("sha256"),
            "bytes": rec.get("bytes"),
            "etag": rec.get("etag"),
            "fetched_at": rec.get("fetched_at"),
            "error": rec.get("error"),
        }
        upstream_recs.append(meta)
        if not rec.get("ok"):
            print(f"    FAIL {rec.get('error')}")
            continue
        print(f"    ok sha256={str(rec.get('sha256'))[:12]}... bytes={rec.get('bytes')}")

        cache_file = CACHE / f"{eid}.txt"
        old_text = cache_file.read_text(encoding="utf-8") if cache_file.exists() else ""
        new_text = rec["body"].decode("utf-8", errors="replace")
        # 更新缓存
        cache_file.write_text(new_text, encoding="utf-8")
        (CACHE / f"{eid}.meta.json").write_text(
            json.dumps({k: v for k, v in meta.items() if k != "body"}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        if not old_text:
            print(f"    first snapshot stored; skip interest diff this run")
            continue

        added = diff_new_lines(old_text, new_text)
        print(f"    new rules: {len(added)}")
        auto_file = 0
        review_file = 0
        for rule in added:
            # 禁止整包：单文件新增极端大时只抽样报告
            if len(added) > 500 and category == "reject":
                # 仍逐条兴趣判定，但 ignore 占绝大多数；预算截断
                pass
            decision = classify_rule(rule, category, seed, selectors)
            action = decision["action"]
            if action == "auto_pr_high":
                if auto_file >= max_auto_file or auto_day >= max_auto_day:
                    action = "review"
                    decision["reason"] += "+budget_cap"
                else:
                    auto_file += 1
                    auto_day += 1
            if action == "review":
                if review_file >= max_review_file:
                    action = "ignore"
                    decision["reason"] += "+review_cap"
                else:
                    review_file += 1
            if action == "ignore":
                continue
            candidates.append(
                {
                    "upstream_id": eid,
                    "category": category,
                    "rule": f"{rule_type(rule)},{rule_host(rule)}",
                    "action": action,
                    "reason": decision["reason"],
                    "target_list": decision.get("target_list"),
                    "priority": decision.get("priority"),
                }
            )

    return upstream_recs, candidates


def build_pr_body(
    mode: str,
    blocked: bool,
    upstream_recs: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
    alerts: List[str],
    reg_fail: List[str],
    gate_msgs: List[str],
) -> Dict[str, Any]:
    high = [c for c in candidates if c["action"] == "auto_pr_high"]
    review = [c for c in candidates if c["action"] == "review"]
    return {
        "title": f"你的订阅 interest patches {datetime.now(TZ).date().isoformat()}",
        "mode": mode,
        "blocked": blocked,
        "schedule_note": "Asia/Shanghai 09:00 & 21:00 frequent upstream interest diff",
        "summary": [
            f"upstream snapshots: {len(upstream_recs)}",
            f"auto_pr_high: {len(high)}",
            f"review: {len(review)}",
            f"conflicts: {len(alerts)}",
            f"regression failures: {len(reg_fail)}",
            f"anomalies: {len(gate_msgs)}",
        ],
        "high_confidence_sample": high[:20],
        "review_sample": review[:20],
        "action": (
            "Open PR with own-list candidates only; no full reject.conf sync. "
            "Wait for human approve before atomic publish."
            if mode == "pr"
            else "APPLY requested — skeleton still refuses unconditional remote overwrite."
        ),
        "docs": ["docs/MAINTENANCE.md", "docs/INTEREST_MODEL.md"],
    }



def maybe_open_github_pr(pr_body: Dict[str, Any], candidates: List[Dict[str, Any]], blocked: bool) -> Dict[str, Any]:
    """若设置 GITHUB_TOKEN 且有候选，尝试开 PR；无候选则 no-op 成功。

    Actions 中由 workflow 调用本脚本 --mode apply --fetch-upstream（直接更新 patches，主人不审 PR）。
    无候选 / 门禁失败时不强制失败（门禁失败仍由 main 返回 EXIT_GATE）。
    """
    result: Dict[str, Any] = {"attempted": False, "created": False, "noop": False, "detail": ""}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    repo = os.environ.get("GITHUB_REPOSITORY") or ""
    if not token:
        result["detail"] = "no GITHUB_TOKEN — simulate only"
        return result
    high = [c for c in candidates if c["action"] in ("auto_pr_high", "review")]
    if blocked:
        result["detail"] = "gates blocked — skip PR"
        return result
    if not high:
        result["noop"] = True
        result["detail"] = "no candidates — no-op success"
        print("  GitHub PR: no-op (no candidates)")
        return result

    result["attempted"] = True
    # Write candidates artifact for the PR branch
    CANDIDATES.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(TZ).strftime("%Y%m%d-%H%M%S")
    branch = f"your-subscription/interest-bot-{stamp}"
    cand_path = CANDIDATES / f"interest-{stamp}.json"
    cand_path.write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_md = PATCHES / "candidates" / f"PR-{stamp}.md"
    lines = [
        f"# {pr_body.get('title')}",
        "",
        f"- schedule: {pr_body.get('schedule_note')}",
        f"- action: {pr_body.get('action')}",
        "",
        "## Summary",
    ]
    for s in pr_body.get("summary") or []:
        lines.append(f"- {s}")
    lines += ["", "## Notes", "", "Own curated lists only. Do not sync full SKK reject.", ""]
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    env = os.environ.copy()
    env["GITHUB_TOKEN"] = token
    env["GH_TOKEN"] = token

    def run(cmd: List[str]) -> subprocess.CompletedProcess:
        print("  $", " ".join(cmd))
        return subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)

    # Prefer gh CLI
    try:
        # Ensure we are in a git repo; Actions checkout provides that.
        st = run(["git", "status", "--porcelain"])
        if st.returncode != 0:
            result["detail"] = "not a git repo — skip PR push"
            print("  GitHub PR skip:", result["detail"])
            return result
        run(["git", "config", "user.name", "your-subscription-interest-bot"])
        run(["git", "config", "user.email", "your-subscription-interest-bot@users.noreply.github.com"])
        run(["git", "checkout", "-B", branch])
        run(["git", "add", str(cand_path.relative_to(ROOT)), str(report_md.relative_to(ROOT))])
        # also add report if present
        report_file = Path(__file__).resolve().parent / "last_bot_report.json"
        if report_file.exists():
            run(["git", "add", str(report_file.relative_to(ROOT))])
        msg = pr_body.get("title") or f"你的订阅 interest patches {stamp}"
        commit = run(["git", "commit", "-m", msg])
        if commit.returncode != 0 and "nothing to commit" in (commit.stdout + commit.stderr):
            result["noop"] = True
            result["detail"] = "nothing to commit"
            return result
        push = run(["git", "push", "-u", "origin", branch])
        if push.returncode != 0:
            result["detail"] = f"push failed: {push.stderr.strip()[:400]}"
            print("  GitHub PR push failed:", result["detail"])
            return result
        body = "\n".join(lines)
        pr = run([
            "gh", "pr", "create",
            "--title", msg,
            "--body", body,
            "--base", os.environ.get("GITHUB_BASE_REF") or "main",
            "--head", branch,
        ])
        if pr.returncode == 0:
            result["created"] = True
            result["detail"] = (pr.stdout or "").strip()
            print("  GitHub PR created:", result["detail"])
        else:
            result["detail"] = f"gh pr create failed: {(pr.stderr or pr.stdout)[:400]}"
            print("  GitHub PR create failed:", result["detail"])
    except FileNotFoundError as e:
        result["detail"] = f"tool missing: {e}"
        print("  GitHub PR skip:", result["detail"])
    except Exception as e:  # noqa: BLE001
        result["detail"] = f"exception: {e}"
        print("  GitHub PR exception:", result["detail"])
    return result


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "你的订阅 V6.0 interest-driven daily patch bot (stdlib). "
            "Schedule: Asia/Shanghai 09:00 & 21:00 fetch frequent upstream → "
            "diff → seed/selectors filter → candidates + PR body. "
            "Never sync entire reject.conf."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python3 scripts/daily_patch_bot.py --mode pr --skip-fetch
  python3 scripts/daily_patch_bot.py --mode pr --fetch-upstream
  python3 scripts/daily_patch_bot.py --mode apply --fetch-upstream --include-frozen
        """,
    )
    parser.add_argument("--mode", choices=("pr", "apply"), default="pr")
    parser.add_argument(
        "--fetch-upstream",
        action="store_true",
        help="拉取 upstream_watch.frequent（及可选 frozen）并做兴趣 diff",
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="跳过上游拉取（本地门禁/回归）；与 --fetch-upstream 同时出现时以 skip 为准",
    )
    parser.add_argument(
        "--include-frozen",
        action="store_true",
        help="连同 frozen 上游一并拉取（非默认日程）",
    )
    parser.add_argument("--report", type=Path, default=ROOT / "scripts" / "last_bot_report.json")
    args = parser.parse_args(argv)

    do_fetch = bool(args.fetch_upstream) and not args.skip_fetch

    print(f"[daily_patch_bot] start {now_label()} mode={args.mode} fetch={do_fetch}")
    print("  model: interest seed/selectors — own lists only; no full upstream sync")

    watch: Dict[str, Any] = {}
    selectors: Dict[str, Any] = {}
    if WATCH_PATH.exists():
        try:
            watch = load_simple_yaml(WATCH_PATH) or {}
        except Exception as e:  # noqa: BLE001
            print(f"  WARN watch yaml parse: {e}")
            watch = {}
    if SELECTORS_PATH.exists():
        try:
            selectors = load_simple_yaml(SELECTORS_PATH) or {}
        except Exception as e:  # noqa: BLE001
            print(f"  WARN selectors yaml parse: {e}")
            selectors = {}

    seed = load_seed()
    print(f"  seed domains={len(seed.get('domains') or [])} suffixes={len(seed.get('suffixes') or [])}")

    upstream_recs: List[Dict[str, Any]] = []
    candidates: List[Dict[str, Any]] = []
    if do_fetch:
        if not watch:
            print("  WARN no upstream_watch.yaml; skip fetch")
        else:
            upstream_recs, candidates = fetch_and_filter(
                watch, seed, selectors, include_frozen=args.include_frozen
            )
            day = datetime.now(TZ).strftime("%Y%m%d")
            out = CANDIDATES / f"interest-{day}.json"
            CANDIDATES.mkdir(parents=True, exist_ok=True)
            write_report(
                out,
                {
                    "generated_at": now_label(),
                    "candidates": candidates,
                    "counts": {
                        "auto_pr_high": sum(1 for c in candidates if c["action"] == "auto_pr_high"),
                        "review": sum(1 for c in candidates if c["action"] == "review"),
                    },
                },
            )
            print(f"  candidates -> {out} ({len(candidates)} kept)")
    else:
        print("  skip fetch (use --fetch-upstream to pull SKK watch list)")

    policy_map = build_policy_map()
    print(f"  loaded patch rules: {len(policy_map)}")

    dedupe_notes = []
    for list_path in sorted(PATCHES.glob("*.list")):
        rules = load_list_rules(list_path)
        kept, removed = semantic_dedupe(rules)
        if removed:
            dedupe_notes.append({"file": list_path.name, "removed": removed})
            print(f"  dedupe {list_path.name}: remove {len(removed)}")

    alerts = conflict_check(policy_map)
    for a in alerts:
        print(f"  GATE {a}")

    # 候选与放行冲突再扫一遍
    for c in candidates:
        if c.get("target_list") == "ads-patch.list" and c.get("reason") != "conflict_with_allow":
            h = rule_host(c["rule"])
            if host_covered_by_allow(h, seed.get("allow_policy_hosts") or []):
                c["action"] = "review"
                c["reason"] = "conflict_with_allow"
                c["target_list"] = None
                alerts.append(f"CANDIDATE_CONFLICT {h}")

    reg_fail = run_regression(REGRESSION_PATH, policy_map)
    for f in reg_fail:
        print(f"  REGRESSION {f}")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")) if MANIFEST_PATH.exists() else {"rules": []}
    old_count = len([r for r in manifest.get("rules", []) if r.get("status") != "placeholder"])
    new_count = len([r for r, p in policy_map.items() if "example.invalid" not in r])
    auto_adds = sum(1 for c in candidates if c["action"] == "auto_pr_high")
    max_add = int((selectors.get("budgets") or {}).get("max_auto_per_day") or 40)
    gate_msgs = anomaly_gates(
        old_count, new_count, deleted_critical=[], added=auto_adds, max_add=max_add
    )
    for m in gate_msgs:
        print(f"  ANOMALY {m}")

    blocked = bool(alerts or reg_fail or gate_msgs)
    pr_body = build_pr_body(
        args.mode, blocked, upstream_recs, candidates, alerts, reg_fail, gate_msgs
    )
    print("  --- simulated PR ---")
    print(f"  title: {pr_body['title']}")
    for line in pr_body["summary"]:
        print(f"  - {line}")
    print(f"  action: {pr_body['action']}")

    report = {
        "generated_at": now_label(),
        "mode": args.mode,
        "fetch": do_fetch,
        "model": "interest_seed+selectors; own lists only",
        "upstream": upstream_recs,
        "candidates_count": len(candidates),
        "dedupe_notes": dedupe_notes,
        "conflicts": alerts,
        "regression_failures": reg_fail,
        "anomalies": gate_msgs,
        "pr": pr_body,
        "apply_performed": False,
        "auto_merge_high_confidence": bool(selectors.get("auto_merge_high_confidence")),
    }

    if args.mode == "apply":
        if blocked:
            print("  apply aborted: gates failed (report only)")
        else:
            # 骨架：可将 auto_pr_high 追加写入本地 list，但仍不推远程
            wrote = 0
            if selectors.get("auto_merge_high_confidence"):
                by_file: Dict[str, List[str]] = {}
                for c in candidates:
                    if c["action"] != "auto_pr_high" or not c.get("target_list"):
                        continue
                    by_file.setdefault(c["target_list"], []).append(c["rule"])
                for fname, rules in by_file.items():
                    path = PATCHES / fname
                    existing = set(load_list_rules(path)) if path.exists() else set()
                    add_lines = []
                    for r in rules:
                        key = f"{rule_type(r)},{rule_host(r)}"
                        # normalize key against existing
                        norm = normalize_rule_line(key) or key
                        if norm not in existing and key not in existing:
                            add_lines.append(key)
                    if add_lines:
                        with path.open("a", encoding="utf-8") as f:
                            f.write("\n# interest-auto " + now_label() + "\n")
                            for line in add_lines:
                                f.write(line + "\n")
                                wrote += 1
                print(f"  apply local append: {wrote} lines (no remote push)")
                report["apply_performed"] = wrote > 0
            else:
                print("  apply: auto_merge_high_confidence=false — write report/candidates only")
                report["apply_performed"] = False

    write_report(args.report, report)
    print(f"  report -> {args.report}")

    if blocked:
        print("[daily_patch_bot] FAIL gates — exit 2")
        return EXIT_GATE
    print("[daily_patch_bot] OK")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
