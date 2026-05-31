# Pillar Attestation (Form 21 EDP / Attestation cotisations de prévoyance)

Official federal form 21 EDP (trilingual DE/FR/IT), issued by bank foundations and insurance companies for 2nd pillar and 3a accounts. Read with `read_pdf()` from `pdf_utils.py`.

## Extraction

```python
from pdf_utils import read_pdf, extract_form21_totals, extract_postfinance_3a

text = read_pdf("/tmp/doc.pdf")

if "Form. 21 EDP" in text:
    contributions, rachats = extract_form21_totals(text) or (None, None)
else:
    # PostFinance "Attestation fiscale" format
    contributions = extract_postfinance_3a(text)
```

`extract_form21_totals()` returns `(contributions, rachats)` as integers in CHF, or `None`. It matches totals by content ("Total … Säule 3a / pilier 3a"), not by field letter (which varies between editions).

## Form editions

| Edition | Total 3a contributions | Total 3a rachats | Birthdate field |
|---|---|---|---|
| 2025 (current) | field **q** | field **x** | field **c** |
| 2011 | field **r** | field **s** | field **d** |

Do not rely on field letters for extraction — use `extract_form21_totals()`.

## Structure

**Section 1 — 2nd pillar** (`Cotisations à des institutions de prévoyance professionnelle, 2e pilier`): voluntary LPP buy-ins, ordinary contributions, dates.

**Section 2 — Pillar 3a** (`Cotisations pour des formes reconnues de prévoyance individuelle liée`):

| Field (2025) | Label | VaudTax XML field |
|---|---|---|
| **a** | Nom et siège de l'institution | — |
| **b/c** | Numéro d'assuré AVS | should match `navs13` in `taxpayerPersonalData1` |
| **c/d** | Date de naissance | should match `birthdate` in `taxpayerPersonalData1` |
| **l/m** | No de police / No de contrat | — |
| **n** | Conclusion | contract opening year |
| **p/q** | Année | should match `fiscalPeriod` |
| **q/r** | **Total cotisations au pilier 3a** | summed → `formesReconnuesPrevoyanceIndividuelleContribuable1` |

**Section 3 — Rachats** (`Rachats pour des formes reconnues de prévoyance individuelle liée`): contract number, fiscal period, prior contributions, buy-in date, amount, total (field **x** in 2025, **s** in 2011).

## Taxpayer attribution (joint filers)

```python
from pdf_utils import identify_taxpayer

ctb1 = {"navs13": "756.XXXX.XXXX.XX", "birthdate": "YYYY-MM-DD", "last_name": "Dupont", "first_name": "Jean"}
ctb2 = {"navs13": "756.XXXX.XXXX.YY", "birthdate": "YYYY-MM-DD", "last_name": "Martin", "first_name": "Marie"}
taxpayer = identify_taxpayer(text, ctb1, ctb2)  # returns "CTB1", "CTB2", or None
```

## Cross-checking against the declaration

1. Extract all attestation PDFs (label contains "cotisations", "21 EDP", or "pilier 3a")
2. Read each with `read_pdf()`, detect format, extract totals
3. For joint filers, call `identify_taxpayer()` per document
4. Sum per taxpayer and compare:
   - CTB1 sum → `formesReconnuesPrevoyanceIndividuelleContribuable1`
   - CTB2 sum → `formesReconnuesPrevoyanceIndividuelleContribuable2`
5. Discrepancy → likely a missing attestation or data-entry error

A taxpayer may hold several 3a accounts — each produces a separate attestation.
