---
name: vaudtax
description: Working with .vaudtax files (Swiss canton Vaud tax declarations). Use when the user mentions a .vaudtax file, wants to read/summarize/convert a VD tax declaration, or inspect tax data (income, deductions, assets, attached documents).
---

# VaudTax Skill

## File format

A `.vaudtax` file is a **ZIP archive** containing:

- **One XML file** (named `<filename>.xml`) — the entire tax declaration as structured XML under the namespace `http://www.vd.ch/fiscalite/vaudtax`, root element `<vaudTaxData>`.
  - **Namespace:** `http://www.vd.ch/fiscalite/vaudtax` (proprietary format, no public XSD available)
  - **XML Declaration:** UTF-8 encoding, standalone mode
  - **Structure:** 32+ main sections organizing all tax declaration data
- **Zero or more `doc*` files** — attached supporting documents. Can be **PDF** (`application/pdf`), **JPEG** (`image/jpeg`), or **PNG** (`image/png`). The format is declared in the XML's `<mimeType>` field.

## Bundled scripts

All scripts live in `${CLAUDE_SKILL_DIR}/scripts/` and use only Python standard library — no installs needed.

| Script | Purpose |
|---|---|
| `parse_vaudtax.py <file.vaudtax>` | Parse and print a human-readable summary to stdout |
| `export_json.py <file.vaudtax> [out.json]` | Export clean JSON (omits UI/navigation state) |
| `compute_code800.py <file.vaudtax>` | Estimate revenu imposable ICC (code 800), IFD, and fortune from a declaration — outputs values ready to pass to `calculate_taxes.py` |
| `calculate_taxes.py --periode YEAR --commune NAME --revenu-icc N --fortune-icc N --revenu-ifd N` | Query the official Canton Vaud tax calculator via HTTP POST and return authoritative results |

The JSON output conforms to **`${CLAUDE_SKILL_DIR}/vaudtax-export.schema.json`** (JSON Schema 2020-12). Refer to it for the full field-level documentation of every section.

### Usage

```bash
cd "${CLAUDE_SKILL_DIR}/scripts"

# Summarize a declaration
python parse_vaudtax.py /path/to/file.vaudtax

# Export as JSON
python export_json.py /path/to/file.vaudtax
```

## Key XML sections

### Metadata & Taxpayer Info
| Section | Description |
|---|---|
| `fiscalPeriod` | ✅ Tax year (e.g. `2025`) |
| `lastGesdemReference` | ✅ Gesdem submission reference |
| `identification` | ✅ Address, municipality, phone, email, IBAN, account holder info |
| `taxpayerPersonalData1` | ✅ Name, birthdate, NAVS13, profession, working location, marital status, working situation |
| `taxpayerPersonalData2` | ✅ Second taxpayer personal data (joint filers only) |
| `representative` | Tax representative details (not yet parsed) |

### Income
| Section | Description |
|---|---|
| `activiteSalarieeRevenus` | ✅ Employed income: employer, net salary, pension contributions, dates, activity rate |
| `complementRentePension` | ✅ Pension/rente income: type, annual amount |
| `activitesIndependantes` | ✅ Self-employment/independent activity income: activity name, net revenue |
| `autresRevenusExoneresImposesSource` | Other income from various sources (not yet parsed) |
| `revenuImposeAutreEtat` | Income taxed in other states (not yet parsed) |

### Deductions & Expenses
| Section | Description |
|---|---|
| `autresFraisEtFraisActiviteSalarialeAccessoire` | ✅ Professional expense deduction method (flat-rate or actual) |
| `fraisTransport` | ✅ Transport costs: type, km, number of days, route |
| `fraisRepas` | ✅ Meal costs: type, number of days |
| `primesEtCotisationsAssurance` | ✅ Insurance premiums, subsidies, 3rd pillar (3a) contributions |
| `deductionSocialeLogement` | ✅ Rent/housing deduction |
| `fraisMedicauxDentaires` | ✅ Medical and dental expenses |
| `interetsDettes` | ✅ Debt interest deductions (code 520): CTB1/CTB2 amounts |
| `fraisFormation` | ✅ Training/education costs: amount per taxpayer |
| `donationsAvancesHoiries` | ✅ Donations and inheritance advances given/received (with kinship, date, amount, counterparty) |
| `successionHoirieDonation` | Inheritances flag section (skipped when `isInitialized=false`) |

