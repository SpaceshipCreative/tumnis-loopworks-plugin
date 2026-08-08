#!/usr/bin/env python3
"""Gated loop state machine with deterministic checks and checkpoints.

Loop YAML (~/.hermes/loops/<name>.yaml):
  name: weekly-report
  goal: "Produce the Monday metrics brief"
  criteria: ["under 400 words"]
  checks: ["test -s /absolute/path/report.md"]  # optional; exit 0 = pass
  max_attempts: 3

Commands: tick | pass | fail | nochange | status | reset
"""
import json
import os
import subprocess
import sys
import time
import yaml

LOOPS = os.path.expanduser("~/.hermes/loops")
STATE = os.path.expanduser("~/.hermes/state/loops")
KRLOG = os.path.expanduser("~/.hermes/state/keep-rate.jsonl")
TERMINAL = {"done", "done:no_change", "stopped:max_attempts", "stopped:check_failed"}


def paths(name):
    if (
        not name
        or name in {".", ".."}
        or os.path.isabs(name)
        or "/" in name
        or "\\" in name
        or ".." in name
    ):
        raise SystemExit(f"unsafe loop name: {name!r}")
    return os.path.join(LOOPS, name + ".yaml"), os.path.join(STATE, name + ".json")


def load(name):
    yf, sf = paths(name)
    if not os.path.isfile(yf):
        raise SystemExit(f"loop definition missing: {yf}")
    with open(yf, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    for key in ("goal", "criteria"):
        if key not in cfg:
            raise SystemExit(f"loop {name}: missing required key '{key}'")
    if not isinstance(cfg["criteria"], list) or not cfg["criteria"]:
        raise SystemExit(f"loop {name}: criteria must be a non-empty list")
    if cfg.get("checks") is not None and not isinstance(cfg["checks"], list):
        raise SystemExit(f"loop {name}: checks must be a list")
    if os.path.exists(sf):
        with open(sf, encoding="utf-8") as f:
            st = json.load(f)
    else:
        st = {"attempt": 0, "status": "pending", "gaps": [], "history": []}
    return cfg, st, sf


def checkpoint_path(sf):
    return sf.replace(".json", ".checkpoint.md")


def save(sf, st, note=None):
    os.makedirs(os.path.dirname(sf), exist_ok=True)
    tmp = sf + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=2)
    os.replace(tmp, sf)
    cp = checkpoint_path(sf)
    lines = [
        f"# Loop checkpoint: {os.path.basename(sf)[:-5]}",
        f"status: {st['status']}",
        f"attempt: {st['attempt']}",
        "gaps: " + ("; ".join(st.get("gaps", [])) or "none"),
    ]
    if note:
        lines.append(f"note: {note}")
    with open(cp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def krlog(name, kept, outcome):
    os.makedirs(os.path.dirname(KRLOG), exist_ok=True)
    with open(KRLOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": int(time.time()), "loop": name, "kept": kept, "outcome": outcome}) + "\n")


def run_checks(cfg):
    results = []
    for command in cfg.get("checks", []):
        proc = subprocess.run(command, shell=True, text=True, capture_output=True, timeout=300)
        results.append({
            "command": command,
            "exit_code": proc.returncode,
            "stdout": proc.stdout[-1000:],
            "stderr": proc.stderr[-1000:],
        })
    return results


def tick(name):
    cfg, st, sf = load(name)
    if st["status"] in TERMINAL:
        print(f"LOOP {name}: terminal state {st['status']}; use reset to run again")
        return
    limit = int(cfg.get("max_attempts", 3))
    if st["attempt"] >= limit:
        st["status"] = "stopped:max_attempts"
        save(sf, st, "hard attempt ceiling reached")
        krlog(name, False, st["status"])
        print(f"LOOP {name}: hit max_attempts={limit}, stopped and logged")
        return
    st["attempt"] += 1
    save(sf, st, "iteration started")
    criteria = "\n".join(f"- {c}" for c in cfg["criteria"])
    checks = "\n".join(f"- {c}" for c in cfg.get("checks", [])) or "(none declared)"
    gaps = "\n".join(f"- {g}" for g in st["gaps"]) or "(first pass)"
    print(f"""LOOP {name} — attempt {st['attempt']}/{limit}

GOAL: {cfg['goal']}

CRITERIA (hard gates):
{criteria}

DETERMINISTIC CHECKS (executed by `pass`; every command must exit 0):
{checks}

PREVIOUS GAPS:
{gaps}

EACH PASS:
1. DRAFT/IMPROVE the work.
2. SCORE each qualitative criterion harshly.
3. GAPS: list exactly what remains weak.
4. CALL:
   - all qualitative criteria clear and checks should pass: loop-runner.py pass {name}
   - nothing needed changing: loop-runner.py nochange {name}
   - otherwise: loop-runner.py fail {name} "gap 1; gap 2"

ANTI-BUSYWORK: NO_CHANGE is success. Never rewrite accurate work to look busy.
Checkpoint: {checkpoint_path(sf)}
""")


def record(name, action, gaps=""):
    cfg, st, sf = load(name)
    if st["status"] in TERMINAL:
        raise SystemExit(f"loop {name}: already terminal ({st['status']}); use reset first")
    if st["attempt"] < 1:
        raise SystemExit(f"loop {name}: call tick before {action}")
    event = {"attempt": st["attempt"], "action": action, "ts": int(time.time())}
    if action == "pass":
        checks = run_checks(cfg)
        event["checks"] = checks
        failed = [r for r in checks if r["exit_code"] != 0]
        if failed:
            st["status"] = "pending"
            st["gaps"] = [f"check failed ({r['exit_code']}): {r['command']}" for r in failed]
            event["passed"] = False
            st["history"].append(event)
            save(sf, st, "deterministic gate rejected pass")
            print(f"LOOP {name}: PASS REJECTED — {len(failed)} deterministic check(s) failed")
            for r in failed:
                print(f"  exit {r['exit_code']}: {r['command']}")
            return 1
        st["status"] = "done"
        st["gaps"] = []
        event["passed"] = True
        st["history"].append(event)
        save(sf, st, "all declared checks passed")
        krlog(name, True, "done")
        print(f"LOOP {name}: attempt {st['attempt']} PASSED, done")
        return 0
    if action == "nochange":
        st["status"] = "done:no_change"
        st["gaps"] = []
        event.update({"passed": True, "no_change": True})
        st["history"].append(event)
        save(sf, st, "nothing needed changing")
        krlog(name, True, "done:no_change")
        print(f"LOOP {name}: attempt {st['attempt']} NO_CHANGE (success)")
        return 0
    st["gaps"] = [g.strip() for g in gaps.split(";") if g.strip()] or ["unspecified gap"]
    st["status"] = "pending"
    event["passed"] = False
    st["history"].append(event)
    save(sf, st, "gaps recorded for next pass")
    print(f"LOOP {name}: attempt {st['attempt']} failed, gaps recorded")
    return 1


def status(name):
    cfg, st, sf = load(name)
    print(f"loop: {name}  status: {st['status']}  attempt: {st['attempt']}/{cfg.get('max_attempts', 3)}")
    print(f"checkpoint: {checkpoint_path(sf)}")
    for h in st["history"]:
        print("  ", h)
    if st["gaps"]:
        print("  open gaps:", "; ".join(st["gaps"]))


def reset(name):
    _, _, sf = load(name)
    st = {"attempt": 0, "status": "pending", "gaps": [], "history": []}
    save(sf, st, "explicit reset")
    print(f"LOOP {name}: reset")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("usage: loop-runner.py tick|pass|fail|nochange|status|reset <name> [gaps]")
    cmd, name = sys.argv[1], sys.argv[2]
    if cmd == "tick": tick(name)
    elif cmd == "pass": sys.exit(record(name, "pass"))
    elif cmd == "nochange": sys.exit(record(name, "nochange"))
    elif cmd == "fail": sys.exit(record(name, "fail", sys.argv[3] if len(sys.argv) > 3 else ""))
    elif cmd == "status": status(name)
    elif cmd == "reset": reset(name)
    else: raise SystemExit(f"unknown command: {cmd}")
