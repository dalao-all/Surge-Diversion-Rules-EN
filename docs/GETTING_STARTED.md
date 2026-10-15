# Set up Surge V3.0.0

Use [surge-V3.0.0.conf](../profiles/surge-V3.0.0.conf), the current public profile. The internal engine and resource paths remain `rulekit_v4` and `dist/v4`.

## Before importing

You need a compatible Surge installation and nodes you are authorized to use. AnyTLS nodes require a Surge version that supports AnyTLS; the profile's Smart groups also require that feature to be available in your installation.

The public file deliberately has **no node definitions in `[Proxy]`**. It also sets **`ipv6 = false`**. An empty node section cannot supply proxy connectivity; adding your own nodes is a required setup step.

1. Download the profile and keep a private working copy.
2. Add your own node definitions to `[Proxy]`, or configure an appropriate provider using the Surge features you use. Never commit credentials or subscription tokens to a public repository.
3. Check every fallback member and Smart filter against your actual node names. The supplied groups reference original labels; they do not automatically map arbitrary subscription names.
4. Import the private copy into Surge, check configuration errors, and download all 23 external rule resources.
5. Check the selected nodes, first matching rule, and actual exit for representative business flows before switching daily traffic.

## Node labels require attention

AI and TikTok have separate fallback groups. Their supplied member order is `🇺🇸 美国 12 家宽`, `🇺🇸 美国 10 家宽`, `🇺🇸 美国 11 家宽`, `🇺🇸 美国 13 家宽`, `🇺🇸 美国 14 家宽`.

The UK fallback uses `🇬🇧 英国 04 家宽`, then `🇬🇧 英国 01`, `🇬🇧 英国 02`, `🇬🇧 英国 03`.

Preserve those exact labels in your private node definitions, or edit every affected group member to your own real labels. Inspect the Smart groups' country, residential and multiplier filters as well. A node name or successful URL test does not prove a residential exit, service eligibility, or a working AI login. Fallback can change your exit when a node fails.

## Expected routing

AI → US residential fallback; TikTok → its own US residential fallback; streaming → streaming Smart; Google → account select, following the AI group by default; UK → UK fallback; global → international Smart; CN → DIRECT. Meta's ordinary traffic uses global routing. Only evidence-backed precise AI authentication exceptions belong in the protected AI layer; Google account consistency is now an explicit reviewed exception; Meta remains on general international routing.

Rules run in the profile's written order: local network foundation → eleven business-protection resources → advertising resource → eleven category resources → CN / GEOIP / FINAL fallback. See the [routing map](../rule-map.html).

## First device checks

Test on Wi-Fi and cellular: bank/payment login, WeChat/DingTalk messaging, domestic video and maps, then AI login/upload/long connections, TikTok and streaming playback. Check DNS failures, node failures and rule rejects separately. Record the app ID, action, real host, first matching rule, policy, actual exit and time. Never substitute invented hosts for missing evidence.

The repository records 164 apps, 13 unresolved records and 5 local-only records. No record has complete or phone-validated coverage. Passing the static probes does not finish this device checklist.

## Keeping rules current

The profile intentionally reads canonical Chinese repository RULE-SET URLs. After a verified publication, refresh external resources in Surge. App changes, source updates and corrections within existing categories can usually be handled in the repository. New routing groups, node setup, DNS/IPv6 settings and module behavior require a profile change.

V3.0.0 does not require installing the archived v6.x AdBlock module. Legacy profiles/modules remain available only for compatibility. Read [maintenance](MAINTENANCE.md) before changing rule sources or rolling back.


Financial select groups: PayPal defaults to `🇺🇸 美国 12 家宽`; Wise, Binance and OKX default to `🇨🇳 台湾 07 家宽`. Preserve those original labels or change the members. The Google account select defaults to the actual `🤖 AI住宅` group; manually selecting another node changes that consistency. See [audit fixes](REVIEW_FIXES.md).
