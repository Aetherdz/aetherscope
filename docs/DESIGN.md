# AetherScope — Design System

Landing page system for `aetherscope`, in the same family as the HuntPack landing.

## Tokens

| Token | Value |
| --- | --- |
| `--bg` | `#201d1d` |
| `--bg-elevated` | `#302c2c` |
| `--border` | `rgba(15,0,0,.12)` |
| `--border-strong` | `#646262` |
| `--text-1` | `#fdfcfc` |
| `--text-2` | `#9a9898` |
| `--text-3` | `#84848a` |
| `--accent` | `#00e063` |
| `--ok` | `#30d158` |
| `--err` | `#ff3b10` |
| `--warn` | `#ff9f0a` |

## Rules

- Mono stack: `Berkeley Mono, ui-monospace, SFMono-Regular, Menlo, monospace`.
- Radius `4px`, flat surfaces, border-only separation.
- Transitions on color only, `120ms`.
- No reveal-on-scroll animation.
- `docs/.nojekyll` present (Pages serves raw files).
- Contrast: `--text-3` on `--bg` ≥ 4.5:1; `--accent` on `--bg` ≥ 7:1.

## Structure

- `docs/DESIGN.md` — this file (source of truth).
- `docs/index.html` — hero: "Scope that keeps receipts." + feature grid + terminal demo.
- `docs/assets/styles.css` — tokens + layout.
- `docs/assets/app.js` — interactive terminal typing demo.
