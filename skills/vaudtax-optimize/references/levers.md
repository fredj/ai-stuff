# Tax-Reduction Levers

Catalog of the levers `optimize.py` reasons about. This file does **not** restate the deduction rules — those are the canonical, sourced rules in [`../../vaudtax/references/deductions.md`](../../vaudtax/references/deductions.md), keyed by CODE. Here we map each lever to its type, declaration CODE, 2025 cap, whether the ICC and IFD deltas differ, and the exact `optimize.py --lever` string.

All caps below are **2025 values** and are indexed annually — verify the year matches the declaration's `fiscalPeriod` before trusting any figure, and re-read the cited CODE section in `deductions.md`.

## The three-mechanism model

A saving can only come from one of three places:

1. **Gap-to-cap, auto-detected.** A contribution with explicit headroom to a hard cap. Only **pilier 3a (CODE 310)** is auto-detected by `optimize.py` — it computes `7258 − declared` itself. No `--lever` needed.
2. **Forfait under-claim.** A formula-based deduction left below its mechanical maximum. There are none to exploit here: transport (140), repas (150) and autres frais (160) are already auto-maximised by `compute_code800` — see below. Do not offer them as levers.
3. **Entitlement levers, passed explicitly.** Deductions the taxpayer is entitled to but that require an eligibility judgment and/or supporting evidence (childcare, formation, dons, debt interest, LPP buy-back). `optimize.py` cannot compute a CHF amount for these from the declaration alone, so they are passed with `--lever "name:icc=N,ifd=N[,cost=N][,type=...]"`.

For two of these codes, `optimize.py` auto-detects the *evidence* (not the amount) and prints it as a "Signals found" line, so the agent doesn't have to already know to look: code 618 (training costs already present in the XML), and code 610 (real estate declared with no debt interest at all). These are still questions, not findings — confirm eligibility before turning one into a `--lever`.

`optimize.py` also auto-detects a **gap-to-cap** signal on code 300 (declared insurance premiums below the ICC cap) the same way it does for pilier 3a — but unlike 3a there's no "top up" action: the gap only becomes real money if the taxpayer already holds an undeclared, deductible premium (accident, life, health for a dependent). Always a question — see `references/questions.md`.

A lever is a **real saving only when both** (a) the rule holds (cited in `deductions.md`) **and** (b) the taxpayer's eligibility is evidenced in the declaration. If either is unconfirmed, it is a **question for the user, not a finding** — surface it as such.

## Lever string syntax

`--lever "name:icc=N,ifd=N[,cost=N][,type=recoverable|forward]"`

- `icc` / `ifd` — the deduction amount applied to each base. Where the cap differs between ICC and IFD, these differ.
- `type`:
  - `recoverable` — taxpayer was already entitled and simply didn't claim it → amend/refile, **no new spending** (cost 0).
  - `forward` — requires committing cash; `cost` defaults to the `icc` amount.
- `cost` — override the implied cost (e.g. a forward lever where outlay ≠ icc delta).

## Lever catalog

