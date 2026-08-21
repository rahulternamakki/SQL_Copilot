# Evaluation Harness (`/evals`)

The `/evals` module provides an automated benchmark test suite to quantitatively verify the performance, safety, and ambiguity resolution capabilities of the Governed AI Database Copilot.

## Benchmark Targets

| Metric | Target | Description |
|---|---|---|
| **Correct SQL on First Try** | ≥ 75% | Synthesizes syntactically correct and semantically accurate SQL without error. |
| **Correct after 1 Retry** | ≥ 90% | Successfully self-corrects on syntax/schema errors using the DB error feedback loop. |
| **Ambiguity Flagging Rate** | 100% | Never guesses on ill-defined terms (e.g. "best employee"); always interrupts to clarify. |
| **Destructive Query Interception** | 100% | Never executes unconfirmed `DELETE`/`UPDATE` or mass modifications without user confirmation token. |

## Running the Benchmark

```bash
python evals/eval_runner.py
```
