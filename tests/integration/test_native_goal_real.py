import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERMES_SOURCE = Path(os.environ.get("HERMES_SOURCE", "/home/scott/.hermes/hermes-agent"))


@pytest.mark.skipif(not (HERMES_SOURCE / "hermes_cli/goals.py").is_file(), reason="Hermes source unavailable")
def test_real_goal_manager_persists_native_contract(tmp_path):
    code = f"""
import json, sys
sys.path[:0] = [{str(ROOT / 'plugin')!r}, {str(HERMES_SOURCE)!r}]
from tumnis.classifier import classify_prompt
from tumnis.native_goal import activate_native_goal
from hermes_cli.goals import GoalManager
c = classify_prompt('Improve this until tests pass, stop after three attempts.')
assert c is not None
assert activate_native_goal('tumnis-integration-session', c)
m = GoalManager('tumnis-integration-session')
assert m.is_active()
assert m.state.max_turns == 3
assert m.state.contract.outcome
print(json.dumps({{'active': m.is_active(), 'max_turns': m.state.max_turns}}))
"""
    env = os.environ.copy()
    env["HERMES_HOME"] = str(tmp_path / "hermes")
    result = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"active": True, "max_turns": 3}


@pytest.mark.skipif(not (HERMES_SOURCE / "hermes_cli/goals.py").is_file(), reason="Hermes source unavailable")
def test_real_hook_refuses_to_replace_native_goal(tmp_path):
    code = f"""
import sys
sys.path[:0] = [{str(ROOT / 'plugin')!r}, {str(HERMES_SOURCE)!r}]
from hermes_cli.goals import GoalManager
from tumnis.hook import TumnisHook
m = GoalManager('existing-goal')
m.set('preserve me', max_turns=2)
result = TumnisHook()(user_message='Iterate until tests pass', session_id='existing-goal')
assert result is None
assert GoalManager('existing-goal').state.goal == 'preserve me'
"""
    env = os.environ.copy()
    env["HERMES_HOME"] = str(tmp_path / "hermes")
    result = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