| CODE | Lever | `--lever` name | Type | Cap (2025) | ICC vs IFD | Detection |
|---|---|---|---|---|---|---|
| [310](../../vaudtax/references/deductions.md#pilier-3a--code-310) | Pilier 3a | `3a` | forward | CHF 7'258 (with LPP) | equal | **auto-detected** (gap to 7258; surfaced as a `lacune_3a` signal instead if the declaration year is already closed — see below) |
| [320](../../vaudtax/references/deductions.md#pilier-3a--code-310) | Rachat LPP / 2e pilier buy-back | `rachat` | forward | per LPP certificate | equal | explicit |
| [670](../../vaudtax/references/deductions.md#frais-de-garde--code-670) | Frais de garde / childcare | `garde` | recoverable | ICC 15'200 / IFD 25'800 per child | **differ** | explicit |
| [618](../../vaudtax/references/deductions.md#frais-de-formation-et-perfectionnement--code-618) | Frais de formation | `formation` | recoverable | ICC 12'000 / IFD 13'000 per person | **differ** | explicit |
| [720](../../vaudtax/references/deductions.md#dons--code-720) | Dons / donations | `dons` | recoverable | ICC 20% of code 700 / IFD 20% of revenu interm. I; min CHF 100/yr | bases differ | explicit |
| [540](../../vaudtax/references/deductions.md#frais-dentretien-dimmeuble--code-540) | Frais d'entretien d'immeuble | `entretien` | recoverable | ICC 10–30% of valeur locative / revenu net immeuble, by age+use; IFD 10%/20% by 10-yr age | **differ** (different age thresholds) | explicit — not file-detectable, ask |
| [610](../../vaudtax/references/deductions.md#intérêts-passifs--dettes-privées--code-610) | Intérêts passifs / debt interest | `interets` | recoverable | gross wealth yield + CHF 50'000 | equal ceiling | explicit |
| [235](../../vaudtax/references/deductions.md#double-activité-des-conjoints--code-235) | Double activité des conjoints | — | — | ICC 1'700 / IFD 50% of lower income ∈ [8'600, 14'100] | **differ** | **auto-applied by `compute_code800`, not a lever** |
| [300](../../vaudtax/references/deductions.md#assurances--code-300) | Assurances / undeclared premium | — | recoverable | ICC 5'000 (single) / 9'900 (married) | differ (combined line for IFD) | **auto-detected signal** (gap to ICC cap) |
| 140 / 150 / 160 | Transport / repas / autres frais | — | — | — | — | **auto-maxed, not a lever** |

### CODE 310 — Pilier 3a (forward, auto-detected)

Cap CHF 7'258 for taxpayers affiliated to the 2e pilier (LPP); ICC = IFD. `optimize.py` computes the headroom as `7258 − declared` on its own — **do not pass a `--lever` for it.** (Non-LPP-affiliated taxpayers have a higher cap; see the CODE 310 table in `deductions.md` — that case is not auto-detected.)

**If the declaration's `fiscalPeriod` is already closed** (a past year), this gap is **not** a same-year top-up any more — `optimize.py` surfaces it as a `"lacune_3a"` signal instead of a scenario. The real lever is a **rachat de lacune 3a** (see `deductions.md` CODE 310) claimed on a later, still-open year: same CHF amount (the prior year's actual shortfall), but computed against *that* year's income and rate — never the closed year's baseline. Conditions to confirm with the user before quoting a saving: the 10-year window, the buy-back year's ordinary contribution paid in full first, and the provider actually offering the feature (from 2026). Once confirmed, compute it as an explicit forward `--lever` on the buy-back year's own declaration/simulation, not on this one.

### CODE 320 — Rachat LPP / 2e pilier buy-back (forward)

Deductible in full; ICC = IFD. The available capacity comes **only** from the LPP certificate (rachat potential) — **never invent or estimate it.** If the certificate is not in the declaration, this is a question for the user, not a finding.

```
--lever "rachat:icc=10000,ifd=10000,type=forward"
```

### CODE 670 — Frais de garde / childcare (recoverable if eligible)

ICC cap CHF 15'200/child, IFD cap CHF 25'800/child — **ICC ≠ IFD**. Eligibility: child under 14 in the household, care incurred because the parent(s) work/train/cannot work, documented.

```
--lever "garde:icc=15200,ifd=25800,type=recoverable"
```

### CODE 618 — Frais de formation (recoverable if eligible)

ICC cap CHF 12'000/person, IFD cap CHF 13'000/person — **ICC ≠ IFD**. Eligibility: not formation initiale, costs borne by the taxpayer (not employer/foundation).

```
--lever "formation:icc=12000,ifd=13000,type=recoverable"
```

### CODE 720 — Dons / donations (recoverable if eligible)

ICC capped at 20% of code 700; IFD capped at 20% of revenu intermédiaire I; total gifts must reach min CHF 100/year. The ICC and IFD bases differ, so the same donation can hit different caps. Pass the **actual donation amounts**, kept within the 20% cap on each base.

```
--lever "dons:icc=2000,ifd=2000,type=recoverable"
```

### CODE 540 — Frais d'entretien d'immeuble (recoverable if eligible)

Only applies to a **built** property (`batimentExiste = true`); an unbuilt land parcel has no maintenance deduction. `optimize.py` cannot detect this at all today — `parse_vaudtax.py`/`export_json.py` don't yet extract building age, `batimentExiste`, or declared maintenance costs (see `xml-sections.md`). Always ask; never auto-signal. Once eligibility, building age, and use (occupied/rented) are confirmed, compute the flat-rate or actual-cost amount per the ICC/IFD tables in `deductions.md`.

```
--lever "entretien:icc=6000,ifd=6000,type=recoverable"
```

### CODE 610 — Intérêts passifs / debt interest (recoverable if eligible)

Deductible up to gross wealth yield + CHF 50'000; **same ceiling for ICC and IFD**. Excludes amortisation (capital repayment), construction-credit interest, and leasing.

```
--lever "interets:icc=3000,ifd=3000,type=recoverable"
```

### CODE 235 — Double activité des conjoints (NOT a lever)

Already computed by `compute_code800` in the baseline for jointly-taxed couples where both spouses have work income (`code235_icc` / `code235_ifd` in the breakdown). Passing it as a `--lever` would deduct it twice.

### CODES 140 / 150 / 160 — Transport, repas, autres frais (NOT levers)

These are auto-maximised by `compute_code800`: transport uses the forfait table to the cap, repas applies the per-day forfait to the annual cap, and autres frais is the mechanical 3% × salaireNet within [2'000, 4'000]. There is **no headroom** to claim. Do **not** offer them as levers and do not pass `--lever` strings for them.
