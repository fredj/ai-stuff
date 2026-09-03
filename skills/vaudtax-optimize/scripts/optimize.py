#!/usr/bin/env python3
"""Find and quantify tax-reduction levers in a .vaudtax declaration.

Delegates all tax math to the sibling `vaudtax` skill's scripts. Adds no tax
math of its own. Network: only the calls calculate_taxes.py makes to vd.ch.
"""
import argparse
import datetime
import json
import subprocess
import sys
import tempfile
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


def run_export_json(vaudtax_file: Path, scripts: Path) -> dict:
    """Run export_json.py (writes to a file, no stdout mode) via a temp file."""
    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / "export.json"
        subprocess.run(
            ["python", str(scripts / "export_json.py"), str(vaudtax_file), str(out_path)],
            capture_output=True, text=True, check=True)
        return json.loads(out_path.read_text())


# Caps sourced from vaudtax/references/deductions.md (2025). Year-specific:
# add a CAPS_<year> table and select on `periode` before reusing for other years.
CAPS_2025 = {
    "pilier3a_lpp": 7258,   # assured under LPP (code 310)
}

# Below this, a gap-to-cap is rounding noise, not an actionable lever. A real
# declaration showed pilier3a=7250 vs cap 7258 (CHF 8) — do not surface that.
MIN_GAP = 100


def detect_auto_levers(breakdown: dict, caps: dict, periode: int, current_year: int) -> tuple:
    """Mechanical levers from the compute_code800 breakdown.

    Mechanism 1 (gap-to-cap): pillar 3a headroom. The 3a contribution is
    deductible identically on ICC and IFD. Other forfaits (transport, meals,
    autres frais) are auto-maximised by compute_code800, so they carry no
    headroom and are intentionally not surfaced here.

    A gap on a still-open declaration year is a same-year top-up: a real
    scenario, computed against this year's baseline. A gap on an already
    closed year cannot be topped up any more — it can only be recovered via
    a "rachat de lacune 3a" claimed on a LATER year's declaration, at that
    year's own income and rate (see deductions.md CODE 310). optimize.py has
    no later year's baseline to compute against here, so that case is
    surfaced as a signal, not a scenario — never invent a saving for it.

    Returns (levers, signals).
    """
    levers, signals = [], []
    gap_3a = caps["pilier3a_lpp"] - breakdown.get("pilier3a", 0)
    if gap_3a >= MIN_GAP:
        if not isinstance(periode, int) or periode >= current_year:
            levers.append({
                "name": "pilier3a", "type": "forward",
                "label": "Pilier 3a — combler le plafond",
                "icc": gap_3a, "ifd": gap_3a, "cost": gap_3a,
            })
        else:
            signals.append({
                "code": "310", "label": "Lacune 3a — rachat possible",
                "note": f"CHF {_chf(gap_3a)} unused 3a headroom in {periode} "
                        "(declaration year is closed). Not a same-year top-up "
                        "any more — check with the 3a provider whether they "
                        "offer the rachat-de-lacune catch-up (from 2026, "
                        "10-year window, ordinary contribution of the buy-back "
                        "year must be paid in full first), then quote the "
                        "saving on that later year's own declaration.",
            })
    return levers, signals


def detect_insurance_gap_signal(breakdown: dict) -> list:
    """CODE 300: gap-to-cap on insurance premiums, computed the same way as
    the pilier 3a gap — but unlike 3a there is no "top up" action; the
    taxpayer must already hold an undeclared, deductible premium (accident,
    life, health for a dependent, ...). Always a question, never a lever.
    """
    signals = []
    cap = breakdown.get("assurances_icc_cap")
    declared = breakdown.get("assurances_icc", 0)
    if cap is not None:
        gap = cap - declared
        if gap >= MIN_GAP:
            signals.append({
                "code": "300", "label": "Assurances — plafond non atteint",
                "note": f"CHF {_chf(gap)} of headroom below the ICC cap "
                        f"(CHF {_chf(cap)}) — any other deductible insurance "
                        "premium (accident, life, health for a dependent) "
                        "not yet declared?",
            })
    return signals


