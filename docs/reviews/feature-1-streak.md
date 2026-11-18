# Manual review — feature 1 (`feature/streak`)

Reviewer: me, line by line over `git diff main...feature/streak`, against
`docs/TASKS.md` task 1. Reviewed commit `fe510a9`. Checklist: correctness, error handling,
naming, API shape, test gaps, data assumptions.

## Findings

### 1. Unknown habit returns 200 with an empty streak — blocking

`GET /habits/99999/streak` returned `{"habit_id": 99999, "streak": 0}`. Every other
endpoint treats a missing habit as a 404 (`add_checkin` does), so a client cannot tell
"this habit has no streak yet" from "this habit does not exist". Fixed with the same
lookup `add_checkin` uses.

### 2. A malformed `day` row crashes the endpoint with a 500 — blocking

`date.fromisoformat` was called inside a set comprehension over every row. Task 2
(validation) is not implemented in this PR, so anything can be in `checkins.day`; one junk
row turned the whole endpoint into an unhandled `ValueError` (traceback: `main.py:104`).
Fixed by parsing row by row and skipping what cannot be parsed. The proper prevention is
validation at write time (task 2, deliberately out of scope), so the read path is defensive
instead.

### 3. Tests only covered the happy path — test gap

The diff had two tests (3-day run, empty). Nothing pinned the behaviours that make the
feature correct:

- a gap in the run must stop the count (`today`, `today-1`, `today-3` → 2);
- a missing check-in **today** makes the current streak 0, even if yesterday was checked
  (the spec says "up to and including today");
- duplicate rows on the same day count once;
- unknown habit → 404;
- an unparsable row does not 500.

All five added; the last two failed before the fix and pass after it. That red → green is
the evidence the review found something real, not a cosmetic pass.

## Accepted trade-offs (not changed)

- **The query reads every check-in for the habit.** At a few years of daily check-ins this
  is thousands of rows, which is fine. A bounded window or a SQL side computation would
  need an index on `checkins(habit_id, day)`; adding schema to both feature branches would
  guarantee a merge conflict for no measurable win here, so it stays a follow-up.
- **`date.today()` is the server's local date.** `day` is a naive ISO date with no
  timezone, so this is the only sensible reading; documented in `_today()`'s docstring.
  Worth noting in the writeup as an assumption the AI reviewer may not share.

## Not a finding

`{"habit_id": ..., "streak": ...}` matches the shape `add_checkin` already returns
(`{"habit_id": ..., "day": ...}`), and the `_today()` seam is what makes the tests
deterministic without freezing the clock globally.