### Assets & Securities
| Section | Description |
|---|---|
| `etatTitres` | ✅ Bank accounts: IBAN, balance, yield |
| `relevesFiscauxBancaires` | ✅ Investment portfolios: fiscal value, gross income, IES |
| `numerairesList` | ✅ Cash and liquid assets |
| `objetsMobiliers` | ✅ Movable property / crypto: description, market value |
| `biensImmobiliers` (2025) / `immeubles` (older) | ✅ Real estate: commune, parcelle, estimation fiscale, rental income, ownership share, acquisition date, built/non-built |
| `autoMoto` | ✅ Vehicles: description, market value |
| `fraisAdministrationTitres` | ✅ Management fees for securities (code 490) |

### Supporting Documents & Navigation
| Section | Description |
|---|---|
| `piecesJustificativesObligatoires` | Mandatory supporting document metadata |
| `piecesJustificativesFacultatives` | Optional supporting document metadata |
| `infosComplementairesIes` | Additional investment income (IES) information |
| `prestationsEnCapital` | Capital benefit payments |
| `guidedNav` | UI/navigation state (form display preferences) |
| `userProfil` | User profile and preferences |

## Summarizing a file

When asked to summarize or read a `.vaudtax` file, run `parse_vaudtax.py` and present the output. If the user wants a richer explanation, use this structure:

1. **Filing info** — fiscal year, reference, submission date (from filename), municipality
2. **Taxpayer(s)** — name, birthdate, civil status, profession, address; CTB2 data if joint filer
3. **Income** — employed activity, pension/rentes, self-employment; employer/net salary/period for each
4. **Deductions** — transport, meals, professional expenses, insurance/3rd pillar, rent, medical, debt interest, education costs
5. **Assets** — bank accounts with balance and yield, investment portfolios, cash, real estate, vehicles, movable objects
6. **Attached documents** — list of attached files (PDF/JPEG/PNG) with their filename and size

Amounts are in CHF unless a different `devise` is specified.

**A summary is just a summary.** Do not run `compute_code800.py` or `calculate_taxes.py` unless the user explicitly asks for a tax estimate. Running the tax scripts uninvited adds latency and produces figures the user didn't ask for.

### Proactive cross-checks during a summary

Even for a basic summary, always cross-check attached documents against their corresponding XML values — discrepancies are high-value findings the user needs before filing.

**Pillar 3a attestations** — whenever `piecesJustificativesFacultatives` or `piecesJustificativesObligatoires` lists one or more attachments whose label contains "21 EDP" or "cotisations" or "pilier 3a":
1. Read each attestation PDF with `read_pdf()` and extract the total using `extract_form21_totals()` (or `extract_postfinance_3a()` for PostFinance format)
2. Sum the amounts per taxpayer and compare against `formesReconnuesPrevoyanceIndividuelleContribuable1` / `...Contribuable2` in `primesEtCotisationsAssurance`
3. If the sums differ, flag it prominently: **"⚠ Écart pilier 3a : attestations CHF X, déclaration CHF Y — vérifier avant envoi"**

**Salary certificates** — whenever a label contains "Certificat de salaire" and the taxpayer has one `activiteSalarieeRevenus` entry:
1. Read the PDF and extract line 11 (salaire net) and line 10.1 (cotisation LPP)
2. Compare against `salaireNet` and `cotisationOrdinaire` in the corresponding XML entry
3. Flag any mismatch — small rounding differences (±1 CHF) are normal; larger gaps are not

These checks take a few extra seconds but can catch real errors. Run them as part of every summary unless the user explicitly says they only want a quick overview.

When verifying or cross-checking deductions, see [DEDUCTIONS.md](DEDUCTIONS.md) for official rules, caps (ICC and IFD), and the analysis checklist.

To estimate taxes due from the declared figures, see [TAX_COMPUTATION.md](TAX_COMPUTATION.md) for the ICC and IFD formulas (any Vaud municipality).

## Full analysis — always include taux marginal

For any **full analysis** of a `.vaudtax` file (i.e. when running both `compute_code800.py` and `calculate_taxes.py`), **always also compute the taux marginal d'imposition** by running `calculate_taxes.py` with the `--marginal-rate` flag:

```bash
python calculate_taxes.py \
  --periode YEAR \
  --commune "Commune" \
  --revenu-icc N --fortune-icc N --revenu-ifd N \
  --marginal-rate
```

This makes two HTTP calls (base and base+1000 CHF) and returns the marginal rate for ICC, IFD, and the combined total.

Include the marginal rate in the output under the tax estimates section:

| | Taux marginal |
|---|---|
| ICC (cantonal + communal) | X.XX % |
| IFD (fédéral direct) | X.XX % |
| **Total** | **X.XX %** |

## Reading attached PDFs

Attached PDFs may be text-based or scanned images. Use the bundled `${CLAUDE_SKILL_DIR}/scripts/pdf_utils.py`:

```python
from pdf_utils import read_pdf, extract_form21_totals, identify_taxpayer

text = read_pdf("/tmp/doc.pdf")               # text PDF or scanned — handled automatically
text = read_pdf("/tmp/doc.pdf", lang="deu")   # switch to German if needed
```

`read_pdf()` tries `pdfplumber` first; falls back to `pytesseract` OCR at 200 dpi for scanned PDFs. JPEG/PNG attachments go straight to OCR. Use `lang="fra"` (default) for French documents; `"deu"` for German-only ones.

## Reading attached salary certificates (Certificat de salaire / Lohnausweis)

The Swiss salary certificate is a standardized federal form (form 11) used by all employers. It is typically attached as a PDF labeled "Certificat de salaire". Read it with `read_pdf()` defined above.

### Numbered fields on the certificate

The form has numbered lines — these are the only values that matter for tax purposes:

| Line | Label (FR) | Description | Reported in VaudTax as |
|---|---|---|---|
| 1 | Salaire / Rente | Base salary (excluding lines 2–7) | — (not stored separately) |
| 2.1 | Verpflegung, logement | Benefits in kind: meals/lodging | checkbox `transportGratuit` / `contributionFraisRepas` |
| 2.2 | Part privée voiture | Private use of company car | — |
| 2.3 | Autres prestations | Other benefits in kind | — |
| 3 | Prestations non périodiques | Irregular payments, bonuses | — (not stored separately) |
| 4 | Prestations en capital | Capital payments | — |
| 5 | Droits de participation | Employee stock/options (see annex) | — |
| 6 | Indemnités administrateur | Board member fees | — |
| 7 | Autres prestations | Other payments | — |
| **8** | **Salaire brut total** | **Sum of lines 1–7** | **— (not stored)** |
| 9 | Cotisations AVS/AI/APG/AC/AINP | Social security deductions | — (not stored) |
| **10.1** | **Cotisations LPP (ordinaires)** | **2nd pillar pension contributions** | **`cotisationOrdinaire`** |
| 10.2 | Cotisations LPP (rachat) | 2nd pillar buy-in contributions | — |
| **11** | **Salaire net** | **Line 8 − lines 9 − 10** | **`salaireNet`** ← key field |
| 12 | Impôt à la source | Withholding tax deducted | — |
| 13.1 | Frais effectifs | Actual expense reimbursements | — |
| 13.2 | Frais forfaitaires | Flat-rate expense reimbursements | — |
| 13.3 | Contributions au perfectionnement | Training contributions | checkbox `contributionPerfectionnement` |
| 14 | Autres prestations accessoires | Other accessory benefits | — |
| **15** | **Remarques** | **Free text: PC famille, special notes** | **`autreCotiContractuelle`** (e.g. PC famille amount) |

**Letter fields** (top of the form):
| Letter | Meaning | VaudTax field |
|---|---|---|
| **C** | **NAVS13 + date of birth** | must match `navs13` + `dateNaissance` in `taxpayerPersonalData1` |
| **D** | **Tax year** | must match `fiscalPeriod` |
| **E** | **Employment period (from – to)** | must match `dateDebut` / `dateFin` in `activiteSalarieeRevenus` |
| F | Transport gratuit domicile–travail | `transportGratuit` (true/false) |
| G | Repas à la cantine / chèques-repas | `contributionFraisRepas` (true/false) |

### What VaudTax actually uses