def detect_candidate_signals(data: dict) -> list:
    """Mechanism 3 aid: structured evidence for entitlement levers `optimize.py`
    cannot compute a CHF amount for. These are questions, not findings — never
    passed as `--lever` automatically. See references/levers.md.
    """
    signals = []

    ctb1_income = any(e.get("taxpayer") == "CTB1" for e in data.get("income", []))
    ctb2_income = any(e.get("taxpayer") == "CTB2" for e in data.get("income", []))
    if data.get("taxpayer2") and ctb1_income and ctb2_income:
        signals.append({
            "code": "235", "label": "Double activité des conjoints",
            "note": "Both spouses have lucrative income — check eligibility "
                    "(see deductions.md CODE 235) and pass --lever if it applies.",
        })

    if data.get("education_costs"):
        signals.append({
            "code": "618", "label": "Frais de formation",
            "note": "Training costs declared — confirm they aren't formation "
                    "initiale and are within the CHF 12'000/13'000 cap.",
        })

    dettes = data.get("debt_interest") or {}
    has_debt_interest = dettes.get("ctb1_amount_chf") or dettes.get("ctb2_amount_chf")
    if data.get("real_estate") and not has_debt_interest:
        signals.append({
            "code": "610", "label": "Intérêts passifs / dettes privées",
            "note": "Real estate declared but no debt interest — check for an "
                    "unclaimed mortgage interest deduction.",
        })

    return signals


def parse_lever_spec(specs: list) -> list:
    """Parse `name:icc=N,ifd=N[,cost=N][,type=...]` strings into lever dicts."""
    levers = []
    for spec in specs:
        if ":" not in spec:
            raise ValueError(f"Malformed lever (need name:...): {spec!r}")
        name, _, rest = spec.partition(":")
        kv = {}
        for pair in rest.split(","):
            k, _, v = pair.partition("=")
            kv[k.strip()] = v.strip()
        if "icc" not in kv or "ifd" not in kv:
            raise ValueError(f"Lever {name!r} needs icc= and ifd=")
        typ = kv.get("type", "forward")
        icc, ifd = int(kv["icc"]), int(kv["ifd"])
        default_cost = icc if typ == "forward" else 0
        levers.append({
            "name": name.strip(), "type": typ, "label": name.strip(),
            "icc": icc, "ifd": ifd, "cost": int(kv.get("cost", default_cost)),
        })
    return levers


def _apply(args: dict, icc: int, ifd: int) -> dict:
    a = dict(args)
    a["revenu_icc"] = max(0, args["revenu_icc"] - icc)
    a["revenu_ifd"] = max(0, args["revenu_ifd"] - ifd)
    return a


def run_scenarios(base_args: dict, levers: list, scripts: Path) -> dict:
    baseline = run_calculate_taxes(base_args, scripts)
    scenarios = []
    for lev in levers:
        r = run_calculate_taxes(_apply(base_args, lev["icc"], lev["ifd"]), scripts)
        scenarios.append({**lev, "total": r["total"],
                          "saved": round(baseline["total"] - r["total"], 2)})
    combined = None
    if levers:
        icc = sum(l["icc"] for l in levers)
        ifd = sum(l["ifd"] for l in levers)
        c = run_calculate_taxes(_apply(base_args, icc, ifd), scripts)
        combined = {"total": c["total"],
                    "saved": round(baseline["total"] - c["total"], 2),
                    "cost": sum(l["cost"] for l in levers)}
    return {"baseline": baseline, "scenarios": scenarios, "combined": combined}


def _chf(n) -> str:
    return f"{round(n):,}".replace(",", "'")


