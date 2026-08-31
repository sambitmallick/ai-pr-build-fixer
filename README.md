# ai-pr-build-fixer — an AI agent that fixes a failing PR build until it's green

Companion repo to a [DevOps Autopilot](https://www.youtube.com/@DevOpsAutopilot) experiment:
an AI agent that watches **one pull request**, and every time the build fails, reads the
compiler errors, fixes the cause on the PR branch, and pushes — looping until that PR's build
is green. It works. And it shows exactly where a green build stops meaning anything.

`taskkit` is a small strict-TypeScript project. `npm run build` is just `tsc`.

## The agent — [`agent/fix_pr.py`](agent/fix_pr.py)

Scoped to a single PR (it never touches `main`):

```
python agent/fix_pr.py <PR_NUMBER>
```

Each round:
1. `gh pr checks` → is the **build** check failing?
2. `gh run view <id> --log-failed` → the exact `tsc` errors.
3. `claude -p "<errors> … fix the cause, no any/!/@ts-ignore, src/ only" --dangerously-skip-permissions`
   → Claude edits the PR's files (headless, local, **$0**).
4. `git commit && push` to the **PR branch only** → CI re-runs.
5. Wait for the new build. Repeat until green, or hit the **6-attempt cap** (so it can never
   loop forever or burn resources on an unfixable PR).

**Three layers keep it PR-only:** the CI runs `on: pull_request`; the agent reads only that
PR's failing build and pushes only to that PR's branch; the fix-prompt forbids touching config,
CI, `main`, or unrelated files.

## What actually happened (PR #1, "Add a daily priority report")

The PR shipped a feature that didn't compile — **6 real `tsc` errors** (missing imports, an
unused local, a `'top' is possibly undefined`, and a string→number type error). The agent
fixed all of them in **one round**, respecting the guardrail (it handled the undefined case with
`top?.title ?? "none"` — not a lazy `!`), pushed, and the build went **green**. Genuinely good.

### The honest beat: compiles ≠ correct

The agent made the build pass. But the build was never the bug. Look at the cost line:

```ts
const cost = add(RATE_PER_MIN, usd(mins)); // 50¢ flat rate ADDED to a raw minute count
```

The rate is 50¢/**min**, so the intended cost is `rate × minutes`. The code **adds** instead.
For 180 minutes of work the report says **$2.30** — it should be **$90.00**. Off by ~40×.

And `tsc` is perfectly happy: it checks **types**, not **math**. `50 + 180` is a valid number —
just the wrong one. The agent did its job (fix the build); the logic bug was never a build error,
so nothing green ever caught it.

**The rule:** let the agent fix your builds — it's a real unblock. But "the build is green" means
it *compiles*. That's the floor, not the finish line. A human still owns "is this actually right."

---
🎬 Full walkthrough: **[DevOps Autopilot](https://www.youtube.com/@DevOpsAutopilot)**
