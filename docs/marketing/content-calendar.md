# Content calendar

Ten pieces. Each one can be written from the repository without a live
provider. "Proof" is the command or file a reader can run or open.
Publish none of them until the launch gate in `launch-plan.md` is met.
Order is a proposal.

| # | Title | Audience | Intent | Angle | Proof | CTA |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Run a coding handoff with no API key | Newcomer | Wants to try something today | The demo path, including what it refuses to do | `triadmux run --demo` | Install from the README |
| 2 | What `doctor` means by ready | Script author | Wants to detect CLIs safely | Found is not enabled. Nothing is launched. | `triadmux doctor` and `inventory.py` | Read supported-CLIs |
| 3 | Dry run, then a record | Cautious user | Wants to know what gets written | `--dry-run` writes nothing. A real synthetic run writes one JSON file. | README flags and `workflow.py` | Run the dry run |
| 4 | Where the bytes went | Operator | Wants limits | Input cap includes the JSON envelope. Output cap stops later stages. | CLI help and provider errors | Set `--max-input-bytes` |
| 5 | A shared clock for three stages | Operator | Timeout behavior | `--total-timeout` and `budget_exhausted` | `tests/test_budget.py` | Read the error sentence |
| 6 | Secrets that must not land in the record | Security reader | Redaction | Names and the 12-character floor. What is not redacted. | `redaction.py`, README | Read SECURITY.md |
| 7 | The child does not inherit your keys | Security reader | Environment boundary | Allowlist, and the macOS CI failure as an open bug, stated plainly | `provider.py`, the 2026-11-19 Actions run | Follow the issue once filed |
| 8 | Recover a run after the controller dies | Operator | Crash behavior | POSIX lock, `runs`, `recover`. Recovery does not resume the task. | README recover paragraph | Try recover on a fixture |
| 9 | Why the live adapters are off | Contributor | Roadmap honesty | Parsers exist. Workflow does not accept them as results. | `docs/provider-contracts.md` | Read the contract doc |
| 10 | Claude Swap is the inspiration, not the codebase | Evaluator | Comparison | Pinned commit, no copied source, different job | `docs/upstream-review.md` | Read the review |

Pieces 7 and 9 are the ones that keep a launch from overclaiming. Write
them before piece 1 is posted anywhere outside the repository.
