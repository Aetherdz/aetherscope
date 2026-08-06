import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

from aetherscope.cli import main

SCOPE = "*.example.com\n!secret.example.com\n10.0.0.0/24\n"


class CliCheckTest(unittest.TestCase):
    def invoke(self, args, stdin=None):
        out = io.StringIO()
        code = 0
        real_stdin = sys.stdin
        if stdin is not None:
            sys.stdin = io.StringIO(stdin)
        try:
            with redirect_stdout(out):
                try:
                    code = main(args)
                except SystemExit as exc:
                    code = exc.code if isinstance(exc.code, int) else 0
        finally:
            sys.stdin = real_stdin
        return code, out.getvalue()

    def test_check_in_scope_exit_zero(self):
        code, out = self.invoke(["-s", "-", "check", "api.example.com"], stdin=SCOPE)
        self.assertEqual(code, 0)
        self.assertIn("api.example.com: in-scope", out)

    def test_check_out_of_scope_exit_one(self):
        code, out = self.invoke(["-s", "-", "check", "secret.example.com"], stdin=SCOPE)
        self.assertEqual(code, 1)
        self.assertIn("out-of-scope", out)

    def test_check_json(self):
        code, out = self.invoke(
            ["-s", "-", "check", "--json", "a.example.com", "10.0.0.9"], stdin=SCOPE
        )
        data = json.loads(out)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["verdict"], "in-scope")
        self.assertEqual(data[1]["verdict"], "in-scope")

    def test_filter(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as handle:
            handle.write(SCOPE)
            scope_path = handle.name
        try:
            code, out = self.invoke(
                ["-s", scope_path, "filter"],
                stdin="a.example.com\nsecret.example.com\nexternal.org\n",
            )
        finally:
            os.unlink(scope_path)
        self.assertEqual(code, 0)
        lines = out.strip().splitlines()
        self.assertEqual(lines, ["a.example.com"])

    def test_parse(self):
        code, out = self.invoke(["-s", "-", "parse"], stdin=SCOPE)
        self.assertEqual(code, 0)
        self.assertIn("*.example.com", out)

    def test_report_json(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as handle:
            handle.write(SCOPE)
            scope_path = handle.name
        try:
            code, out = self.invoke(
                ["-s", scope_path, "report", "--format", "json"],
                stdin="a.example.com\nother.net\n",
            )
        finally:
            os.unlink(scope_path)
        self.assertEqual(code, 0)
        report = json.loads(out)
        self.assertEqual(report["summary"]["in-scope"], 1)
        self.assertEqual(report["summary"]["unknown"], 1)

    def test_version(self):
        code, out = self.invoke(["--version"])
        self.assertEqual(code, 0)
        self.assertIn("aetherscope", out)


if __name__ == "__main__":
    unittest.main()
