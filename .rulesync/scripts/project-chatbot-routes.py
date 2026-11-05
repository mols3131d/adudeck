#!/usr/bin/env python3
"""Project and validate .agents/route metadata from canonical Rulesync assets."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
EXTERNAL_SOURCE_KEY = "mols3131d/mols-agent-assets"
EXTERNAL_SKILL_PATH = "src/rulesync/.rulesync/skills"


def extract_scalar(front: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}:[ \t]*(.+?)[ \t]*$", front)
    if not match:
        raise SystemExit(f"missing frontmatter key '{key}'")
    value = match.group(1).strip()
    if value in {">", ">-", "|", "|-"}:
        block = re.search(
            rf"(?m)^{re.escape(key)}:[ \t]*[>|]-?[ \t]*\n((?:[ \t]+[^\n]*(?:\n|$))+)",
            front,
        )
        if not block:
            raise SystemExit(f"empty multiline frontmatter key '{key}'")
        return " ".join(line.strip() for line in block.group(1).splitlines()).strip()
    return value.strip("'\"")


def parse_skill_frontmatter(path: Path) -> tuple[str, str]:
    if not path.is_file():
        raise SystemExit(f"skill file not found: {path}")
    match = FRONT_MATTER_RE.match(path.read_text(encoding="utf-8"))
    if not match:
        raise SystemExit(f"missing YAML frontmatter in {path}")
    front = match.group(1)
    return extract_scalar(front, "name"), extract_scalar(front, "description")


def load_jsonl(path: Path, expected_kind: str) -> tuple[dict[str, object], list[dict[str, object]]]:
    if not path.is_file():
        raise SystemExit(f"route file not found: {path}")
    rows: list[dict[str, object]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"invalid JSONL at {path}:{line_no}: {exc.msg}") from exc
        if not isinstance(row, dict):
            raise SystemExit(f"route row must be an object at {path}:{line_no}")
        rows.append(row)

    if not rows:
        raise SystemExit(f"empty route file: {path}")
    meta = rows[0].get("_meta")
    if (
        not isinstance(meta, dict)
        or meta.get("kind") != expected_kind
        or not isinstance(meta.get("instructions"), str)
        or not str(meta["instructions"]).strip()
    ):
        raise SystemExit(f"invalid _meta header for {expected_kind}: {path}")
    return meta, rows[1:]


def validate_static_route_files(route_dir: Path) -> None:
    route_md = route_dir / "ROUTE.md"
    if not route_md.is_file():
        raise SystemExit(f"missing route entrypoint: {route_md}")
    route_text = route_md.read_text(encoding="utf-8")
    for target in ("skills.jsonl", "rules.jsonl"):
        if target not in route_text:
            raise SystemExit(f"{route_md} must reference {target}")

    _, rule_entries = load_jsonl(route_dir / "rules.jsonl", "rules")
    if rule_entries:
        raise SystemExit("rules.jsonl must stay delegated to CHATBOT.md without duplicate rule entries")


def main() -> None:
    if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1] not in ("write", "--check")):
        print(f"usage: {sys.argv[0]} [--check]", file=sys.stderr)
        raise SystemExit(2)
    check_only = len(sys.argv) == 2 and sys.argv[1] == "--check"

    repo = Path.cwd()
    route_dir = repo / ".agents" / "route"
    skills_jsonl = route_dir / "skills.jsonl"

    validate_static_route_files(route_dir)
    meta, actual_entries = load_jsonl(skills_jsonl, "skills")

    existing_descriptions: dict[str, str] = {}
    seen_names: set[str] = set()
    seen_sources: set[str] = set()
    for entry in actual_entries:
        name = entry.get("name")
        desc = entry.get("description")
        source = entry.get("source")
        if (
            not isinstance(name, str)
            or not name.strip()
            or not isinstance(desc, str)
            or not desc.strip()
            or not isinstance(source, str)
            or not source.strip()
        ):
            raise SystemExit(f"invalid skill route entry in {skills_jsonl}: {entry}")
        if name in seen_names:
            raise SystemExit(f"duplicate skill name in {skills_jsonl}: {name}")
        if source in seen_sources:
            raise SystemExit(f"duplicate skill source in {skills_jsonl}: {source}")
        seen_names.add(name)
        seen_sources.add(source)
        existing_descriptions[name] = desc

    expected_entries: list[dict[str, str]] = []

    for skill_md in sorted((repo / ".rulesync" / "skills").glob("*/SKILL.md")):
        name, canonical_desc = parse_skill_frontmatter(skill_md)
        rel_source = skill_md.relative_to(repo).as_posix()
        expected_entries.append(
            {
                "name": name,
                "description": existing_descriptions.get(name, canonical_desc),
                "source": rel_source,
            }
        )

    lock_data = json.loads((repo / "rulesync.lock").read_text(encoding="utf-8"))
    ext_source = lock_data["sources"][EXTERNAL_SOURCE_KEY]
    resolved_ref = ext_source["resolvedRef"]
    for name in sorted(ext_source["skills"]):
        desc = existing_descriptions.get(name)
        if not desc:
            curated_md = repo / ".rulesync" / "skills" / ".curated" / name / "SKILL.md"
            _, desc = parse_skill_frontmatter(curated_md)
        url = (
            f"https://raw.githubusercontent.com/{EXTERNAL_SOURCE_KEY}/"
            f"{resolved_ref}/{EXTERNAL_SKILL_PATH}/{name}/SKILL.md"
        )
        expected_entries.append({"name": name, "description": desc, "source": url})

    if check_only:
        actual_pairs = [(str(e["name"]), str(e["source"])) for e in actual_entries]
        expected_pairs = [(e["name"], e["source"]) for e in expected_entries]
        if actual_pairs != expected_pairs:
            raise SystemExit(
                f"skill route drift in {skills_jsonl}: expected {len(expected_pairs)} synced entries"
            )
        return

    lines = [json.dumps({"_meta": meta}, ensure_ascii=False, separators=(",", ":"))]
    lines.extend(
        json.dumps(entry, ensure_ascii=False, separators=(",", ":")) for entry in expected_entries
    )
    rendered = "\n".join(lines) + "\n"
    if skills_jsonl.read_text(encoding="utf-8") != rendered:
        skills_jsonl.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
