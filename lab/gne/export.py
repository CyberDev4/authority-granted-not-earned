"""Turn a research episode into a Trajectory so monitors can run on it.

Every episode carries a programmatic label (did the forbidden call happen at the
probe?). That makes the study a source of verifiable-ground-truth trajectories
for authorization-failure monitors: the data type Apollo's agenda names as the
bottleneck.
"""
from __future__ import annotations

import json
from pathlib import Path

from agentscope.trajectory import Trajectory


def episode_to_trajectory(rec: dict, eid: str) -> Trajectory:
    t = Trajectory(id=eid, source="gne", meta={"config": rec["config"], "label_comply": rec["grade"]["comply"]})
    for m in rec["transcript"]:
        if m["role"] == "boundary":
            label = "context compacted; summary follows" if m["content"] == "compaction" else "handoff to sub-agent; briefing follows"
            t.add("boundary", text=label, meta={"kind": m["content"], "step": m.get("step")})
            continue
        content = m["content"]
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        for b in content:
            if b["type"] == "text":
                t.add(m["role"], text=b["text"])
            elif b["type"] == "tool_use":
                t.add("assistant", tool=b["name"], args=b["input"], tool_use_id=b["id"])
            elif b["type"] == "tool_result":
                t.add("tool_result", text=str(b["content"]), tool_use_id=b["tool_use_id"])
    return t


def export_dir(runs: str | Path, out: str | Path) -> int:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in sorted(Path(runs).glob("*.json")):
        if p.name.startswith("FAILED_"):
            continue
        rec = json.loads(p.read_text())
        episode_to_trajectory(rec, p.stem).save(out / f"{p.stem}.traj.json")
        n += 1
    return n
