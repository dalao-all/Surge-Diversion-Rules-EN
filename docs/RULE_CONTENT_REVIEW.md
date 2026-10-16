# Rule content review — 2026-10-16

This release changes repository rules and their regression checks. It preserves the user's V3.3.0 phone profile, business-first ordering, IPv6 disabled and empty Proxy section. Compiler version 4.2.0 still publishes at dist/v4.

## Reviewed corrections

- Remove AS20473 from OpenAI classification: it is shared Vultr hosting, not an OpenAI-owned network. Replace six broad AI/TikTok substring rules with bounded domains and explicitly identified service endpoints.
- Supplement OpenAI and Claude authentication, static assets and content domains using vendor network documentation and the v2fly domain community. WorkOS additions are exact required endpoints, not a blanket exception for shared WorkOS hosting. Supplemental sources admit only the reviewed subset; unknown upstream additions are reported for review.
- Move the general Google download suffix gvt1.com from streaming to Google. Move TRAE international endpoints incorrectly inherited from TikTok to AI, retaining domestic endpoint classification. Protect the exact Discord upload bucket from the broader googleapis.com match.
- Associate official website/privacy-page domains with Tianfutong, JegoTrip, Autohome, NetEase UU Remote, Traffic 12123 and Individual Income Tax. Website identity is not proof of complete private app API coverage; these remain partial coverage.
- Normalize IPv4-mapped IPv6 addresses consistently. The Tencent Video 29-row representation change was not a change of network ownership. Exclude its three mapped addresses in the IANA 198.18.0.0/15 benchmark range; these cannot identify Tencent services. Keep source-change guards enabled.
- Refresh enabled sources at pinned commits. Advertising changes: 688 additions and 278 removals, net +410, subject to public-suffix, protection, size-change and business regression checks.

## Cross-checks and evidence boundaries

The review compares blackmatrix, Sukka, v2fly and AWA classifications with vendor documentation and official developer/privacy links. Community lists can share inputs; repeated entries are not independent votes.

The official AdGuard DNS filter was used as a comparison, not copied into Surge. Only 184315 unmodified suffix blocks and 11 simple exceptions were compared. Of 141417 published ad rules, 128196 host witnesses are also covered by these simple AdGuard blocks. Missing corroboration does not prove a rule is wrong. Two TVB exception candidates remain unresolved rather than automatically allowed. ABP modifiers and regular expressions were not converted.

Validation includes 237 static probes, eight negative scope probes, 69 compiler/content/failure-isolation tests and nine mirror tests. The local Surge parser accepted a synthetic-node profile and all 151443 expanded external rule rows. No private node credentials were exported or connected.

The user's business-first ordering deliberately bypasses 17 of 18 legacy advertising probes. They are disclosed in dist/v4/content-audit.json and must not be described as successful blocks. All 219 business probes pass with both supported external-domain orderings. This does not simulate DNS, GeoIP or inline protocol rules and is not an iPhone login, performance, battery or video test.

All exported rows are mechanically checked for syntax, scope, provenance and conflict handling. This is not a claim that every advertising domain's purpose has been manually verified. Unknown apps and unobserved private API endpoints still need request evidence. Failed daily updates retain the prior published release; third-party availability cannot be guaranteed.

## Sources and audit records

- [Vultr AS20473](https://docs.vultr.com/products/network/bgp/asn-information/as20473)
- [OpenAI network requirements](https://help.openai.com/en/articles/9247338-network-recommendations-for-chatgpt-errors-on-web-and-apps)
- [Claude Desktop network requirements](https://code.claude.com/docs/en/desktop#network-access-requirements)
- [Google Chrome update endpoints](https://support.google.com/chrome/a/answer/6334001)
- [Google Gemini API](https://ai.google.dev/api/models)
- [IANA special-purpose IPv4 registry](https://www.iana.org/assignments/iana-ipv4-special-registry/iana-ipv4-special-registry.xhtml)
- [AdGuard DNS filter](https://github.com/AdguardTeam/AdGuardSDNSFilter)

Per-decision evidence: rulekit_v4/content-review.json. App identity: rulekit_v4/apps.json. Comparison snapshot: rulekit_v4/reference-comparison.json. Source commits and hashes: dist/v4/sources.lock.json. Per-rule provenance: dist/v4/provenance.ndjson.gz. Classification results: dist/v4/content-audit.json. The English mirror adopts the canonical release only after its GitHub validation succeeds.
