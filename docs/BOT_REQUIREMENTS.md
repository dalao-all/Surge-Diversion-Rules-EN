# Historical interest-bot requirements

> **Legacy design record — superseded.** This document describes the earlier v6.x interest-filtered patch bot. It is not the current release contract or schedule. Start with [V3.0.0 setup](GETTING_STARTED.md), [maintenance](MAINTENANCE.md) and [the current compiler](../rulekit_v4/README.md).

## What the earlier proposal covered

The original September 2026 proposal derived interest from the iPhone app catalog in `patches/app_catalog.yaml`, associated seed files, existing profile exceptions and selected upstream lists. The available tunnel/SGLog application-log archive was not a HAR or a reliable business-domain request inventory.

Its planned workflow watched upstream additions, filtered candidates by installed-app/vendor interest, applied conflict checks and prepared small `patches/` updates. Historical drafts mentioned 09:00 / 21:00 Beijing runs, PR-based review and differing optional direct-push phases. Those statements were proposals at different stages, not evidence that a production publisher was running successfully.

## Constraints retained as useful context

- Never expose node credentials or private subscription tokens.
- Keep domestic Douyin separate from international TikTok.
- Do not turn Pangle advertising into a TikTok business allow rule.
- Treat ambiguous app identity, shared clouds and missing request evidence as gaps.
- Prefer precise, attributable exceptions over broad vendor keyword whitelists.
- Do not infer complete application coverage from an app catalog or an available source list.

## What replaced it

Current maintenance is deterministic and manifest-based: 160 app records, 109 sources, 28 shared dependencies, seven categories, seven protection files, one advertising file and seven category files. The canonical repository fetches and validates upstreams; this English repository mirrors verified artifacts using its own token. Current schedules are 05:37 canonical build, 06:07 English mirror and 21:17 health check, all Beijing time.

The old seed files, selectors, `scripts/daily_patch_bot.py` and workflow example remain historical implementation references. Their presence does not make them the active installation or scheduled publication path. See Git history for the full earlier specification and [INTEREST_MODEL.md](INTEREST_MODEL.md) for its assumptions.
