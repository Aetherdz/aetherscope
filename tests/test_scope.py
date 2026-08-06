import unittest

from aetherscope.scope import IN_SCOPE, OUT_OF_SCOPE, UNKNOWN, Scope, parse_rule


class ParseRuleTest(unittest.TestCase):
    def test_comments_ignored(self):
        self.assertIsNone(parse_rule("# comment"))
        self.assertIsNone(parse_rule("; semicolon comment"))
        self.assertIsNone(parse_rule("   "))

    def test_bare_host(self):
        rule = parse_rule("example.com")
        self.assertIsNotNone(rule)
        self.assertEqual(rule.kind, "host")
        self.assertEqual(rule.host, "example.com")
        self.assertFalse(rule.excluded)

    def test_wildcard(self):
        rule = parse_rule("*.example.com")
        self.assertEqual(rule.kind, "wildcard")
        self.assertEqual(rule.host, "example.com")

    def test_negation(self):
        rule = parse_rule("!admin.example.com")
        self.assertEqual(rule.kind, "host")
        self.assertTrue(rule.excluded)

    def test_url_rule(self):
        rule = parse_rule("https://api.example.com/v1")
        self.assertEqual(rule.kind, "host")
        self.assertEqual(rule.scheme, "https")
        self.assertEqual(rule.path, "/v1")

    def test_host_port(self):
        rule = parse_rule("example.com:8080")
        self.assertEqual(rule.host, "example.com")
        self.assertEqual(rule.port, "8080")


class ScopeMatchTest(unittest.TestCase):
    def setUp(self):
        self.scope = Scope.from_text(
            "\n".join(
                [
                    "*.example.com",
                    "!secret.example.com",
                    "example.org/invoice",
                    "10.0.0.0/24",
                    "# comment",
                ]
            )
        )

    def test_wildcard_in_scope(self):
        self.assertEqual(self.scope.classify("api.example.com")[0], IN_SCOPE)

    def test_apex_in_scope(self):
        self.assertEqual(self.scope.classify("example.com")[0], IN_SCOPE)

    def test_negation_wins(self):
        verdict, rule = self.scope.classify("secret.example.com")
        self.assertEqual(verdict, OUT_OF_SCOPE)
        self.assertTrue(rule.excluded)

    def test_suffix_not_matched(self):
        self.assertEqual(self.scope.classify("notexample.com")[0], UNKNOWN)

    def test_url_in_scope(self):
        self.assertEqual(self.scope.classify("https://api.example.com/v2")[0], IN_SCOPE)

    def test_url_path_out_of_scope(self):
        self.assertEqual(self.scope.classify("https://example.org/other")[0], UNKNOWN)

    def test_cidr_ip(self):
        self.assertEqual(self.scope.classify("10.0.0.5")[0], IN_SCOPE)

    def test_ip_outside_cidr(self):
        self.assertEqual(self.scope.classify("192.168.1.1")[0], UNKNOWN)

    def test_unknown_host(self):
        self.assertEqual(self.scope.classify("foo.org")[0], UNKNOWN)


class ScopeReprTest(unittest.TestCase):
    def test_rule_count(self):
        self.assertEqual(len(self.scope_rules()), 4)

    def scope_rules(self):
        return Scope.from_text(
            "*.a.com\n!b.a.com\nc.a.com\n10.0.0.1\n"
        ).rules


if __name__ == "__main__":
    unittest.main()
