# ShowOnce demo video script (2:00)

Use the recorded FAW-7 run and its actual Linear history. Do not reenact the
first HTTP 410 as if it happens during a fresh successful run. The successful
retry used an operator-selected available NVIDIA model; ShowOnce did not read
a Neatlogs trace or restore an Entire checkpoint in this run.

| Time | Show | Say |
| --- | --- | --- |
| 0:00–0:12 | [FAW-7](https://linear.app/fawaz123/issue/FAW-7/showonce-live-demo-add2-3-returns-1-instead-of-5): failure comment, then Done state. | “What should an AI fixer do when *it* fails? ShowOnce keeps the ticket open. It earns ‘Done’ with a passing test.” |
| 0:12–0:27 | The sample `add` function returning `a - b`; the failing test. | “Our sample bug is small enough to inspect: `add(2, 3)` returns minus one. The repository’s test fails in a fresh Python process.” |
| 0:27–0:43 | FAW-7 description and first comment. | “ShowOnce created this real Linear issue. Its first NVIDIA request returned HTTP 410. The issue stayed open, and the failure was recorded instead of being hidden.” |
| 0:43–1:05 | Recorded retry output: same issue ID, NVIDIA model, `return a + b`. | “We selected an available NVIDIA model and retried the same issue. One real model call proposed this one-line change.” |
| 1:05–1:25 | Before/after code and FAIL → PASS test result. | “ShowOnce applied that line to a temporary repo copy and ran the real test again. It passed. That result comes from the test process, not the model’s confidence.” |
| 1:25–1:43 | FAW-7 marked Done; verification comment. | “Only after verification did it close FAW-7. The issue retains both the failed attempt and the successful proof, so anyone can audit what happened.” |
| 1:43–2:00 | Title card: **Failure stays open. Proof closes the loop.** | “That is ShowOnce’s promise: an AI repair is an attempt; a passing test is evidence. When an attempt fails, the work stays visible.” |

Recording notes:

- The run is documented in [live_nvidia_linear_run.md](../evidence/live_nvidia_linear_run.md). Use the real Linear issue and actual terminal output; do not fabricate a Slack report or trace view.
- `python cli.py demo-live-linear` creates a **new** real Linear issue. For a fresh recording, capture that new issue ID and update the video. Do not rerun against FAW-7 merely to recreate the original failure.
- Slack intake is still blocked by the bot's channel permissions. Neatlogs MCP authentication passed, but a hosted trace for this run has not been verified. Entire has no verified checkpoint for this run. Do not claim those actions in the voiceover yet.
