import contextlib
import datetime as dt
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from health import GitHub, HealthError, eligible, evaluate, main, recent_runs


NOW = dt.datetime(2026, 10, 15, 1, tzinfo=dt.timezone.utc)
REPO = "example/surge"


def run(run_id=10, hours=1, status="completed", conclusion="success", **changes):
    stamp = (NOW - dt.timedelta(hours=hours)).isoformat()
    result = dict(id=run_id, created_at=stamp, updated_at=stamp, status=status,
                  conclusion=conclusion, event="schedule", head_branch="main",
                  head_repository={"full_name": REPO})
    result.update(changes)
    return result


class EvaluationTests(unittest.TestCase):
    def check(self, runs, **kwargs):
        return evaluate(runs, NOW, "main", REPO, **kwargs)

    def test_first_deployment_concurrent_update_has_bounded_pending_grace(self):
        result = self.check([run(hours=0.1, status="in_progress", conclusion=None)])
        self.assertEqual("pending", result.state)
        self.assertIn("not yet confirmed", result.message)
        for status in ("in_progress", "queued"):
            with self.subTest(status=status), self.assertRaisesRegex(HealthError, "grace"):
                self.check([run(hours=1.01, status=status, conclusion=None)])
        with self.assertRaisesRegex(HealthError, "between zero and one"):
            self.check([], grace_hours=2)

    def test_no_success_no_run_fails(self):
        with self.assertRaisesRegex(HealthError, "No eligible"):
            self.check([])

    def test_recent_success_and_exact_36_hour_boundary(self):
        self.assertEqual("healthy", self.check([run(hours=36)]).state)
        with self.assertRaisesRegex(HealthError, "stale"):
            self.check([run(hours=36.01)])

    def test_latest_completed_failure_cannot_be_hidden_by_old_success_or_retry(self):
        records = [run(9, hours=2), run(10, hours=1, conclusion="failure")]
        with self.assertRaisesRegex(HealthError, "older success"):
            self.check(records)
        records.append(run(11, hours=0.1, status="in_progress", conclusion=None))
        with self.assertRaisesRegex(HealthError, "older success"):
            self.check(records)

    def test_failed_trigger_is_reported_even_if_a_newer_run_succeeded(self):
        trigger = run(9, hours=2, conclusion="failure")
        with self.assertRaisesRegex(HealthError, "Triggering update run 9"):
            self.check([run(10, hours=1)], trigger=trigger)

    def test_successful_trigger_can_bridge_api_list_eventual_consistency(self):
        self.assertEqual("healthy", self.check([], trigger=run()).state)

    def test_pull_request_non_default_branch_and_fork_cannot_count_as_success(self):
        for change in ({"event": "pull_request"}, {"event": "pull_request_target"},
                       {"head_branch": "feature"}, {"head_repository": {"full_name": "fork/surge"}}):
            with self.subTest(change=change):
                candidate = run(**change)
                self.assertFalse(eligible(candidate, "main", REPO))
                with self.assertRaisesRegex(HealthError, "No eligible"):
                    self.check([candidate])
                self.assertEqual("skipped", self.check([run()], trigger=candidate).state)

    def test_successful_rerun_uses_completion_time_but_does_not_hide_newer_failure(self):
        rerun = run(1, hours=100, updated_at=(NOW - dt.timedelta(hours=1)).isoformat())
        self.assertEqual("healthy", self.check([rerun]).state)
        with self.assertRaisesRegex(HealthError, "older success"):
            self.check([rerun, run(2, hours=2, conclusion="failure")])

    def test_invalid_or_future_timestamp_fails(self):
        for change in ({"updated_at": "bad"}, {"created_at": None}, {"updated_at": (NOW + dt.timedelta(hours=1)).isoformat()}):
            with self.subTest(change=change), self.assertRaises(HealthError):
                self.check([run(**change)])


class ApiTests(unittest.TestCase):
    def test_rate_limit_and_server_errors_retry_with_bounded_delays(self):
        for code in (429, 500, 503):
            with self.subTest(code=code):
                calls, waits = [], []
                def opener(request, timeout):
                    calls.append(request)
                    if len(calls) < 3:
                        raise urllib.error.HTTPError(request.full_url, code, "secret response", {"Retry-After": "600"}, None)
                    return io.StringIO('{"workflow_runs": []}')
                result = GitHub("SECRET_TOKEN", opener=opener, sleep=waits.append).get("/test")
                self.assertEqual({"workflow_runs": []}, result)
                self.assertEqual([10, 10], waits)
                self.assertEqual(3, len(calls))

    def test_persistent_api_errors_are_failures_without_secrets_or_empty_runs(self):
        for code, expected_calls in ((429, 3), (503, 3), (401, 1), (403, 1), (404, 1)):
            with self.subTest(code=code):
                calls = []
                def opener(request, timeout):
                    calls.append(1)
                    raise urllib.error.HTTPError(request.full_url, code, "SECRET_TOKEN", {}, None)
                api = GitHub("SECRET_TOKEN", opener=opener, sleep=lambda _: None)
                with self.assertRaisesRegex(HealthError, f"HTTP {code}") as error:
                    recent_runs(api, REPO, "rulekit-v4.yml", "main")
                self.assertNotIn("SECRET_TOKEN", str(error.exception))
                self.assertEqual(expected_calls, len(calls))

    def test_invalid_json_and_network_failure_do_not_become_missing_success(self):
        for response in (io.StringIO("not json"), urllib.error.URLError("SECRET_TOKEN")):
            def opener(request, timeout):
                if isinstance(response, Exception):
                    raise response
                return response
            with self.subTest(response=type(response).__name__), self.assertRaisesRegex(HealthError, "health is unknown") as error:
                GitHub("SECRET_TOKEN", opener=opener).get("/test")
            self.assertNotIn("SECRET_TOKEN", str(error.exception))

    def test_pagination_filters_runs_and_uses_parameterized_workflow_and_branch(self):
        class FakeApi:
            def __init__(self):
                self.paths = []
            def get(self, path):
                self.paths.append(path)
                if len(self.paths) == 1:
                    return {"workflow_runs": [run(event="pull_request")] * 100}
                return {"workflow_runs": [run(head_branch="release", head_repository={"full_name": "example/english"})]}
        api = FakeApi()
        result = recent_runs(api, "example/english", "english update.yml", "release")
        self.assertEqual(1, len(result))
        self.assertIn("/repos/example/english/actions/workflows/english%20update.yml/", api.paths[0])
        self.assertIn("branch=release", api.paths[0])
        self.assertIn("page=2", api.paths[1])

    def test_malformed_response_fails(self):
        class FakeApi:
            def get(self, path):
                return {"message": "unavailable"}
        with self.assertRaisesRegex(HealthError, "invalid workflow-runs"):
            recent_runs(FakeApi(), REPO, "rulekit-v4.yml", "main")

    def test_cli_uses_actual_trigger_failure_and_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            event = Path(directory) / "event.json"
            event.write_text(json.dumps({"workflow_run": run(conclusion="failure")}))
            output = io.StringIO()
            with patch.dict(os.environ, {"GITHUB_TOKEN": "SECRET_TOKEN", "GITHUB_EVENT_NAME": "workflow_run"}), \
                 patch("health.GitHub.get", return_value={"workflow_runs": [run(11)]}), \
                 contextlib.redirect_stderr(output):
                code = main(["--repository", REPO, "--branch", "main", "--event-path", str(event)])
            self.assertEqual(1, code)
            self.assertIn("Triggering update", output.getvalue())
            self.assertNotIn("SECRET_TOKEN", output.getvalue())


if __name__ == "__main__":
    unittest.main()
