#!/usr/bin/env python3
"""
An AI agent that fixes a failing PR build — and NOTHING ELSE.

Scope (enforced): it operates on ONE pull request. It reads only that PR's
failing build logs, edits only the PR branch's source, and pushes only to that
PR branch. It never touches main. It loops until the PR's build is green or a
hard attempt cap is hit.

Usage: python agent/fix_pr.py <PR_NUMBER>
"""
import subprocess
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO = "sambitmallick/ai-pr-build-fixer"
WORKFLOW = "build"
CLAUDE = r"C:\Users\sambi\.local\bin\claude.exe"
MAX_ATTEMPTS = 6

PR = sys.argv[1] if len(sys.argv) > 1 else "1"


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def pr_branch(pr):
    r = sh(["gh", "pr", "view", pr, "-R", REPO, "--json", "headRefName", "-q", ".headRefName"])
    return r.stdout.strip()


def latest_run_id(branch):
    r = sh(["gh", "run", "list", "-R", REPO, "--branch", branch, "--workflow", WORKFLOW,
            "--limit", "1", "--json", "databaseId", "-q", ".[0].databaseId"])
    return r.stdout.strip()


def wait_for_run(branch, after_id=None, timeout=420):
    """Wait for a build run (newer than after_id) to complete; return (id, conclusion)."""
    start = time.time()
    while time.time() - start < timeout:
        r = sh(["gh", "run", "list", "-R", REPO, "--branch", branch, "--workflow", WORKFLOW,
                "--limit", "1", "--json", "databaseId,status,conclusion"])
        import json
        rows = json.loads(r.stdout or "[]")
        if rows:
            run = rows[0]
            rid = str(run["databaseId"])
            if after_id and rid == after_id:
                time.sleep(6); continue  # still the old run, wait for the new one
            if run["status"] == "completed":
                return rid, run["conclusion"]
        time.sleep(8)
    return None, "timeout"


def failing_errors(run_id):
    r = sh(["gh", "run", "view", run_id, "-R", REPO, "--log-failed"])
    lines = [ln for ln in r.stdout.splitlines() if "error TS" in ln]
    # strip the gh log prefix (job\tstep\ttimestamp\t...) -> keep from "src/"
    cleaned = []
    for ln in lines:
        i = ln.find("src/")
        cleaned.append(ln[i:] if i != -1 else ln.strip())
    return "\n".join(dict.fromkeys(cleaned))  # de-dup, keep order


PROMPT = """You are an autonomous build-fixer working on ONE pull request. The PR's build is \
failing. The build command is `npm run build`, which runs `tsc` in TypeScript strict mode.

Here are the exact compiler errors:
{errors}

Fix the ACTUAL root cause of each error in the source files under src/. Rules:
- Do NOT silence errors with `any`, the non-null assertion `!`, or `@ts-ignore` — fix the real cause.
- Do NOT delete code or weaken behavior just to make it compile.
- Only edit files under src/. Do not touch config, CI, or unrelated files.
- Make the smallest correct change, then stop. Do not run git or push."""


def claude_fix(errors, repo_dir):
    prompt = PROMPT.format(errors=errors)
    print("   → handing the errors to the agent (claude -p, $0 local)…", flush=True)
    p = subprocess.run([CLAUDE, "-p", prompt, "--dangerously-skip-permissions"],
                       cwd=repo_dir, capture_output=True, text=True, timeout=600)
    tail = (p.stdout or "").strip().splitlines()[-4:]
    for ln in tail:
        print("     " + ln, flush=True)


def main():
    import os
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    branch = pr_branch(PR)
    print(f"agent: fixing build on PR #{PR}  (branch: {branch})  repo: {REPO}\n", flush=True)
    # make sure we're on the PR branch locally
    sh(["git", "fetch", "origin", branch], cwd=repo_dir)
    sh(["git", "checkout", branch], cwd=repo_dir)
    sh(["git", "reset", "--hard", f"origin/{branch}"], cwd=repo_dir)

    last_id = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"── attempt {attempt}/{MAX_ATTEMPTS} " + "─" * 40, flush=True)
        print("   waiting for the PR build to finish…", flush=True)
        rid, concl = wait_for_run(branch, after_id=last_id)
        print(f"   build run {rid}: {concl}", flush=True)
        if concl == "success":
            print(f"\n✅ PR #{PR} build is GREEN. The agent is done.", flush=True)
            return
        if concl != "failure":
            print(f"   unexpected conclusion ({concl}); stopping.", flush=True)
            return
        errors = failing_errors(rid)
        print("   compiler errors:", flush=True)
        for ln in errors.splitlines():
            print("     " + ln, flush=True)
        claude_fix(errors, repo_dir)
        # commit + push ONLY to the PR branch
        sh(["git", "add", "-A"], cwd=repo_dir)
        c = sh(["git", "commit", "-m", f"fix(build): resolve tsc errors (agent attempt {attempt})"], cwd=repo_dir)
        if "nothing to commit" in (c.stdout + c.stderr):
            print("   agent made no change; stopping to avoid a loop.", flush=True)
            return
        sh(["git", "push", "origin", branch], cwd=repo_dir)
        print("   pushed the fix to the PR branch → CI re-runs.\n", flush=True)
        last_id = rid
    print(f"\n⛔ Hit the {MAX_ATTEMPTS}-attempt cap without a green build. Handing back to a human.", flush=True)


if __name__ == "__main__":
    main()
