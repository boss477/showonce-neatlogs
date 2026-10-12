# Live NVIDIA + Linear demo — 2026-10-12

Real issue: [FAW-7](https://linear.app/fawaz123/issue/FAW-7/showonce-live-demo-add2-3-returns-1-instead-of-5)

- The sample `add(2, 3)` bug was injected into a temporary repo copy. The real subprocess test failed before repair.
- The first NVIDIA request used `meta/llama-3.1-8b-instruct` and returned HTTP 410. ShowOnce left FAW-7 open and recorded the failure in a comment.
- An operator selected an available model for the retry, which reused FAW-7 and called `nvidia/nemotron-3.5-lightning-30b-a3b`. NVIDIA returned `return a + b` in one model call (461 total tokens).
- The patch was applied only to the temporary copy. The real subprocess test passed. ShowOnce added a verification comment and moved FAW-7 to Done. A read-only Linear query confirmed the state and both comments.
- Slack intake was not used: the current bot token lacks `channels:read` and cannot access the historical demo channel. No production repo was changed. An Entire checkpoint or hosted Neatlogs trace was not verified for this run.
