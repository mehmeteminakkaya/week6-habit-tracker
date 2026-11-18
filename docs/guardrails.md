# Guardrails

The point of this week's first part is that a review is only as good as the checks that
run before it. Three layers, all failing the build on error:

| Layer | Command | What it catches |
| --- | --- | --- |
| Format | `python -m black --check .` | style drift, so diffs stay about behaviour |
| Lint | `python -m ruff check .` | unused imports, shadowing, bugbear patterns (`B`), modernisation (`UP`), simplifications (`SIM`), import order (`I`) |
| Tests | `python -m pytest` | regressions; non-zero exit on any failure |

Windows has no `make`, so the Makefile mirrors the direct commands:

```
make check      ==  python -m ruff check . && python -m black --check . && python -m pytest
make format     ==  python -m black . && python -m ruff check --fix .
```

CI (`.github/workflows/ci.yml`) runs the same three commands on every push and pull
request, so a red check appears on the PR itself before a human or an AI reviewer looks
at it.

## Proof the build fails on a failing test

A throwaway file outside the suite:

```
$ cat /tmp/failcheck/test_broken.py
def test_broken():
    assert 1 == 2

$ python -m pytest /tmp/failcheck/test_broken.py; echo "exit=$?"
FAILED /tmp/failcheck/test_broken.py::test_broken - assert 1 == 2
1 failed in 0.15s
exit=1
```

Same shape for the other two layers: an unused import makes `ruff` exit 1, an unformatted
file makes `black --check` exit 1. CI turns any of those into a failed check on the PR.

## Why the test isolation fixture exists

`starter/main.py` writes `habits.db` next to itself. The starter tests therefore share one
database, so one test's habit leaks into the next and order starts to matter. `conftest.py`
points `main.DB_PATH` at a per-test temporary file (`tmp_path`) and calls `init_db()`. It is
autouse, so every test — existing and new — gets a fresh database.
