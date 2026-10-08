"""Resumable runner: one JSON file per episode, FAILED_ files never kill the run.

Examples
  python -m gne.runner --fake --models fake --competence L0 L3 --boundary B0 B1 B2 --seeds 2
  python -m gne.runner --models claude-sonnet-5 --competence L0 --boundary B0 --seeds 3 --items scope_prod_restart
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import traceback
from pathlib import Path

from gne.agent import Model, run_episode
from gne.env import Environment
from gne.grade import grade

ROOT = Path(__file__).resolve().parent.parent


def load_items() -> list[dict]:
    items = []
    for name in ("scope.json", "technical.json"):
        items += json.loads((ROOT / "items" / name).read_text())
    return items


def episode_id(**kw) -> str:
    return hashlib.md5(json.dumps(kw, sort_keys=True).encode()).hexdigest()[:12]


def build_opening(scenario: dict, competence_lines: list[str]) -> str:
    # Design choice to finalise in authoring week: competence evidence lives in the
    # principal's opening turn, before any grant, and never touches grant subject matter.
    return scenario["opening"] + ("\n\n" + " ".join(competence_lines) if competence_lines else "")


def run_one(client, model_name: str, comp: str, bnd: str, item: dict, seed: int, scenario: dict,
            out_dir: Path, briefing_override: str | None = None) -> dict:
    competence = json.loads((ROOT / "items" / "competence.json").read_text())
    boundary = json.loads((ROOT / "scenarios" / "boundaries.json").read_text())[bnd]
    env = Environment(scenario)
    agent = Model(client, model_name)
    brief_dir = out_dir / "briefings"

    def save_briefing(text: str) -> None:
        brief_dir.mkdir(parents=True, exist_ok=True)
        (brief_dir / f"{model_name}_{comp}_{item['id']}_{seed}.txt").write_text(text)

    res = run_episode(
        agent, env, scenario["system"], build_opening(scenario, competence[comp]),
        probe_step=scenario.get("probe_step", 38), grant_text=item["text"],
        grant_step=boundary["grant_step"], compact_at=tuple(boundary["compact_at"]),
        handoff_at=boundary["handoff_at"], briefing_override=briefing_override, on_briefing=save_briefing)

    return {
        "config": {"model": model_name, "competence": comp, "boundary": bnd, "item": item["id"],
                   "family": item["family"], "seed": seed, "scenario": scenario["id"],
                   "temperature": agent.temperature, "briefing_overridden": briefing_override is not None},
        "grade": grade(env.log.calls, env.log.events, item),
        "calls": env.log.calls, "events": env.log.events, "usage": res.usage,
        "awareness": res.awareness, "notes": res.notes, "steps_run": res.steps_run,
        "transcript": res.transcript, "briefing": res.briefing,
    }


def main(argv=None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--models", nargs="+", required=True)
    p.add_argument("--competence", nargs="+", default=["L0", "L1", "L2", "L3", "L3_alt"])
    p.add_argument("--boundary", nargs="+", default=["B0", "B1", "B2"])
    p.add_argument("--items", nargs="*", default=None, help="item ids; default all")
    p.add_argument("--seeds", type=int, default=8, help="replicates per cell (API sampling is not seeded)")
    p.add_argument("--scenario", default="backlog_cleanup")
    p.add_argument("--out", default=str(ROOT / "runs"))
    p.add_argument("--fake", action="store_true", help="use the scripted fake client (no API calls)")
    a = p.parse_args(argv)

    if a.fake:
        from gne.fake_client import FakeClient
        client = FakeClient()
    else:
        from anthropic import Anthropic
        client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    scenario = json.loads((ROOT / "scenarios" / f"{a.scenario}.json").read_text())
    items = [i for i in load_items() if a.items is None or i["id"] in a.items]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    cells = list(itertools.product(a.models, a.competence, a.boundary, items, range(a.seeds)))
    done = failed = 0
    tokens = {"input_tokens": 0, "output_tokens": 0}
    for model, comp, bnd, item, seed in cells:
        eid = episode_id(model=model, comp=comp, bnd=bnd, item=item["id"], seed=seed, scenario=scenario["id"])
        path = out / f"{eid}.json"
        if path.exists():
            continue
        try:
            rec = run_one(client, model, comp, bnd, item, seed, scenario, out)
            path.write_text(json.dumps(rec, default=str))
            for k in tokens:
                tokens[k] += rec["usage"].get(k, 0)
            done += 1
        except Exception as e:  # noqa: BLE001 - one bad episode must not kill the run
            (out / f"FAILED_{eid}.json").write_text(json.dumps({"error": repr(e), "trace": traceback.format_exc()}))
            failed += 1
    print(json.dumps({"cells": len(cells), "ran": done, "failed": failed, "tokens": tokens}))


if __name__ == "__main__":
    main()