VaudTax only stores a subset of the certificate:
- **Employer name** (`employeur`)
- **Line 10.1** (`cotisationOrdinaire`) — LPP/2nd pillar deduction
- **Line 11** (`salaireNet`) — the single most important number
- **Line 13.3** (`contributionPerfectionnement`) — training contribution checkbox
- **Line 15 remarks** (`autreCotiContractuelle`) — e.g. PC famille contribution
- Checkboxes F and G

Lines 1, 3, 8, and 9 are **not stored** in the declaration — only the net result (line 11) is reported.

### Cross-checking a salary certificate against the declaration

When the user asks to verify a salary certificate:
1. Extract the PDF from the `.vaudtax` archive using the `doc*` key
2. Read it with `read_pdf()` (tries text extraction, falls back to OCR)
3. Read: field C (NAVS13 + birthdate), field D (year), field E (from/to), employer name, line 10.1 (LPP), line 11 (net salary), line 13.3 (perfectionnement checkbox), line 15 remarks
4. Compare against XML fields in `activiteSalarieeRevenus` (and `taxpayerPersonalData1`):
   - C (NAVS13) → `navs13` in `taxpayerPersonalData1`
   - C (birthdate) → `dateNaissance` in `taxpayerPersonalData1`
   - D → `fiscalPeriod`
   - E → `dateDebut` / `dateFin`
   - employer name → `employeur`
   - line 10.1 → `cotisationOrdinaire`
   - line 11 → `salaireNet`
   - line 13.3 → `contributionPerfectionnement` (true/false)
   - line 15 → `autreCotiContractuelle` (optional — may be absent if not applicable)
5. Note: VaudTax rounds to whole CHF — small rounding differences are normal

## Reading attached pillar attestations (Form 21 EDP / Attestation cotisations de prévoyance)

The Swiss pillar attestation is the official federal **form 21 EDP** (trilingual DE/FR/IT), issued by bank foundations and insurance companies for both 2nd pillar and 3a accounts. Read it with `read_pdf()` defined above.

To extract the totals, use `extract_form21_totals(text)` from `pdf_utils.py` — it returns `(contributions, rachats)` as integers in CHF, or `None` if absent. It identifies the total lines by their content ("Total … Säule 3a / pilier 3a") rather than the field letter, which varies between form editions (see below).

### Form editions

The form 21 EDP has been revised over time. **The field letters for the total lines differ between editions** — do not rely on them for extraction:

| Edition | Total 3a contributions | Total 3a rachats |
|---|---|---|
| 2025 (current) | field **q** | field **x** |
| 2011 | field **r** | field **s** |

The 2011 edition also places birthdate on field **d** instead of **c**.

### Structure of form 21 EDP

The form covers three distinct sections:

**Section 1 — 2nd pillar contributions** (`Cotisations à des institutions de prévoyance professionnelle, 2e pilier`):
Voluntary LPP buy-ins, ordinary contributions, employer contributions paid by the employee, dates.

**Section 2 — Pillar 3a contributions** (`Cotisations pour des formes reconnues de prévoyance individuelle liée`):

| Field (2025) | Label (FR) | Description | VaudTax XML field |
|---|---|---|---|
| **a** | Nom et siège de l'institution | Provider name and address | — |
| **b/c** | Numéro d'assuré AVS | AVS/NAVS13 number | should match `navs13` in `taxpayerPersonalData1` |
| **c/d** | Date de naissance | Birthdate of insured | should match `birthdate` in `taxpayerPersonalData1` |
| **l/m** | No de police / No de contrat | Policy or contract number | — |
| **n** | Conclusion | Contract opening year | — |
| **p/q** | Année | Tax year of the contribution | should match `fiscalPeriod` |
| **q/r** | **Total cotisations au pilier 3a** | **Total regular 3a contributions for the year** | summed → `formesReconnuesPrevoyanceIndividuelleContribuable1` |

**Section 3 — Pillar 3a buy-ins / rachats** (`Rachats pour des formes reconnues de prévoyance individuelle liée`):
Contract number, fiscal period, contributions already paid, buy-in date, buy-in amount, and total (field **x** in 2025, **s** in 2011).

### Non-standard formats

Some providers issue their own attestation format instead of form 21 EDP. Use `extract_postfinance_3a(text)` from `pdf_utils.py` for **PostFinance** "Attestation fiscale" PDFs — the amount appears on a line like `Année: 2024 CHF 3'000.00`. Detect which format you have by checking for `"Form. 21 EDP"` in the text.

