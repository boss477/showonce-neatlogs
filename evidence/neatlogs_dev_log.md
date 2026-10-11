# neatlogs development log

This log records bugs in ShowOnce found through neatlogs traces.

| Trace link | What was wrong | Fix commit | Trace after fix |
|---|---|---|---|
| `local://pending/loop-detection` | Repeated identical tool calls were not surfaced as a failed verification. | `pending` | `local://pending/loop-detection-fixed` |
| `local://pending/honesty-rule` | A failed judge path could be mistaken for success; verdict handling must degrade to WARN. | `pending` | `local://pending/honesty-rule-fixed` |
| `local://showonce.step.issue` | The installed neatlogs 1.4 API exposes `trace`/`span` as decorators; passing step attributes to `span(...)` raised `TypeError`. | `pending` | `local://showonce.step.issue-fixed` |
