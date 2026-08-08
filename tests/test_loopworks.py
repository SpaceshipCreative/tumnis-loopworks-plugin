#!/usr/bin/env python3
import json
import os
from pathlib import Path
import py_compile
import shutil
import subprocess
import tempfile
import textwrap

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
HOME = Path(tempfile.mkdtemp(prefix="tumnis-loopworks-test-"))
ENV = os.environ | {"HOME": str(HOME)}
LOOPS = HOME / ".hermes/loops"
GRAPHS = HOME / ".hermes/graphs"
LOOPS.mkdir(parents=True)
GRAPHS.mkdir(parents=True)


def run(args, expected=0):
    result = subprocess.run([str(a) for a in args], env=ENV, text=True, capture_output=True)
    assert result.returncode == expected, (args, result.returncode, result.stdout, result.stderr)
    return result


def run_with_env(args, env, expected=0):
    result = subprocess.run([str(a) for a in args], env=env, text=True, capture_output=True)
    assert result.returncode == expected, (args, result.returncode, result.stdout, result.stderr)
    return result


def main():
    try:
        for script in SCRIPTS.glob("*.py"):
            py_compile.compile(str(script), doraise=True)

        installer = ROOT / "install.sh"
        install_home = HOME / "default-install"
        install_hermes = install_home / ".hermes"
        install_hermes.mkdir(parents=True)
        soul = install_hermes / "SOUL.md"
        soul.write_text("# Existing Identity\n\nKeep this section.\n")
        install_env = os.environ | {
            "HOME": str(install_home),
            "HERMES_HOME": str(install_hermes),
        }
        run_with_env([installer, "--with-preflight"], install_env)
        assert soul.read_text().count("# Loop/Graph Preflight") == 1
        assert "Never require the user to name the skill" in soul.read_text()
        assert list(install_hermes.glob("SOUL.md.backup-loopworks-*"))
        assert (install_hermes / "plugins/tumnis-loopworks/plugin.yaml").is_file()
        assert (install_hermes / "plugins/tumnis-loopworks/tumnis/hook.py").is_file()
        assert (install_home / "bin/graph_runtime.py").is_file()
        run_with_env([installer, "--with-preflight"], install_env)
        assert soul.read_text().count("# Loop/Graph Preflight") == 1

        opt_out_home = HOME / "opt-out-install"
        opt_out_hermes = opt_out_home / ".hermes"
        opt_out_env = os.environ | {
            "HOME": str(opt_out_home),
            "HERMES_HOME": str(opt_out_hermes),
        }
        run_with_env([installer], opt_out_env)
        assert not (opt_out_hermes / "SOUL.md").exists()
        assert (opt_out_hermes / "plugins/tumnis-loopworks/plugin.yaml").is_file()
        assert (opt_out_hermes / "skills/autonomous-ai-agents/loop-graph-system/SKILL.md").is_file()

        manual_home = HOME / "manual-install"
        manual_hermes = manual_home / ".hermes"
        manual_env = os.environ | {"HOME": str(manual_home), "HERMES_HOME": str(manual_hermes)}
        run_with_env([installer, "--manual-only"], manual_env)
        assert not (manual_hermes / "plugins/tumnis-loopworks").exists()
        assert not (manual_hermes / "SOUL.md").exists()
        assert (manual_home / "bin/loop-runner.py").is_file()

        uninstall_home = HOME / "uninstall-test"
        uninstall_hermes = uninstall_home / ".hermes"
        uninstall_env = os.environ | {"HOME": str(uninstall_home), "HERMES_HOME": str(uninstall_hermes)}
        run_with_env([installer, "--with-preflight"], uninstall_env)
        preserved_state = uninstall_hermes / "state/loops/preserve.json"
        preserved_state.write_text("{}")
        run_with_env([ROOT / "uninstall.sh", "--remove-preflight"], uninstall_env)
        assert not (uninstall_hermes / "plugins/tumnis-loopworks").exists()
        assert not (uninstall_home / "bin/loop-runner.py").exists()
        assert preserved_state.is_file()
        assert "# Loop/Graph Preflight" not in (uninstall_hermes / "SOUL.md").read_text()

        artifact = HOME / "artifact.txt"
        (LOOPS / "gate.yaml").write_text(textwrap.dedent(f"""
            name: gate
            goal: make artifact
            criteria: [artifact exists]
            checks: ["test -s {artifact}"]
            max_attempts: 2
        """))
        loop = SCRIPTS / "loop-runner.py"
        keep = SCRIPTS / "keep-rate.py"
        graph = SCRIPTS / "graph-runner.py"

        assert "unsafe loop name" in run([loop, "status", "../outside"], 1).stderr

        run([loop, "tick", "gate"])
        assert "PASS REJECTED" in run([loop, "pass", "gate"], 1).stdout
        artifact.write_text("ok\n")
        run([loop, "pass", "gate"])
        state_path = HOME / ".hermes/state/loops/gate.json"
        state = json.loads(state_path.read_text())
        assert state["status"] == "done"
        assert "terminal state done" in run([loop, "tick", "gate"]).stdout
        assert (HOME / ".hermes/state/loops/gate.checkpoint.md").is_file()

        run([loop, "reset", "gate"])
        run([loop, "tick", "gate"])
        run([loop, "nochange", "gate"])
        assert "done:no_change" in run([loop, "tick", "gate"]).stdout

        log = HOME / ".hermes/state/keep-rate.jsonl"
        with log.open("a") as handle:
            handle.write("not-json\n")
            handle.write(json.dumps({"loop": "bad-loop", "kept": False}) + "\n")
        assert json.loads(run([keep, "--json"]).stdout)["malformed_lines"] == 1
        run([keep, "--strict"], 2)

        workflow = GRAPHS / "valid.yaml"
        workflow.write_text(textwrap.dedent("""
            workflow: valid
            nodes:
              a:
                task: produce A
                output: a.md
                checks: ["test -s {output}"]
              b:
                task: consume A
                depends_on: [a]
                output: b.md
        """))
        assert "2 nodes, 2 waves" in run([graph, "plan", workflow]).stdout
        emitted = run([graph, "run", workflow]).stdout
        manifest = json.loads(emitted)
        assert manifest["contract"] == "tumnis.graph/v1"
        assert len(manifest["waves"]) == 2
        assert manifest["waves"][0]["delegated_nodes"] == ["a"]
        assert "delegate_task(tasks=[...])" in manifest["execution"]["reasoning_nodes"]
        assert manifest["waves"][0]["check_commands"]["a"] == [
            f'test -s {manifest["waves"][0]["outputs"]["a"]}'
        ]
        assert "hermes_tools" not in emitted and "delegation(" not in emitted

        invalid = GRAPHS / "invalid.yaml"
        invalid.write_text(textwrap.dedent("""
            workflow: invalid
            nodes:
              a:
                task: bad dependency
                depends_on: [missing]
                output: a.md
        """))
        assert "unknown dependencies" in run([graph, "plan", invalid], 1).stderr
        print("PASS: all Tumnis Loopworks regression gates")
    finally:
        shutil.rmtree(HOME)


if __name__ == "__main__":
    main()