### Taxpayer attribution of attached documents

Documents have **no explicit taxpayer field** in the XML. For single filers (`taxpayerPersonalData2` absent) all documents are CTB1. For joint filers, `parse_vaudtax.py` sets `taxpayer: None` on each attachment.

Two approaches to resolve attribution, depending on document type:

**Salary certificates** — cross-reference via employer name:
Each `activiteSalarieeRevenus` entry has `isContribuable1: true/false`. Read the employer name from the PDF and match it against the XML entries to determine which taxpayer the certificate belongs to.

**3a attestations and other documents** — content-based detection:
Use `identify_taxpayer(text, ctb1, ctb2)` from `pdf_utils.py`. It scores each taxpayer by matching identifiers found in the PDF text (birthdate DD.MM.YYYY, last name, NAVS13) against `taxpayerPersonalData1` and `taxpayerPersonalData2`:

```python
ctb1 = {"navs13": "756.XXXX.XXXX.XX", "birthdate": "YYYY-MM-DD", "last_name": "Dupont", "first_name": "Jean"}
ctb2 = {"navs13": "756.XXXX.XXXX.YY", "birthdate": "YYYY-MM-DD", "last_name": "Martin", "first_name": "Marie"}
taxpayer = identify_taxpayer(read_pdf("/tmp/doc.pdf"), ctb1, ctb2)
# returns "CTB1", "CTB2", or None if not determinable
```

### Cross-checking 3a attestations against the declaration

When the user asks to verify pillar 3a contributions:
1. Extract all insurance attachment PDFs from the `.vaudtax` archive (label contains "cotisations" or "assurance")
2. Read each with `read_pdf()`
3. For joint filers, call `identify_taxpayer()` to determine CTB1 vs CTB2 for each document
4. Detect format: `"Form. 21 EDP"` in text → use `extract_form21_totals()`; otherwise try `extract_postfinance_3a()`
5. Compare per taxpayer:
   - sum of CTB1 attestations → `formesReconnuesPrevoyanceIndividuelleContribuable1`
   - sum of CTB2 attestations → `formesReconnuesPrevoyanceIndividuelleContribuable2`
6. A discrepancy means an attachment is likely missing

A taxpayer may hold several 3a accounts — each produces a separate attestation.

## Extracting attached files

Each `<documents>` element in the XML has:
- `<key>` — the ZIP entry name (e.g. `doc17700000000000`), used to extract the file
- `<filename>` — the original filename as uploaded by the user
- `<mimeType>` — `application/pdf`, `image/jpeg`, or `image/png`
- `<label>` — human-readable description (e.g. "Activités salariées : Certificat de salaire")
- `<fileSize>` — size in bytes

Always use the `open_attachment()` context manager from `parse_vaudtax.py` — it extracts to a temp file and deletes it automatically on exit:

```python
from parse_vaudtax import open_attachment
from pdf_utils import read_pdf

with open_attachment("file.vaudtax", "doc17700000000000", suffix=".pdf") as path:
    text = read_pdf(path)
# temp file is deleted here
```

Use the `<key>` value (not the `<reference>` UUID) to match XML metadata to ZIP entries. The `parse_vaudtax.py` script lists all attachments with their key, filename, MIME type, size, and label.

## VaudTax XML Schema (Proprietary Format)

The VaudTax XML format is **proprietary and maintained by the Canton Vaud tax authority**. Key characteristics:

- **Namespace URI:** `http://www.vd.ch/fiscalite/vaudtax` (does not resolve; not publicly documented)
- **Root Element:** `<vaudTaxData>`
- **No XSD schema:** The XML files do not include `xsi:schemaLocation` references; the schema is not publicly available
- **Non-standard structure:** The format is tightly coupled with the official Canton Vaud tax declaration form and may change across fiscal years
- **32+ main XML sections** organizing all tax data (metadata, income, deductions, assets, supporting docs, UI state)

### Implications for Parsing
- Scripts must handle missing or optional sections gracefully
- Element names follow French naming conventions (e.g., `activiteSalarieeRevenus`, `fraisTransport`)
- No formal validation against a public schema; assume the structure is as documented above
- Future tax years may introduce new sections or change existing element names

### Field name discovery for newer sections

