#!/usr/bin/env python3
"""Rebuild dist zip packages from current sources (deterministic file lists)."""

from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MAIN_FILES = [
    "SKILL.md",
    "agents/openai.yaml",
    "assets/company-policy.yaml",
    "assets/cost-scenarios.csv",
    "assets/decision-memo.md",
    "assets/project-brief.md",
    "assets/risk-register.csv",
    "assets/spend-input.csv",
    "assets/supplier-evaluation.csv",
    "references/category-playbooks.md",
    "references/operating-model.md",
]
MAIN_FILES += [str(p.relative_to(ROOT)).replace("\\", "/") for p in sorted((ROOT / "references" / "categories").glob("*.md"))]
MAIN_FILES += [str(p.relative_to(ROOT)).replace("\\", "/") for p in sorted((ROOT / "references" / "workflows").glob("*.md"))]
MAIN_FILES.append("scripts/procurement_math.py")

SOURCING_FILES = [
    "skills/it-sourcing-map/SKILL.md",
    "skills/it-sourcing-map/agents/openai.yaml",
    "skills/it-sourcing-map/references/five-looks-and-map-schema.md",
    "skills/it-sourcing-map/scripts/render_supplier_map.py",
]


def build(zip_path: Path, prefix: str, files: list[str], strip_prefix: str = "") -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as bundle:
        for rel in files:
            source = ROOT / rel
            if not source.exists():
                raise SystemExit(f"missing source file: {rel}")
            arcname = rel[len(strip_prefix):] if strip_prefix and rel.startswith(strip_prefix) else f"{prefix}/{rel}"
            bundle.write(source, arcname)
    print(f"built {zip_path.relative_to(ROOT)} ({zip_path.stat().st_size} bytes)")


def main() -> None:
    build(ROOT / "dist" / "IT采购助理.zip", "it-procurement-assistant", MAIN_FILES)
    build(ROOT / "dist" / "it-sourcing-map.zip", "", SOURCING_FILES, strip_prefix="skills/")


if __name__ == "__main__":
    main()
