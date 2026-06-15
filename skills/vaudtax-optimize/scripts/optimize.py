#!/usr/bin/env python3
"""Find and quantify tax-reduction levers in a .vaudtax declaration.

Delegates all tax math to the sibling `vaudtax` skill's scripts. Adds no tax
math of its own. Network: only the calls calculate_taxes.py makes to vd.ch.
"""
import json
import subprocess
from pathlib import Path


def resolve_vaudtax_scripts(start: "Path | None" = None) -> Path:
    """Locate the vaudtax skill's scripts/ directory.

    Sibling path first (both skills installed under skills/), then a filesystem
    search. Raises FileNotFoundError naming the missing dependency.
    """
    explicit = start is not None
    start = (start or Path(__file__).resolve().parent)
    sibling = start.parent.parent / "vaudtax" / "scripts"
    if (sibling / "compute_code800.py").exists():
        return sibling
    bases = {start} if explicit else {start, Path.home()}
    for base in bases:
        for hit in base.glob("**/vaudtax/scripts/compute_code800.py"):
            return hit.parent
    raise FileNotFoundError(
        "Requires the vaudtax skill to be installed: could not find "
        "compute_code800.py / calculate_taxes.py next to vaudtax-optimize.")


def parse_chf(s: str) -> float:
    """Parse a Swiss-formatted amount ("23'450.65") to float."""
    return float(str(s).replace("'", "").strip())


def run_compute_code800(vaudtax_file: Path, scripts: Path) -> dict:
    proc = subprocess.run(
        ["python", str(scripts / "compute_code800.py"), str(vaudtax_file), "--json"],
        capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def run_calculate_taxes(a: dict, scripts: Path, marginal: bool = False) -> dict:
    cmd = ["python", str(scripts / "calculate_taxes.py"),
           "--periode", str(a["periode"]), "--commune", a["commune"],
           "--etat-civil", a.get("etat_civil", "single"),
           "--revenu-icc", str(a["revenu_icc"]),
           "--fortune-icc", str(a["fortune_icc"]),
           "--revenu-ifd", str(a["revenu_ifd"]), "--json"]
    for flag, key in (("--enfants", "enfants"), ("--enfants-demi", "enfants_demi"),
                      ("--enfants-menage", "enfants_menage")):
        if a.get(key):
            cmd += [flag, str(a[key])]
    if marginal:
        cmd.append("--marginal-rate")
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(proc.stdout)
    if marginal:
        return {"marginal_total": data["marginal_total"]}
    return {"total": parse_chf(data["total_icc_ifd"]),
            "total_icc": parse_chf(data["total_icc"]),
            "total_ifd": parse_chf(data["total_ifd"])}
