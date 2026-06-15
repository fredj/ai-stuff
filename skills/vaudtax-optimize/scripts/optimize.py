#!/usr/bin/env python3
"""Find and quantify tax-reduction levers in a .vaudtax declaration.

Delegates all tax math to the sibling `vaudtax` skill's scripts. Adds no tax
math of its own. Network: only the calls calculate_taxes.py makes to vd.ch.
"""
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