def format_report(results: dict, periode: str, signals: "list | None" = None) -> str:
    signals = signals or []
    base = results["baseline"]["total"]
    recoverable = [s for s in results["scenarios"] if s["type"] == "recoverable"]
    forward = [s for s in results["scenarios"] if s["type"] == "forward"]
    lines = [f"Tax optimization — {periode}",
             f"Baseline total tax: CHF {_chf(base)}", ""]
    if recoverable:
        lines.append("Recoverable now (amend / refile — no new spending)")
        for s in recoverable:
            lines.append(f"  {s['label']:<30} saved CHF {_chf(s['saved'])}")
        lines.append("")
    if forward:
        lines.append("Forward-looking (requires committing cash)")
        for s in forward:
            net = s["saved"] - s["cost"]
            lines.append(f"  {s['label']:<30} cost CHF {_chf(s['cost'])}  "
                         f"saved CHF {_chf(s['saved'])}  net CHF {_chf(net)}")
        lines.append("")
    if results.get("combined"):
        c = results["combined"]
        lines.append(f"Combined realistic scenario: saved CHF {_chf(c['saved'])} "
                     f"(cash cost CHF {_chf(c['cost'])})")
        lines.append("")
    if signals:
        lines.append("Signals found — confirm eligibility (not findings)")
        for sig in signals:
            lines.append(f"  CODE {sig['code']} — {sig['label']}: {sig['note']}")
    return "\n".join(lines)


def run_calculate_taxes(a: dict, scripts: Path) -> dict:
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
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(proc.stdout)
    return {"total": parse_chf(data["total_icc_ifd"]),
            "total_icc": parse_chf(data["total_icc"]),
            "total_ifd": parse_chf(data["total_ifd"])}


def run_main(argv) -> tuple:
    """Parse args, run analysis, return (exit_code, report_text). Testable core."""
    ap = argparse.ArgumentParser(
        description="Find and quantify tax-reduction levers in a .vaudtax file.")
    ap.add_argument("file", help="Path to the .vaudtax file")
    ap.add_argument("--commune", default=None,
                    help="Override; defaults to the commune compute_code800 emits")
    ap.add_argument("--etat-civil", default="single",
                    choices=["single", "married", "parent"])
    ap.add_argument("--enfants", type=int, default=0)
    ap.add_argument("--enfants-demi", type=int, default=0)
    ap.add_argument("--enfants-menage", type=int, default=0)
    ap.add_argument("--lever", action="append", default=[],
                    help="Explicit lever name:icc=N,ifd=N[,cost=N][,type=...]")
    args = ap.parse_args(argv)

    scripts = resolve_vaudtax_scripts()
    compute = run_compute_code800(Path(args.file), scripts)
    periode = compute.get("periode", "?")
    commune = args.commune or compute.get("commune")
    if not commune:
        ap.error("No commune in the declaration; pass --commune explicitly.")
    base_args = {
        "periode": int(periode) if str(periode).isdigit() else periode,
        "commune": commune, "etat_civil": args.etat_civil,
        "enfants": args.enfants, "enfants_demi": args.enfants_demi,
        "enfants_menage": args.enfants_menage,
        "revenu_icc": compute["revenu_icc"], "fortune_icc": compute["fortune_icc"],
        "revenu_ifd": compute["revenu_ifd"],
    }
    current_year = datetime.date.today().year
    auto_levers, lacune_signals = detect_auto_levers(
        compute["breakdown"], CAPS_2025, base_args["periode"], current_year)
    levers = auto_levers + parse_lever_spec(args.lever)
    results = run_scenarios(base_args, levers, scripts)
    exported = run_export_json(Path(args.file), scripts)
    signals = (lacune_signals + detect_candidate_signals(exported)
               + detect_insurance_gap_signal(compute["breakdown"]))
    return 0, format_report(results, periode=str(periode), signals=signals)


def main():
    try:
        rc, out = run_main(sys.argv[1:])
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 2
    print(out)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
