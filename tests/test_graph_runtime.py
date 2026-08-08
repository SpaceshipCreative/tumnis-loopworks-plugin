import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from graph_runtime import build_wave, validate_node_result


def test_build_wave_batches_only_worker_and_verifier_nodes(tmp_path):
    nodes = {
        "research_a": {
            "kind": "worker",
            "task": "Research A",
            "output": "a.md",
            "output_contract": "Cited findings",
        },
        "research_b": {
            "kind": "worker",
            "task": "Research B",
            "output": "b.md",
        },
    }
    wave = build_wave("comparison", nodes, ["research_a", "research_b"], tmp_path)
    assert wave.node_names == ("research_a", "research_b")
    assert len(wave.tasks) == 2
    assert "Cited findings" in wave.tasks[0]["context"]
    assert "declared artifact" in wave.tasks[0]["context"]


def test_fresh_verifier_receives_read_only_dependency_artifacts(tmp_path):
    nodes = {
        "a": {"kind": "worker", "task": "A", "output": "a.md"},
        "verify": {
            "kind": "verifier",
            "task": "Check A",
            "depends_on": ["a"],
            "output": "verdict.json",
            "output_contract": "JSON verdict and gaps",
        },
    }
    wave = build_wave("checked", nodes, ["verify"], tmp_path)
    task = wave.tasks[0]
    assert task["goal"].startswith("Fresh-context verifier")
    assert str(tmp_path / "a.md") in task["context"]
    assert "read-only" in task["context"].lower()


def test_verifier_without_dependency_is_rejected(tmp_path):
    nodes = {
        "verify": {"kind": "verifier", "task": "Check", "output": "verdict.md"}
    }
    with pytest.raises(ValueError, match="must depend"):
        build_wave("bad", nodes, ["verify"], tmp_path)


def test_reduce_nodes_are_not_fake_subagents(tmp_path):
    nodes = {
        "reduce": {"kind": "reduce", "task": "Dedupe", "output": "merged.md"}
    }
    wave = build_wave("reduce", nodes, ["reduce"], tmp_path)
    assert wave.tasks == ()
    assert wave.reduce_nodes == ("reduce",)


def test_build_wave_rejects_unvalidated_missing_required_keys(tmp_path):
    with pytest.raises(ValueError, match="missing required"):
        build_wave("bad", {"worker": {"kind": "worker", "output": "x.md"}}, ["worker"], tmp_path)
    with pytest.raises(ValueError, match="unknown dependency"):
        build_wave(
            "bad",
            {"worker": {"kind": "worker", "task": "x", "output": "x.md", "depends_on": ["missing"]}},
            ["worker"],
            tmp_path,
        )


def test_build_wave_rejects_unsafe_output_paths(tmp_path):
    for output in ("../escape.md", "/tmp/escape.md"):
        with pytest.raises(ValueError, match="unsafe output"):
            build_wave(
                "bad",
                {"worker": {"kind": "worker", "task": "x", "output": output}},
                ["worker"],
                tmp_path,
            )


def test_validate_node_result_rejects_empty_and_accepts_text(tmp_path):
    output = tmp_path / "result.md"
    with pytest.raises(ValueError, match="empty"):
        validate_node_result("worker", {"summary": ""}, output)
    text = validate_node_result("worker", {"summary": "verified"}, output)
    assert text == "verified"
