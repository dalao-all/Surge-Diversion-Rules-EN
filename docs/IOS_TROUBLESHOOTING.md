# iPhone request bursts and resource-download troubleshooting

The supplied screenshot shows 588 requests in about one second, including 13 for `api-access.pangolin-sdk-toutiao-b.com`. Several advertising SDK hosts matched REJECT or REJECT-DROP. This establishes a burst of requests; the screenshot alone cannot prove every request was a retry caused by rejection, or establish a wrong node country or password.

## Early rejection and protection boundaries

The internal engine is 4.1.1. The main profile references 24 remote resources: eleven protection lists, one `ads-storm.list`, one `ads.domainset`, and eleven functional lists. The export validation manifest covers 25 data files, including the compatible `ads.list`; the static suite contains 210 probes. The main profile keeps GitHub raw URLs and a daily update interval of 86400 seconds.

Only nine explicit advertising endpoints already present in the screenshot enter the dedicated `ads-storm.list`, with `REJECT-DROP,pre-matching`. The full advertising DOMAIN-SET continues to use ordinary REJECT. According to the [official Surge reject-policy documentation](https://manual.nssurge.com/policies/reject.html), ordinary REJECT automatically escalates after 50 triggers within 30 seconds. Since Surge iOS 5.14, pre-matching can reject at the DNS/TCP stage; UDP still uses ordinary rules. Pre-matching takes priority over every ordinary allow rule, so putting an allow rule first is insufficient protection.

The generator retains only exact hosts still covered by the final cleaned advertising data and excludes all current and historical protection ranges. Adding protection automatically removes intersecting storm entries. The screenshots show direct connections to `et.tanx.com` and `userlink.alicdn.com`; connection records alone do not establish the purpose of those requests, so their parent domains are not newly blocked. DIRECT and normal active status for Apple, mail and OCSP are not evidence of a configuration fault.

## Separate empty nodes from download failures

The public profile retains `ipv6 = false` and an empty `[Proxy]` section as requested. Add your own nodes to a private copy, preserve your confirmed group-member order, and check name references and available nodes. Empty groups may fall back to SUBSTITUTE/DIRECT; Smart does not accept a built-in REJECT member to fill an empty group. That behavior does not establish a country or password fault.

Independent retrievals of raw `ads.domainset` and `cn.list` returned HTTP 200 with complete content during this investigation. This proves only those retrievals succeeded. The iPhone's exact failing network path and cause remain unconfirmed; phone resource loading cannot be called fixed. Do not assume remote downloads follow a particular routing policy, or add unsupported parameters such as `force-policy`.

Run the configuration check and confirm working nodes, then manually update external resources in Surge. Record each failing URL, time, exact error and network type. Check Wi-Fi and cellular separately. Successful import, server publication and actual phone download are separate outcomes.

## Local offline emergency copy

A local delivery may include `outputs/surge-V3.0.0-离线应急.conf`, with complete static rules and no dependency on external domain lists, for temporary initial connection and resource-download recovery. It is not committed to the public repository and is not a repository download link. You still need your own node definitions, and this copy does not update automatically. Return to the daily-updated main profile after connectivity and resource checks succeed.

## Real iPhone acceptance remains pending

Repeat the same business action over a comparable observation period and compare request totals, SDK-host counts and matched policies. Test app launch, login, payments, messaging and actual exits. Early rejection may change log visibility, so check application behavior as well. Static probes and independent downloads do not establish successful iPhone loading, an improved request burst, or acceptance of all business flows.

Additional check: the supplied expired V2.0.2 file contains 172 AnyTLS nodes. All current explicit member labels exist; streaming/international filters match 43/32 nodes. Only labels and field structure were checked; expired passwords were not reused. A stale resource cache can still retain a removed early-reject entry. Refresh all external resources successfully after changing protections before validating affected business flows.
