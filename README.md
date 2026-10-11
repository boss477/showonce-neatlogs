# ShowOnce

Show your agent the job once. It compiles a walkthrough into a workflow contract, runs it with traced steps, verifies each contract, and recovers from failures with checkpointed context.

## The demo wow moment

The implement worker receives a bug report, creates a Linear issue, changes the sample repo, and hits an injected failing test. It then calls the Neatlogs MCP: `search_traces` finds the failed run and `get_trace_context` reads the span tree. ShowOnce uses that evidence to retry from an Entire checkpoint, reruns the test, and produces a draft Slack/Linear update for human approval.

Set `NEATLOGS_PROJECT_KEY` to use live Neatlogs MCP. With no key, the same sequence runs with clearly labelled MOCK trace context; no fake production result is reported.

### Live integrations

Copy `.env.example` to `.env` and set `NEATLOGS_PROJECT_KEY`, `SLACK_BOT_TOKEN`, and `LINEAR_API_KEY`. ShowOnce then queries Neatlogs MCP, posts to Slack, and creates Linear issues. Leave any key blank to use the labelled MOCK adapter. External updates should be run as drafts during the demo; use a human approval step before sending production messages.

### Slack → Linear → fix → Slack/Teams pipeline

```powershell
python cli.py watch            # poll Slack every 15s; --once for a single pass
python cli.py handle "bug: add(2,3) returns -1"   # run one report without reading Slack
python cli.py inject-bug       # put the sample bug back to demo again
```

For each new top-level Slack message containing `SLACK_TRIGGER` (default `bug`), ShowOnce creates a Linear issue, acknowledges in the Slack thread, fixes `sample_repo`, runs its real test, then closes the Linear issue (moves it to the team's Done state with a comment) and replies "Code has been fixed" in the thread. It also posts to Teams if `TEAMS_WEBHOOK_URL` is set. If the test still fails, the issue stays open with the test output attached. `watch` starts from "now", so older channel history is not processed; its position is kept in `evidence/slack_watch_state.json`.

## Architecture

```mermaid
flowchart LR
  T[Teach walkthrough] --> C[Compile workflow.yaml]
  C --> R[Run coordinator]
  R --> V[Verify code rules + loops + judge]
  V -->|failed| P[Entire checkpoint]
  P --> F[Diagnose + fix + resume]
  F --> V
  V --> L[Failure memory]
```

## Run

```powershell
python -m pip install -r requirements.txt
python cli.py demo
python evals/run_recovery.py
```

Open `ui/index.html` in a browser for the controlled AG-UI-style Control Room demo. It streams the recovery story visually: failed test → Neatlogs trace inspection → Entire checkpoint → human approval → passing retry. The static UI is dependency-free; its event names and flow are ready to be replaced with a live AG-UI transport when the backend is deployed.

Mock Slack and Linear adapters are labelled `MOCK` in code. The sample repo fix and test are real. Set `OPENAI_API_KEY` only when connecting an LLM compiler/judge; secrets are gitignored.

## Sponsor tools

- neatlogs: `showonce.observability.init_tracing()` initializes tracing and each coordinator step is a span. See `evidence/neatlogs_dev_log.md` for two found → fixed → verified entries.
- Entire: installed with CLI 0.11.4, enabled for Codex in `.entire/settings.json`, and used for repository checkpoints. The implement worker is configured by `entire enable --agent codex` in its own checkout. `evidence/entire/` stores retry context snapshots. The runtime fallback is local checkpoint JSON because the worker cannot assume an authenticated Entire API.
- cfo.ai: `evidence/business_plan.md` is the requested placeholder.
- AG-UI / CopilotKit: the control room uses the AG-UI event-driven model and controlled generative UI cards for timeline, trace evidence, checkpoint state, diffs, tests, and approvals. AG-UI is complementary to MCP: MCP supplies tools, AG-UI supplies the user-facing event stream.

### Retry and restored context

Example checkpoint: `evidence/entire/retry-fix-1.json` records the failed step, failure, lessons, and the decision to restore that context before retrying. The retry then re-runs verification from the restored step rather than restarting the workflow.

## Measured results and limitations

Run `python evals/run_recovery.py`; it writes timestamped JSON and CSV without overwriting prior runs. The bundled harness is deterministic and offline, so its token/cost fields are zero and are not evidence of LLM performance. Any unreachable model call must be marked `INVALID` and excluded. This prototype does not claim to solve recovery; it measures the recovery behavior available in each run.
