# TriadMux

TriadMux is a local-first CLI for coordinating coding assistants. Version
**0.0.0** demonstrates a leader, reviewer, and synthesis handoff using
deterministic synthetic stages. It keeps run records on the local machine.

## Quick start

Requires Python 3.12 or later. From a checkout:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
triadmux doctor
triadmux run --demo "Review the project's build instructions"
triadmux status <run-id>
```

`doctor` locates Codex, Claude Code and Grok executables on PATH. The demo
works without any of them installed or authenticated. Run records can contain
your task and result. They live in the ignored `.triadmux/` directory by
default. Use `triadmux --state-dir PATH` to select another location. An
interrupted run remains inspectable. There is no automatic replay.

The same handoff can run through the bundled synthetic subprocess adapter.
Each stage has its own timeout and stdout limit. Status records include a
failure code when the provider exits early, exceeds a limit, or returns an
invalid response.

```sh
triadmux run --provider synthetic --timeout 5 --max-output-bytes 65536 "Review the build"
```

The adapter currently runs only the bundled synthetic worker. Live provider
support will require workspace isolation and process-tree cleanup.

Run the tests with `PYTHONPATH=src python -m unittest discover -s tests -v`.
See [the roadmap](ROADMAP.md) for alpha, beta and release gates and
[the to-do list](TODO.md) for the next implementation slice.

TriadMux is independently maintained and released under the [MIT license](LICENSE).

See the [upstream review](docs/upstream-review.md) and
[provider contract inventory](docs/provider-contracts.md) for the adapter plan.
