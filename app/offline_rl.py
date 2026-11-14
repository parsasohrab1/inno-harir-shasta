"""Offline-only fitted-Q iteration scaffold.

This module consumes a fixed, pre-collected transition dataset. It has no
simulator stepping, network, PLC/DCS, actuator, or live-control dependency.
Actions are abstract labels and must never be mapped to plant commands here.
"""
from __future__ import annotations

from math import isfinite
from typing import Any


def _state_key(state: list[float] | tuple[float, ...]) -> tuple[float, ...]:
    if not state:
        raise ValueError("state must not be empty")
    values = tuple(float(v) for v in state)
    if not all(isfinite(v) for v in values):
        raise ValueError("state contains a non-finite value")
    return tuple(round(v, 3) for v in values)


def fit_fitted_q_iteration(
    transitions: list[dict[str, Any]],
    action_ids: list[str],
    iterations: int = 20,
    gamma: float = 0.95,
) -> dict[str, Any]:
    """Fit a tiny tabular Q table from offline records only; never interacts with an environment."""
    if not transitions:
        raise ValueError("offline transition dataset is empty")
    if not action_ids or len(set(action_ids)) != len(action_ids):
        raise ValueError("action_ids must be non-empty and unique")
    if not 1 <= iterations <= 500:
        raise ValueError("iterations must be between 1 and 500")
    if not 0.0 <= gamma <= 1.0:
        raise ValueError("gamma must be between 0 and 1")

    rows = []
    for item in transitions:
        if item.get("source") not in {"simulator", "offline_dataset"}:
            raise ValueError("only simulator/offline_dataset records are accepted")
        state = _state_key(item["state"])
        next_state = _state_key(item["next_state"])
        action = str(item["action_id"])
        reward = float(item["reward"])
        if action not in action_ids or not isfinite(reward):
            raise ValueError("unknown action or invalid reward")
        rows.append((state, action, reward, next_state, bool(item.get("terminal", False))))

    q: dict[tuple[tuple[float, ...], str], float] = {}
    for _ in range(iterations):
        previous = dict(q)
        for state, action, reward, next_state, terminal in rows:
            future = 0.0 if terminal else max(
                (previous.get((next_state, candidate), 0.0) for candidate in action_ids),
                default=0.0,
            )
            q[(state, action)] = reward + gamma * future

    policy = {}
    states = sorted({row[0] for row in rows})
    for state in states:
        policy[str(state)] = max(
            action_ids,
            key=lambda action: q.get((state, action), float("-inf")),
        )
    return {
        "mode": "OFFLINE_DATASET_ONLY",
        "iterations": iterations,
        "gamma": gamma,
        "transition_count": len(rows),
        "q_values": {f"{state}|{action}": value for (state, action), value in q.items()},
        "policy_by_observed_state": policy,
        "execution": "NONE — abstract action labels only; no environment or equipment interaction.",
    }
