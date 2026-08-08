"""Tumnis Loopworks Hermes plugin registration."""

from .tumnis.hook import get_default_hook


def register(ctx):
    """Register the single cache-safe prompt-classification hook."""
    ctx.register_hook("pre_llm_call", get_default_hook())
