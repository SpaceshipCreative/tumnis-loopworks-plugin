import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugin"
if str(PLUGIN) not in sys.path:
    sys.path.insert(0, str(PLUGIN))

from tumnis.aux_classifier import classify_ambiguous
from tumnis.classifier import classify_prompt
from tumnis.graph_contract import render_graph_contract
from tumnis.hook import TumnisHook
from tumnis.models import Classification, Shape
from tumnis.native_goal import activate_native_goal


def test_plugin_entrypoint_loads_as_isolated_package():
    code = f"""
import importlib.util, sys
entry = {str(PLUGIN / '__init__.py')!r}
spec = importlib.util.spec_from_file_location('_tumnis_plugin_canary', entry, submodule_search_locations=[{str(PLUGIN)!r}])
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
class Context:
    def __init__(self): self.hooks = []
    def register_hook(self, name, callback): self.hooks.append((name, callback))
ctx = Context()
module.register(ctx)
assert len(ctx.hooks) == 1 and ctx.hooks[0][0] == 'pre_llm_call'
"""
    result = subprocess.run(
        [sys.executable, "-c", code], text=True, capture_output=True, cwd="/tmp"
    )
    assert result.returncode == 0, result.stderr


def test_manifest_declares_pre_llm_hook():
    text = (PLUGIN / "plugin.yaml").read_text()
    assert "name: tumnis-loopworks" in text
    assert "pre_llm_call" in text


@pytest.mark.parametrize(
    ("prompt", "shape"),
    [
        ("Summarize this paragraph in one sentence.", Shape.DIRECT),
        ("Improve this until the tests pass, stop after three attempts.", Shape.LOOP),
        ("Research n8n, Zapier, and Make in parallel, then compare them.", Shape.GRAPH),
        (
            "Research three options in parallel, verify each, and iterate until every claim is supported.",
            Shape.LOOP_GRAPH,
        ),
    ],
)
def test_obvious_prompt_shapes(prompt, shape):
    result = classify_prompt(prompt)
    assert result is not None
    assert result.shape is shape


@pytest.mark.parametrize(
    "prompt",
    [
        "/goal status",
        "[Continuing toward your standing goal]\nKeep working",
        "[ASYNC DELEGATION BATCH COMPLETE — abc]",
        "thanks",
        "",
    ],
)
def test_classifier_excludes_internal_and_trivial_prompts(prompt):
    assert classify_prompt(prompt) is None


def test_classification_rejects_executable_gates_and_caps_fields():
    value = Classification.from_dict(
        {
            "shape": "LOOP",
            "confidence": 2,
            "reason": "x" * 400,
            "goal": "g" * 9000,
            "max_turns": 999,
            "contract": {"outcome": "o" * 9000, "checks": ["rm -rf /"]},
        }
    )
    assert value.confidence == 1.0
    assert value.max_turns == 20
    assert len(value.goal) == 4000
    assert "checks" not in value.contract


def test_graph_contract_requires_native_subagent_batch_and_verifier():
    text = render_graph_contract(loop=False, durable=False)
    assert "delegate_task(tasks=[...])" in text
    assert "fresh-context verifier" in text
    assert "Retry only failed" in text


def test_durable_graph_contract_uses_kanban_goal_mode():
    text = render_graph_contract(loop=True, durable=True)
    assert "Kanban" in text
    assert "goal_mode=True" in text


class FakeManager:
    state_by_session = {}

    def __init__(self, session_id, default_max_turns=20):
        self.session_id = session_id
        self.state = self.state_by_session.get(session_id)

    def has_goal(self):
        return self.state is not None

    def set(self, goal, max_turns=None, contract=None):
        self.state = {"goal": goal, "max_turns": max_turns, "contract": contract}
        self.state_by_session[self.session_id] = self.state
        return self.state


class FakeContract:
    def __init__(self, **kwargs):
        self.values = kwargs


def test_aux_classifier_parses_strict_result_and_fails_direct():
    class Message:
        content = json.dumps(
            {
                "shape": "GRAPH",
                "confidence": 0.9,
                "reason": "independent_workstreams",
                "goal": "Compare three systems",
                "max_turns": 5,
                "contract": {"outcome": "Verified comparison"},
            }
        )

    class Choice:
        message = Message()

    class Response:
        choices = [Choice()]

    result = classify_ambiguous("Compare three systems", call_llm=lambda **_: Response())
    assert result.shape is Shape.GRAPH
    assert classify_ambiguous("ambiguous", call_llm=lambda **_: (_ for _ in ()).throw(RuntimeError())) is None


def test_native_goal_activation_never_replaces_existing_goal():
    FakeManager.state_by_session.clear()
    c = Classification.loop("finish the work", verification="tests pass", max_turns=4)
    assert activate_native_goal("s1", c, manager_cls=FakeManager, contract_cls=FakeContract)
    first = FakeManager.state_by_session["s1"]
    assert not activate_native_goal("s1", c, manager_cls=FakeManager, contract_cls=FakeContract)
    assert FakeManager.state_by_session["s1"] is first


def test_hook_direct_is_noop_and_loop_activates_goal():
    FakeManager.state_by_session.clear()
    hook = TumnisHook(manager_cls=FakeManager, contract_cls=FakeContract)
    assert hook(user_message="Summarize this.", session_id="d1") is None
    result = hook(
        user_message="Improve this until tests pass, stop after three attempts.",
        session_id="l1",
    )
    assert "TUMNIS SHAPE: LOOP" in result["context"]
    assert FakeManager.state_by_session["l1"]["max_turns"] == 3


def test_hook_skips_subagents_and_existing_goals():
    FakeManager.state_by_session.clear()
    hook = TumnisHook(manager_cls=FakeManager, contract_cls=FakeContract)
    assert hook(user_message="iterate until done", session_id="s", parent_session_id="parent") is None
    FakeManager.state_by_session["s"] = {"goal": "existing"}
    assert hook(user_message="iterate until done", session_id="s") is None
