import json
import subprocess
import unittest
from tooling.repo import matches_gap


class CompilerGapMatching(unittest.TestCase):
    def setUp(self):
        self.diagnostic = {
            "definition": "pinned-definition", "code": "application.source.syntax",
            "category": "syntax", "stage": "parse", "outcome": "not_submitted",
            "evidence": "local_before_dispatch", "location": {
                "source": "root/build.transit", "line": "1", "byte_column": "23"},
            "facts": [{"field": "native_cause", "value": {"text": "InvalidSourceSyntax"}}],
        }
        self.expected = {
            "definition": "pinned-definition", "code": "application.source.syntax",
            "category": "syntax", "stage": "parse", "native_cause": "InvalidSourceSyntax",
            "source": "root/build.transit", "line": "1", "byte_column": "23",
        }

    def result(self, code=1, stderr=""):
        return subprocess.CompletedProcess([], code, json.dumps(self.diagnostic), stderr)

    def test_only_exact_compiler_diagnostic_matches(self):
        self.assertTrue(matches_gap(self.result(), self.expected)[0])
        for field in ["definition", "code", "category", "stage"]:
            with self.subTest(field=field):
                changed = dict(self.expected, **{field: "different"})
                self.assertFalse(matches_gap(self.result(), changed)[0])
        self.diagnostic["location"]["line"] = "2"
        self.assertFalse(matches_gap(self.result(), self.expected)[0])

    def test_success_crash_and_runtime_failure_cannot_be_allowed_failures(self):
        for code in [0, 2, -11, 137]:
            self.assertFalse(matches_gap(self.result(code), self.expected)[0])
        self.diagnostic["outcome"] = "unknown"
        self.assertFalse(matches_gap(self.result(), self.expected)[0])

    def test_malformed_output_or_extra_stderr_does_not_match(self):
        self.assertFalse(matches_gap(self.result(stderr="unexpected failure"), self.expected)[0])
        for text in ["", "not json", "{}", "[]", json.dumps(self.diagnostic) + "\n{}"]:
            self.assertFalse(matches_gap(subprocess.CompletedProcess([], 1, text, ""), self.expected)[0])


if __name__ == "__main__":
    unittest.main()
