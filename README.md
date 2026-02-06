# AVOT Chassis (Minimal)

This repository is a **minimal, language-agnostic chassis** for AVOTs (Autonomous Voices of Thought).

It includes:
- The canonical AVOT behavioral contract (Markdown)
- A minimal Python base class implementing the contract
- Read-only registry loader + signal ledger adapters (Python)
- A TypeScript interface mirror + adapters (optional)
- A first system test AVOT: **Archivist** (Python), wired to the registry + signal ledger

> This repo is intentionally small. Capabilities live elsewhere; **character lives here**.

## Quick start (Python)

```bash
cd python
python -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
python -m avot_chassis.examples.run_archivist
```

This will:
- Load `registry/avot_registry.yaml`
- Load `registry/signal_ledger.yaml`
- Instantiate AVOT-ARCHIVIST from `headers/AVOT-ARCHIVIST.header.yaml`
- Demonstrate a refusal-safe action attempt
- Append a sample signal entry

## Repo layout

```
contracts/                    # canonical behavioral contract (language-agnostic)
python/avot_chassis/          # python chassis + adapters + example
typescript/                   # TS mirror (optional)
registry/                     # sample registry + signal ledger for local testing
headers/                      # sample AVOT headers for local testing
```

## Notes

- This chassis does not enforce global policy.
- It enables **self-awareness** (identity, lifecycle, permissions) and **structured refusal**.
- Signals are **non-binding observations**.