For sections added based on ECH-0119 cross-referencing (`complementRentePension`, `activitesIndependantes`, `interetsDettes`, `fraisFormation`, `immeubles`, `autoMoto`), the XML element names are inferred from VaudTax naming conventions and may need adjustment.

**Important:** These sections are always present in the XML even when unused, with `<isInitialized>false</isInitialized>`. The parsers skip such empty sections automatically. `activitesIndependantes` uses `<activitesIndependantesCtb1>` / `<activitesIndependantesCtb2>` sub-elements.

If a parsed field returns `None` unexpectedly, use this snippet to inspect actual child element names:

```python
import zipfile, xml.etree.ElementTree as ET
NS = "http://www.vd.ch/fiscalite/vaudtax"
with zipfile.ZipFile("file.vaudtax") as z:
    xml_name = next(n for n in z.namelist() if n.endswith(".xml"))
    root = ET.parse(z.open(xml_name)).getroot()
for el in root.findall(f"{{{NS}}}immeubles"):  # change section name as needed
    print({c.tag.split("}")[1]: c.text for c in el})
```

### Known differences between fiscal years

| Section | 2023 | 2024 | 2025 |
|---|---|---|---|
| Medical expenses | `fraisMedicaux` | `fraisMedicaux` | `fraisMedicauxDentaires` |
| Medical net amount field | `montantACharge` | `montantACharge` | `montantFrais` |
| Real estate | `immeubles` | `immeubles` | `biensImmobiliers` |
| Real estate fiscal value | `valeurFiscale` | `valeurFiscale` | `estimationFiscale` |

- `parse_vaudtax.py` handles both variants transparently.

## Official references

