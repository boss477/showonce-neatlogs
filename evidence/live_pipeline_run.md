# Live pipeline run: 2026-10-12

First end-to-end run of `python cli.py watch --once` against real Slack and Linear.
Checked independently afterwards via the Slack and Linear APIs.

| Step | Observed |
|---|---|
| Pre-flight | `python cli.py check`-equivalent read-only checks passed: Slack auth, channel membership, history read; Linear viewer and team |
| Trigger | One test message containing `bug` posted in `#showonce-demo` (channel `C0C8LUM4VU1`) |
| Linear | Issue `FAW-5` created, then moved to **Done** (state type `completed`) with an automated fix comment |
| Slack | Two bot replies in the report's thread: the acknowledgement naming `FAW-5`, then "Code has been fixed. Tests pass and FAW-5 is closed in Linear." |
| Repo | `sample_repo/test_buggy.py` failed with `AssertionError` before the run and passed after it |
| Neatlogs | Not exercised: no project key configured, so no hosted trace exists for this run |

Limitations: the fix is the sample repo's deterministic one-line patch, not a model-generated repair.
No tokens, user names or private message contents are recorded here.
