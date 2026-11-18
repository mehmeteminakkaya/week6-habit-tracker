# Week 6 — Habit Tracker: guardrails, two features, human vs AI review

A tiny FastAPI + SQLite habit tracker from the course starter, extended with **two features
on branches**, deterministic **guardrails**, a **line-by-line manual review** of each diff,
and an **AI review** to compare against.

## Quickstart

```bash
pip install -r requirements.txt
python -m pytest          # 20 tests
uvicorn main:app --reload # http://localhost:8000/docs
```

Python 3.10+.

## Guardrails

| Check | Command | Catches |
| --- | --- | --- |
| Format | `python -m black --check .` | style drift in diffs |
| Lint | `python -m ruff check .` | unused imports, bugbear patterns, import order, simplifications |
| Tests | `python -m pytest` | regressions (non-zero exit on failure) |

`make check` runs all three; `make format` fixes. CI (`.github/workflows/ci.yml`) runs the
same commands on every push and PR, so a red check is visible before anyone reviews.
Details and the proof that a failing test fails the build: [`docs/guardrails.md`](docs/guardrails.md).

## Endpoints

Starter:

- `POST /habits` `{ "name": "Read 20 minutes" }`
- `GET /habits`
- `POST /habits/{id}/checkin` `{ "day": "2026-09-22" }`
- `GET /habits/{id}/checkins`

Added in this week's two PRs:

### `GET /habits/{id}/streak` — task 1

Current run of consecutive days with a check-in, counting back from **today** (the spec's
"up to and including today"). A missing check-in today means a streak of 0, even if
yesterday was checked.

```json
{"habit_id": 1, "streak": 3}
```

- Unknown habit → `404 {"detail": "unknown habit"}`.
- Duplicate check-in rows on one day count once (dates are collected in a set).
- An unparsable `day` row is skipped, not a 500 — write-time validation is task 2 and
  deliberately out of scope here.

### `GET /habits/{id}/summary` — task 3

Check-ins in the **last seven calendar days, today included** (`today-6 .. today`).

```json
{"habit_id": 1, "count": 4, "window_start": "2026-09-19", "window_end": "2026-09-25"}
```

- The count is **distinct days**, not rows: a habit checked twice today counts as 1.
  The API allows duplicate rows (no uniqueness constraint), and reporting "9 check-ins in
  a week" would be meaningless.
- Unknown habit → 404; unparsable rows skipped; future-dated check-ins are outside the
  window (`start <= day <= end`).
- The window bounds are returned so the caller never has to infer which seven days counted.

## Branches, PRs and reviews

| Branch | Feature | PR | Manual review |
| --- | --- | --- | --- |
| `feature/streak` | task 1, `GET /habits/{id}/streak` | [#1](https://github.com/mehmeteminakkaya/week6-habit-tracker/pull/1) | [`docs/reviews/feature-1-streak.md`](docs/reviews/feature-1-streak.md) |
| `feature/weekly-summary` | task 3, `GET /habits/{id}/summary` | [#2](https://github.com/mehmeteminakkaya/week6-habit-tracker/pull/2) | [`docs/reviews/feature-2-summary.md`](docs/reviews/feature-2-summary.md) |

Each branch carries two commits: the feature as the agent first produced it, then the
review-driven fix. The review documents list the blocking findings (unknown habit returned
200; one malformed row 500'd the endpoint), the test gaps that were closed, and the
trade-offs that were accepted instead of fixed.

## Layout

```
main.py                    app + the two new endpoints
test_main.py               starter tests
tests/test_streak.py       9 streak tests
tests/test_summary.py      8 summary tests
conftest.py                per-test SQLite isolation
docs/TASKS.md              course task list
docs/guardrails.md         guardrail commands + failing-build proof
docs/reviews/              manual review notes per PR
pyproject.toml             black / ruff / pytest config
Makefile, .github/         local + CI entry points
writeup.md                 human vs AI review comparison, what I learned
```
