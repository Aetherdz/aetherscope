# AetherScope

Scope enforcement for authorized security testing.

Given a scope file (the assets you are allowed to test) and a list of targets,
`aetherscope` tells you, for every target, whether it is **in-scope**,
**out-of-scope** (explicitly denied), or **unknown**. It is built to be piped:
feed it a subdomain list, keep only what is safe to test, and generate a
JSON or Markdown report alongside.

## Features

- Parse a scope file supporting:
  - exact hosts (`example.com`)
  - wildcard domains (`*.example.com`)
  - negations / exclusions (`!secret.example.com`, `!*.example.com`)
  - host with port (`example.com:8080`)
  - URL rules with scheme and path (`https://api.example.com/v1`)
  - IP addresses (`203.0.113.5`)
  - CIDR ranges (`10.0.0.0/24`)
  - comments (`#` and `;`) and blank lines
- Classify targets as `in-scope` / `out-of-scope` / `unknown` / `error`.
- Negation rules always win over inclusion rules.
- Pipe a list of targets and keep only in-scope entries.
- Exit codes for scripting: `0` in-scope, `1` out-of-scope, `2` unknown, `3` error.
- JSON and Markdown reports.

## Install

```bash
pip install .
# or from source
python -m aetherscope --version
```

## Usage

### check

Classify targets against a scope file:

```bash
aetherscope -s scope.txt check api.example.com admin.example.com
# api.example.com: in-scope
# admin.example.com: in-scope
```

Read targets from stdin:

```bash
cat hosts.txt | aetherscope -s scope.txt check
```

JSON output:

```bash
aetherscope -s scope.txt check --json example.com
```

### filter

Keep only in-scope targets (piping-friendly):

```bash
cat recon_subs.txt | aetherscope -s scope.txt filter > in_scope.txt
```

### parse

Show the parsed rules:

```bash
aetherscope -s scope.txt parse
```

### report

Build a report:

```bash
aetherscope -s scope.txt report --format json --input targets.txt -o report.json
aetherscope -s scope.txt report --format markdown --input targets.txt -o report.md
```

The scope file may be given as `-` to read it from stdin, and the target list
may be given as `-` to read it from stdin.

## Example scope file

```text
# program scope
*.example.com
!secret.example.com
example.org/invoice
10.0.0.0/24
203.0.113.5
```

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Aether-DZ.