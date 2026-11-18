# Week 6 writeup — guardrails, two features, and what an AI reviewer caught that I did not

Two features from `docs/TASKS.md` (task 1, streak; task 3, weekly summary) were
implemented on branches and put through the same pipeline: **deterministic guardrails →
my line-by-line review → an independent AI review**. Both PRs are merged, so `main` has the
features and 20 passing tests.

> **Tooling note:** CodeRabbit was not installed on the repository (it needs the GitHub App
> on the account, which I did not have set up for this run). The AI review is an
> **independent reviewer pass**: a separate AI agent that got only the PR diff, the app and
> `docs/TASKS.md`, and was told not to read my review notes. Its review is posted verbatim
> on each PR ([#1](https://github.com/mehmeteminakkaya/week6-habit-tracker/pull/1#issuecomment-6977503377),
> [#2](https://github.com/mehmeteminakkaya/week6-habit-tracker/pull/2#issuecomment-6977503837)).
> CodeRabbit can be added later with `@coderabbitai review`; the comparison below would not
> change shape, only the reviewer's name.

## Part I — guardrails

Three layers, all failing the build on error, all wired into CI:

| Layer | Command | What it caught in practice |
| --- | --- | --- |
| Format | `python -m black --check .` | the starter erases double blank lines and wraps at 100; without it every diff carries style noise |
| Lint | `python -m ruff check .` | unused imports and the `B`/`UP`/`SIM` families; clean on all commits |
| Tests | `python -m pytest` | 10 tests at the start of the week, 20 after both features |

Proof that a failing test fails the build is in
[`docs/guardrails.md`](docs/guardrails.md) — a throwaway failing test exits 1 and CI would
turn it into a red check on the PR. The more useful guardrail turned out to be **test
isolation**: the starter shares one `habits.db`, so habits leaked between tests. `conftest.py`
points `main.DB_PATH` at a per-test temporary file, which is what let both feature branches
add tests without stepping on each other's data.

## Part II — how the two reviews compared

### PR #1 — streak

| Finding | My review | AI review | Outcome |
| --- | --- | --- | --- |
| Unknown habit returned `200 {"streak": 0}` | **blocking**, found by reading the diff | confirmed as handled after the fix | fixed in commit 2 |
| One malformed row 500'd the endpoint | **blocking**, reproduced by a test | confirmed, asked for a log | fixed; the "log it" half deferred |
| No tests for gap / missing today / duplicate day | found, 5 tests added | — | fixed |
| "Today" is the server's local date while `day` is client-sent | noted as an accepted trade-off | rated **major**: a UTC server and a UTC−8 user disagree about the date around midnight | kept, but the contract moved into the endpoint docstring |
| Streak reads 0 when today has no check-in | passed as spec-compliant | rated **major**: genuinely ambiguous half of "up to and including today" | kept, pinned by a test, named in the docstring |
| No test that a future day does not count | missed | found | test added |
| PR description claimed "14 passed (3 + 11)" | missed | found: it does not reproduce | description corrected |

### PR #2 — weekly summary

| Finding | My review | AI review | Outcome |
| --- | --- | --- | --- |
| Unknown habit → 200 with `count: 0` | blocking, fixed | confirmed handled | fixed |
| Malformed row → 500 | blocking, fixed | confirmed, asked for a log | fixed; log deferred |
| Window edges (`today-6` in, `today-7` out), future rows, duplicates untested | found, 5 tests added | confirmed correct and tested | fixed |
| Distinct days vs rows | decided and documented | agreed with the rationale | unchanged |
| **"The two branches merge without conflict"** | **I asserted it without testing it** | **falsified it**: merging both produces three content conflicts in `main.py`; only the identical `_today` block merges cleanly | description corrected, branch rebased onto merged `main`, conflict resolved, no duplicated preamble |
| No cross-habit isolation test | missed | found by mutation: deleting `WHERE habit_id = ?` kept all tests green | test added |
| Sibling `GET /habits/{id}/checkins` returns `200 []` for unknown habits | missed | found | acknowledged as pre-existing, out of scope |
| Description count wrong | missed | found | corrected |

### Where each reviewer was better

**The human pass was better at finding actual defects.** The two blocking bugs — 200 for an
unknown habit, 500 on an unparsable row — were both found by reading the code and reproducing
them with a test, and the AI review treated them as already handled because by then they
were. The human pass also caught the test gaps that made the feature correct rather than
merely passing (gap in the run, missing today, duplicate day, boundary).

**The AI pass was better at adversarial verification.** It did not trust the description: it
merged the two branches and found the conflict I had only assumed away, and it ran mutation
checks (delete a `WHERE` clause, delete the `$` branch of a regex) to prove that tests would
stay green if the code regressed. That is a different skill from reading a diff, and it is
exactly where I was lazy: I claimed mergeability from memory instead of from `git merge`.

**Both missed the same thing:** neither review questioned the timezone contract of `day` until
the AI raised it as a risk, and neither added the cross-habit isolation test until the AI's
mutation check demanded it.

## What I learned

Guardrails and LLM review catch different classes of problem: `black`/`ruff`/`pytest` tell
you the code is well-formed and does what its tests say, while a reviewer tells you the tests
say the wrong thing. The most valuable single finding of the week was not a bug but a false
claim in my own PR description — I wrote that two independent branches would merge cleanly
without ever running `git merge`, and an AI reviewer that actually ran it caught me. That
changed how I write PR descriptions: claims about behaviour need a command behind them, the
same as code. The second lesson is about trusting AI review: it is strong at mechanical
verification (merges, mutations, boundary probes) and weak at understanding what the author
already fixed, so the honest workflow is to run it *after* the human pass and treat its
findings as a checklist of things to verify, not as a verdict.