| Resource | URL | Notes |
|---|---|---|
| Instructions générales 2025 | [21001_2025.pdf](https://www.vd.ch/fileadmin/user_upload/organisation/dfin/aci/fichiers_pdf/21001_2025.pdf) | Main guide — pp. 59–68 for tax computation; URL is year-specific |
| ICC barème revenu 2025 | [barème_revenu_2025.pdf](https://www.vd.ch/fileadmin/user_upload/organisation/dfin/aci/fichiers_pdf/barème_revenu_2025.pdf) | Full income tax table at CHF 100 intervals |
| ICC barème fortune 2025 | [barème_fortune_2025.pdf](https://www.vd.ch/fileadmin/user_upload/organisation/dfin/aci/fichiers_pdf/barème_fortune_2025.pdf) | Full wealth tax table at CHF 1'000 intervals |
| IFD barème 2025 (form 58c) | [Bareme_IFD_58c-2025.pdf](https://www.vd.ch/fileadmin/user_upload/organisation/dfin/aci/fichiers_pdf/Bareme_IFD_58c-2025.pdf) | Single + married tables |
| Communal coefficients | [Arrêtés d'imposition](https://www.vd.ch/etat-droit-finances/communes/finances-communales/arretes-dimposition-et-tableaux-des-impots-communaux) | Current year XLS for all communes |

Limits and barème tables are indexed annually — verify the year matches the declaration's `fiscalPeriod`. Update PDF URLs by replacing the year suffix (e.g. `21001_2024.pdf` for fiscal year 2024).

## Reporting unhandled content

The skill may encounter VaudTax files from fiscal years or configurations it was not designed for — new XML sections, renamed fields, or unexpected data layouts. When this happens, always tell the user clearly and suggest opening a GitHub issue.

**Triggers — report an issue when:**

- `parse_vaudtax.py` output includes a **"Sections non reconnues"** block listing unknown section names.
- A section listed as "not yet parsed" in the Key XML sections table above (e.g. `autresRevenusExoneresImposesSource`, `revenuImposeAutreEtat`, `representative`, `prestationsEnCapital`) **contains data** (i.e. `isInitialized` is not `false` and relevant child elements are non-empty) — meaning the user's declaration has content the skill can't read.
- An `export_json.py` JSON field has an unexpected structure or a key section is `null` when it shouldn't be.
- A script raises an exception or produces clearly wrong output (e.g. zero assets when the XML has populated `etatTitres` entries).

**What to say to the user:**

> This declaration contains content that the vaudtax skill doesn't handle yet: **[describe what's missing or broken]**. The analysis above may be incomplete.
>
> If you'd like this to be supported, please open an issue at:
> **https://github.com/fredj/ai-stuff/issues**
>
> Include: the fiscal year (`fiscalPeriod`), the unknown section name(s) or field(s), and a brief description of what data they contain (no personal data needed).

Do **not** silently skip unhandled content — always surface the gap to the user.

## Anti-hallucination rules

These rules take precedence over everything else in this skill. Tax data is sensitive — being wrong is worse than being incomplete.

**Rule 1 — Every value must have a source.**
Every number or fact stated about a declaration must trace back to one of:
- output from a bundled script (`parse_vaudtax.py`, `export_json.py`, `compute_code800.py`, `calculate_taxes.py`), or
- a direct XML field read shown in a code block.

If neither applies, say "not found in the file" — never supply a value from general knowledge or inference.

**Rule 2 — Never compute taxes without running the scripts.**
Do not estimate ICC/IFD/fortune tax from training-data knowledge of Swiss tax formulas, barème tables, or commune coefficients. Always run `compute_code800.py` + `calculate_taxes.py`. The only acceptable exception is explaining the method conceptually when the user asks "how does this work?" — but never produce a figure that way.

**Rule 3 — `None` / absent ≠ zero ≠ "not applicable".**
A field missing from script output or reading as `None` from the XML may mean any of: not declared, genuinely zero, section not initialized, or **not yet parsed by the skill**. These are different. Report it as absent: "no value found for X" or "the script did not extract Y." Never silently substitute zero or omit the gap.

**Rule 4 — Check `fiscalPeriod` before applying any year-specific rule.**
Deduction caps, barème tables, and form field names all change by year. Read `fiscalPeriod` from the file first. Never apply 2025 limits to a 2023 or 2024 declaration without explicitly stating the assumption and flagging it as unverified.

**Rule 5 — Never describe what an unhandled section "probably" contains.**
If a section is not parsed by the skill (marked "not yet parsed" in the Key XML sections table), do not infer its contents from its name, label, or general Swiss tax knowledge. Say "this section exists in the file but is not yet handled by the skill" and follow the Reporting unhandled content procedure.

**Rule 6 — Never fabricate totals.**
Do not add up partial extracted values to produce a "total income" or "total deductions" figure unless the script explicitly outputs that total. Partial sums look authoritative and hide gaps.

**Rule 7 — Never guess XML field names.**
If you need to read a field not covered by the bundled scripts, use the discovery snippet from the "Field name discovery" section to inspect actual element names. Do not invent plausible-sounding names like `montantTotal` or `revenuBrut` — they may not exist or may mean something different.

**When in doubt:** say what you found, say what you couldn't find, and let the user decide. "The file has a `prestationsEnCapital` section but the skill can't read it yet — see https://github.com/fredj/ai-stuff/issues to request support" is always a correct answer.

## Guardrails

- **Estimates vs official figures.** `compute_code800.py` output is an estimate. When a `lastGesdemReference` or an official bordereau is available, those figures take precedence. Never present script output as the authoritative tax due.

- **Barème limits are year-specific — always use `fiscalPeriod`.** The limits in DEDUCTIONS.md (pilier 3a CHF 7'258, assurances CHF 9'900, etc.) are 2025 values. For declarations with a different `fiscalPeriod`, the applicable limits differ. Don't apply current-year limits to another fiscal year without flagging the assumption.

- **Don't cross-apply commune rates.** Tax coefficients are commune-specific. If the commune in `identification` differs from the one passed to `calculate_taxes.py`, flag the mismatch. Yvonand ≠ Yverdon ≠ Lausanne.

- **Réforme valeur locative applies from 2029.** For any analysis projecting future tax liability (2029+): valeur locative is suppressed, mortgage interest becomes non-deductible (except primo-acquéreurs Art. 33a LIFD), and code 660 (logement) disappears for IFD. Don't apply pre-2029 deduction rules to post-2028 projections.

- **Network exposure is limited to aggregate figures only.** The only network call in the entire skill is `calculate_taxes.py` → `https://www.vd.ch/...`. It sends three integers (`revenu_icc`, `fortune_icc`, `revenu_ifd`), the normalized commune name, and marital status — no NAVS13, IBAN, name, address, employer name, or salary breakdown. All other scripts are fully local and make no network calls.
