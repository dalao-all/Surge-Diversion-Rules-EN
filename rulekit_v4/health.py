"""Check default-branch update health using the GitHub API (Python stdlib only)."""

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


class HealthError(Exception):
    """A failed health check or unavailable evidence."""


def timestamp(value):
    try:
        result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError("missing timezone")
        return result
    except (AttributeError, TypeError, ValueError) as exc:
        raise HealthError("GitHub returned a missing or invalid run timestamp.") from exc


class GitHub:
    def __init__(self, token, api_url="https://api.github.com", opener=None, sleep=time.sleep):
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.opener = opener or urllib.request.urlopen
        self.sleep = sleep

    def get(self, path):
        request = urllib.request.Request(self.api_url + path, headers={
            "Authorization": "Bearer " + self.token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "surge-rule-update-health",
        })
        for attempt in range(3):
            try:
                with self.opener(request, timeout=20) as response:
                    return json.load(response)
            except urllib.error.HTTPError as exc:
                if (exc.code == 429 or 500 <= exc.code <= 599) and attempt < 2:
                    # Bound both retry count and delay, even with an excessive Retry-After.
                    try:
                        delay = float(exc.headers.get("Retry-After", 2 ** attempt))
                    except (TypeError, ValueError):
                        delay = 2 ** attempt
                    self.sleep(max(0, min(10, delay)))
                    continue
                raise HealthError(f"GitHub API request failed (HTTP {exc.code}); health is unknown.") from exc
            except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
                # Never dump response bodies, request headers, or the token.
                raise HealthError("GitHub API could not be read; health is unknown.") from exc


def eligible(run, branch, repository):
    return (run.get("head_branch") == branch
            and run.get("event") not in {"pull_request", "pull_request_target"}
            and (run.get("head_repository") or {}).get("full_name", repository) == repository)


def recent_runs(api, repository, workflow, branch):
    path = f"/repos/{repository}/actions/workflows/{urllib.parse.quote(workflow, safe='')}/runs"
    runs = []
    for page in range(1, 11):
        query = urllib.parse.urlencode({"branch": branch, "per_page": 100, "page": page})
        payload = api.get(path + "?" + query)
        if not isinstance(payload, dict) or not isinstance(payload.get("workflow_runs"), list):
            raise HealthError("GitHub returned an invalid workflow-runs response; health is unknown.")
        batch = payload["workflow_runs"]
        runs.extend(run for run in batch if eligible(run, branch, repository))
        if any(run.get("conclusion") == "success" for run in runs) or len(batch) < 100:
            return runs
    raise HealthError("Run history exceeded the 1,000-run evidence limit; health is unknown.")


@dataclass(frozen=True)
class Result:
    state: str
    message: str


def evaluate(runs, now, branch, repository, trigger=None, max_age_hours=36, grace_hours=1):
    if not 0 <= grace_hours <= 1:
        raise HealthError("First-run grace must be between zero and one hour.")
    valid = [run for run in runs if eligible(run, branch, repository)]
    if trigger is not None:
        if not eligible(trigger, branch, repository):
            return Result("skipped", "Ignored a pull request, fork, or non-default-branch update.")
        if trigger.get("status") != "completed" or trigger.get("conclusion") != "success":
            raise HealthError(f"Triggering update run {trigger.get('id')} did not succeed "
                              f"({trigger.get('conclusion') or trigger.get('status')}).")
        if not any(run.get("id") == trigger.get("id") for run in valid):
            valid.append(trigger)
    if not valid:
        raise HealthError("No eligible default-branch update runs exist; no successful update is established.")
    # API order is by creation, not completion; an old rerun must not replace a newer failed update.
    valid.sort(key=lambda run: (timestamp(run.get("created_at")), int(run.get("id", 0))), reverse=True)
    latest = valid[0]
    completed = next((run for run in valid if run.get("status") == "completed"), None)
    if completed and completed.get("conclusion") != "success":
        raise HealthError(f"Latest completed eligible update run {completed.get('id')} failed "
                          f"({completed.get('conclusion')}); an older success cannot clear this failure.")
    successes = [run for run in valid if run.get("status") == "completed" and run.get("conclusion") == "success"]
    if not successes:
        elapsed = (now - timestamp(latest.get("created_at"))).total_seconds() / 3600
        if latest.get("status") in {"queued", "in_progress", "waiting", "requested", "pending"} and 0 <= elapsed <= grace_hours:
            return Result("pending", f"PENDING: first default-branch update is {latest.get('status')} "
                          f"({elapsed:.2f} h old; grace <= {grace_hours:g} h). Publication is not yet confirmed.")
        raise HealthError("No successful default-branch update exists; first-run grace is unavailable or expired.")
    success = max(successes, key=lambda run: timestamp(run.get("updated_at")))
    age = (now - timestamp(success.get("updated_at"))).total_seconds() / 3600
    if age < 0:
        raise HealthError("Successful update timestamp is in the future; health is unknown.")
    if age > max_age_hours:
        raise HealthError(f"Last successful update is stale ({age:.1f} h > {max_age_hours:g} h).")
    return Result("healthy", f"Last successful default-branch update: {age:.1f} h ago; run {success.get('id')}.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--workflow", default="rulekit-v4.yml", help="Workflow filename or numeric ID")
    parser.add_argument("--branch", help="Defaults to the repository's configured default branch")
    parser.add_argument("--event-path", default=os.environ.get("GITHUB_EVENT_PATH"))
    parser.add_argument("--max-age-hours", type=float, default=36)
    parser.add_argument("--grace-hours", type=float, default=1)
    args = parser.parse_args(argv)
    try:
        if not args.repository or len(args.repository.split("/")) != 2:
            raise HealthError("Provide --repository OWNER/REPO or GITHUB_REPOSITORY.")
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise HealthError("GITHUB_TOKEN is required to read workflow evidence.")
        api = GitHub(token, os.environ.get("GITHUB_API_URL", "https://api.github.com"))
        branch = args.branch or api.get(f"/repos/{args.repository}").get("default_branch")
        if not branch:
            raise HealthError("GitHub did not return the repository's default branch.")
        trigger = None
        if args.event_path:
            event = json.loads(Path(args.event_path).read_text())
            if os.environ.get("GITHUB_EVENT_NAME") == "workflow_run":
                trigger = event.get("workflow_run")
                if not isinstance(trigger, dict):
                    raise HealthError("workflow_run event is missing its triggering run.")
        result = evaluate(recent_runs(api, args.repository, args.workflow, branch),
                          dt.datetime.now(dt.timezone.utc), branch, args.repository, trigger,
                          args.max_age_hours, args.grace_hours)
        print(f"{result.state.upper()}: {result.message}")
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as handle:
                handle.write(f"Update health: **{result.state}**\n\n{result.message}\n")
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as handle:
                handle.write(f"state={result.state}\n")
        return 0
    except (HealthError, OSError, ValueError, TypeError, AttributeError) as exc:
        # Only our sanitized HealthError messages can enter CI output.
        message = str(exc) if isinstance(exc, HealthError) else "Unable to read health evidence."
        print("FAILED: " + message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
