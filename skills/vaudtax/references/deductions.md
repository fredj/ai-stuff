# Deduction Rules and Limits

Official rules for Canton Vaud (ICC) and federal (IFD) deductions. Source: [Instructions générales 21001](https://www.vd.ch/fileadmin/user_upload/organisation/dfin/aci/fichiers_pdf/21001_2025.pdf) (2025 edition — URL is year-specific, update for other fiscal years).
Limits are indexed annually — verify the year matches the declaration's `fiscalPeriod`.

## Contents

- [Transport — CODE 140](#transport--code-140)
- [Repas — CODE 150](#repas--code-150)
- [Autres frais professionnels — CODE 160](#autres-frais-professionnels--code-160)
- [Assurances — CODE 300](#assurances--code-300)
- [Pilier 3a — CODE 310](#pilier-3a--code-310)
- [Intérêts capitaux d'épargne — CODE 480](#intérêts-capitaux-dépargne--code-480)
- [Déduction logement — CODE 660](#déduction-logement--code-660)
- [Frais médicaux — CODE 710](#frais-médicaux--code-710)
- [Verification checklist](#verification-checklist)

---

## Transport — CODE 140

**ICC:** Forfait table based on shortest one-way distance (transport public). NOT the actual subscription cost.

| Distance (km) | ICC annual (CHF) | | Distance (km) | ICC annual (CHF) |
|---|---|---|---|---|
| 20 | 3'001 | | 35 | 3'448 |
| 25 | 3'136 | | 40 | 3'608 |
| 30 | 3'288 | | 45 | 3'768 |
| 31 | 3'320 | | 51+ | 4'080 (max) |

Full table in instructions pp. 19–20. Capped at the most expensive 2nd-class general pass (= 51 km forfait).

**IFD:** Capped at **CHF 3'300** per employed person regardless of distance.

**2025 limits:** ICC max CHF 4'080 / IFD max CHF 3'300

---

## Repas — CODE 150

**ICC and IFD:** Per-day forfait, capped annually.

| Type | Per day | Max/year |
|---|---|---|
| `HORS_DOMICILE_NORMAL` (regular lunch outside) | CHF 15 | CHF 3'200 |
| Cantine or employer subsidy (`contributionFraisRepas` = true on salary cert) | CHF 7.50 | CHF 1'600 |

Deduction = `min(nbJours × per_day, annual_cap)`. Part-time taxpayers with fewer working days do not reach the cap.

---

## Autres frais professionnels — CODE 160

**ICC and IFD:** Forfait = **3% of `salaireNet`**, min CHF 2'000, max CHF 4'000.

Cross-check: `ctb1_forfait_chf` should equal `max(2000, min(4000, round(salaireNet × 0.03)))`.

---

## Assurances — CODE 300

Deduction = **min(net premiums after subsidies, family-status cap)**. The cap is always applied — declared gross amounts above the cap have no fiscal impact.

**ICC caps (2025):**

| Situation familiale | Max ICC |
|---|---|
| Célibataire / veuf / séparé / divorcé | CHF 5'000 |
| Marié / partenariat enregistré | CHF 9'900 |
| + par enfant (part 0.5 sous code 810) | + CHF 1'300 |

**IFD caps (2025):**

| Situation familiale | Max IFD |
|---|---|
| Célibataire | CHF 1'800 |
| Marié / partenariat enregistré | CHF 3'700 |
| + par enfant / personne à charge | + CHF 700 |

> If net premiums ≥ ICC cap, the actual deduction equals the cap regardless of whether all premiums are individually justified. Missing justifications for amounts above the cap have no fiscal impact.

---

## Intérêts capitaux d'épargne — CODE 480

**ICC:** Savings interest income from private wealth (savings accounts, postal accounts, Swiss/foreign bonds, mortgages, etc.) is deductible up to:

| Situation familiale | Max ICC |
|---|---|
| Célibataire / veuf / séparé / divorcé | CHF 1'600 |
| Marié / partenariat enregistré | CHF 3'300 |
| + par enfant (part 0.5 code 810) | + CHF 300 |

**Excluded:** dividends, equity fund distributions, and any income without the character of savings interest are **not deductible** under code 480.

**IFD:** Code 480 is combined with code 300 (assurances) and code 340 under a single IFD cap — see Key differences table. It is not a separate line item for IFD.

**Will-be-zero check:** if the taxpayer has no savings interest declared under code 410, deduction = CHF 0.

---

## Pilier 3a — CODE 310

**ICC and IFD (2025):**

| Situation | Max |
|---|---|
| Assuré au 2e pilier (LPP) | CHF 7'258 |
| Non assuré au 2e pilier | CHF 36'288 (20% of net lucrative income) |

Cross-check: sum of all form 21 EDP attestations per taxpayer must equal `formesReconnuesPrevoyanceIndividuelleContribuable1/2` and must not exceed the applicable maximum. Missing attestations = unjustified declaration.

---

## Déduction logement — CODE 660

**ICC only** — does not exist for IFD.

**Formula:** `max(0, min(min(loyer_sans_charges, plafond_loyer) − 20% × code_650, max_deduction))`

| Situation | Plafond loyer déterminant | Max déduction |
|---|---|---|
| Célibataire / veuf / séparé / divorcé | CHF 11'100 | CHF 6'800 |
| Marié / partenariat enregistré | CHF 13'700 | CHF 6'800 |
| + par enfant (entretien complet) | + CHF 3'700 | — |

The CHF 6'800 absolute cap applies regardless of family situation.

- `loyer_sans_charges` = annual rent **excluding charges** (not the figure in the declaration, which may include charges)
- `code_650` = revenu net after all deductions (estimated from the declaration)

**Will-be-zero check:** if `20% × code_650 ≥ plafond_loyer`, deduction = CHF 0. For a célibataire, this occurs when code 650 ≥ ~CHF 55'500. High earners typically get no rent deduction.

---

## Frais médicaux — CODE 710

**ICC:** Deductible only if frais exceed **5% of code 700** (revenu net soumis à l'impôt cantonal — after all professional deductions, not the raw net salary). Only the excess above the threshold is deductible.

**IFD:** Same 5% threshold applied to revenu intermédiaire II (formula: `revenu_intermédiaire_II × 5/95`, capped at declared frais at code 710).

> For a salaried person, code 700 ≈ net salary + investment income − professional deductions. Compute `5% × code_700` before flagging medical costs as a tax saving. With a high income, the threshold is rarely reached.

---

## Verification checklist

When verifying deductions, cross-check supporting documents **and** apply deduction rules:

1. **Salary certificate** → cross-check fields C/D/E, lines 10.1, 11, 15 against XML
2. **3a attestations** → sum per taxpayer vs declared; check ≤ annual max; flag missing docs
3. **Transport** → look up declared km in forfait table; verify IFD ≤ CHF 3'300
4. **Repas** → confirm ≤ CHF 3'200 (or ≤ CHF 1'600 if cantine)
5. **Autres frais prof.** → verify 3% × salaireNet ∈ [2'000, 4'000]
6. **Assurances** → compute min(net premiums, ICC cap) and min(net premiums, IFD cap); assess impact of any unjustified amounts
7. **Intérêts épargne (code 480)** → ICC deduction = min(savings interest from code 410, cap); verify only savings-type income is included, not dividends
8. **Logement** → compute min(loyer, plafond) − 20% × code_650; flag if zero
9. **Frais médicaux** → compute 5% × code_700; flag if frais < threshold (deduction = 0)
10. **Portfolio / titres** → cross-check fiscal value, gross dividends, withholding tax (IES) against broker statement
