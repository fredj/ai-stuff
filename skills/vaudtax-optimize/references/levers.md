# Tax-Reduction Levers

Catalog of the levers `optimize.py` reasons about. This file does **not** restate the deduction rules — those are the canonical, sourced rules in [`../../vaudtax/references/deductions.md`](../../vaudtax/references/deductions.md), keyed by CODE. Here we map each lever to its type, declaration CODE, 2025 cap, whether the ICC and IFD deltas differ, and the exact `optimize.py --lever` string.

All caps below are **2025 values** and are indexed annually — verify the year matches the declaration's `fiscalPeriod` before trusting any figure, and re-read the cited CODE section in `deductions.md`.

## The three-mechanism model

A saving can only come from one of three places:

1. **Gap-to-cap, auto-detected.** A contribution with explicit headroom to a hard cap. Only **pilier 3a (CODE 310)** is auto-detected by `optimize.py` — it computes `7258 − declared` itself. No `--lever` needed.
2. **Forfait under-claim.** A formula-based deduction left below its mechanical maximum. There are none to exploit here: transport (140), repas (150) and autres frais (160) are already auto-maximised by `compute_code800` — see below. Do not offer them as levers.
3. **Entitlement levers, passed explicitly.** Deductions the taxpayer is entitled to but that require an eligibility judgment and/or supporting evidence (childcare, formation, dons, debt interest, double-activité, LPP buy-back). `optimize.py` cannot detect these from the declaration alone, so they are passed with `--lever "name:icc=N,ifd=N[,cost=N][,type=...]"`.

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
| [310](../../vaudtax/references/deductions.md#pilier-3a--code-310) | Pilier 3a | `3a` | forward | CHF 7'258 (with LPP) | equal | **auto-detected** (gap to 7258) |
| [320](../../vaudtax/references/deductions.md#pilier-3a--code-310) | Rachat LPP / 2e pilier buy-back | `rachat` | forward | per LPP certificate | equal | explicit |
| [670](../../vaudtax/references/deductions.md#frais-de-garde--code-670) | Frais de garde / childcare | `garde` | recoverable | ICC 15'200 / IFD 25'800 per child | **differ** | explicit |
| [618](../../vaudtax/references/deductions.md#frais-de-formation-et-perfectionnement--code-618) | Frais de formation | `formation` | recoverable | ICC 12'000 / IFD 13'000 per person | **differ** | explicit |
| [720](../../vaudtax/references/deductions.md#dons--code-720) | Dons / donations | `dons` | recoverable | ICC 20% of code 700 / IFD 20% of revenu interm. I; min CHF 100/yr | bases differ | explicit |
| [610](../../vaudtax/references/deductions.md#intérêts-passifs--dettes-privées--code-610) | Intérêts passifs / debt interest | `interets` | recoverable | gross wealth yield + CHF 50'000 | equal ceiling | explicit |
| [235](../../vaudtax/references/deductions.md#double-activité-des-conjoints--code-235) | Double activité des conjoints | `double` | recoverable | ICC 1'700 / IFD 50% of lower income ∈ [8'600, 14'100] | **differ** | explicit (married only) |
| 140 / 150 / 160 | Transport / repas / autres frais | — | — | — | — | **auto-maxed, not a lever** |

### CODE 310 — Pilier 3a (forward, auto-detected)

Cap CHF 7'258 for taxpayers affiliated to the 2e pilier (LPP); ICC = IFD. `optimize.py` computes the headroom as `7258 − declared` on its own — **do not pass a `--lever` for it.** (Non-LPP-affiliated taxpayers have a higher cap; see the CODE 310 table in `deductions.md` — that case is not auto-detected.)

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

### CODE 610 — Intérêts passifs / debt interest (recoverable if eligible)

Deductible up to gross wealth yield + CHF 50'000; **same ceiling for ICC and IFD**. Excludes amortisation (capital repayment), construction-credit interest, and leasing.

```
--lever "interets:icc=3000,ifd=3000,type=recoverable"
```

### CODE 235 — Double activité des conjoints (recoverable, married only)

ICC CHF 1'700; IFD 50% of the lower work income within [8'600, 14'100] — **ICC ≠ IFD**. Applies only to jointly-taxed couples where both spouses have a lucrative activity.

```
--lever "double:icc=1700,ifd=10000,type=recoverable"
```

### CODES 140 / 150 / 160 — Transport, repas, autres frais (NOT levers)

These are auto-maximised by `compute_code800`: transport uses the forfait table to the cap, repas applies the per-day forfait to the annual cap, and autres frais is the mechanical 3% × salaireNet within [2'000, 4'000]. There is **no headroom** to claim. Do **not** offer them as levers and do not pass `--lever` strings for them.
