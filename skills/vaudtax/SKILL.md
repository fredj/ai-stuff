---
name: vaudtax
description: Working with .vaudtax files (Swiss canton Vaud tax declarations). Use when the user mentions a .vaudtax file, wants to read/summarize/convert a VD tax declaration, or inspect tax data (income, deductions, assets, attached documents).
---

# VaudTax Skill

## File format

A `.vaudtax` file is a **ZIP archive** containing:

- **One XML file** (named `<filename>.xml`) — the entire tax declaration as structured XML under the namespace `http://www.vd.ch/fiscalite/vaudtax`, root element `<vaudTaxData>`.
  - **Namespace:** `http://www.vd.ch/fiscalite/vaudtax` (proprietary format, no public XSD available)
  - **Structure:** 32+ main sections organizing all tax declaration data
- **Zero or more `doc*` files** — attached supporting documents: PDF, JPEG, or PNG. The format is declared in the XML's `<mimeType>` field.

## Bundled scripts

All scripts live in `${CLAUDE_SKILL_DIR}/scripts/` and use only Python standard library — no installs needed.

| Script | Purpose |
|---|---|
| `parse_vaudtax.py <file.vaudtax>` | Parse and print a human-readable summary to stdout |
| `export_json.py <file.vaudtax> [out.json]` | Export clean JSON (omits UI/navigation state) |
| `compute_code800.py <file.vaudtax>` | Estimate revenu imposable ICC (code 800), IFD, and fortune — outputs values ready to pass to `calculate_taxes.py` |
| `calculate_taxes.py --periode YEAR --commune NAME --revenu-icc N --fortune-icc N --revenu-ifd N` | Query the official Canton Vaud tax calculator via HTTP POST and return authoritative results |

The JSON output conforms to **`${CLAUDE_SKILL_DIR}/vaudtax-export.schema.json`** (JSON Schema 2020-12).

```bash
cd "${CLAUDE_SKILL_DIR}/scripts"
python parse_vaudtax.py /path/to/file.vaudtax
python export_json.py  /path/to/file.vaudtax
```

## Key XML sections

### Metadata & Taxpayer Info
| Section | Description |
|---|---|
| `fiscalPeriod` | ✅ Tax year (e.g. `2025`) |
| `lastGesdemReference` | ✅ Gesdem submission reference |
| `identification` | ✅ Address, municipality, phone, email, IBAN |
| `taxpayerPersonalData1` | ✅ Name, birthdate, NAVS13, profession, marital status |
| `taxpayerPersonalData2` | ✅ Second taxpayer (joint filers only) |
| `representative` | Tax representative details (not yet parsed) |

### Income
| Section | Description |
|---|---|
| `activiteSalarieeRevenus` | ✅ Employed income: employer, net salary, pension contributions, dates, activity rate |
| `complementRentePension` | ✅ Pension/rente income: type, annual amount |
| `activitesIndependantes` | ✅ Self-employment income: activity name, net revenue |
| `autresRevenusExoneresImposesSource` | Other income (not yet parsed) |
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
| `interetsDettes` | ✅ Debt interest deductions (code 520) |
| `fraisFormation` | ✅ Training/education costs |
| `donationsAvancesHoiries` | ✅ Donations and inheritance advances |
| `successionHoirieDonation` | Inheritances flag (skipped when `isInitialized=false`) |

### Assets & Securities
| Section | Description |
|---|---|
| `etatTitres` | ✅ Bank accounts: IBAN, balance, yield |
| `relevesFiscauxBancaires` | ✅ Investment portfolios: fiscal value, gross income, IES |
| `numerairesList` | ✅ Cash and liquid assets |
| `objetsMobiliers` | ✅ Movable property / crypto |
| `biensImmobiliers` (2025) / `immeubles` (older) | ✅ Real estate: commune, parcelle, fiscal value, rental income |
| `autoMoto` | ✅ Vehicles |
| `fraisAdministrationTitres` | ✅ Management fees for securities (code 490) |

### Supporting Documents & Navigation
| Section | Description |
|---|---|
| `piecesJustificativesObligatoires` | Mandatory supporting document metadata |
| `piecesJustificativesFacultatives` | Optional supporting document metadata |
| `infosComplementairesIes` | Additional investment income (IES) information |
| `prestationsEnCapital` | Capital benefit payments (not yet parsed) |
| `guidedNav` / `userProfil` / `piecesJustificativesSubFormInitialized` | UI/navigation state — intentionally skipped |

## Summarizing a file

Run `parse_vaudtax.py` and present the output using this structure:

1. **Filing info** — fiscal year, reference, municipality
2. **Taxpayer(s)** — name, birthdate, civil status, profession; CTB2 if joint filer
3. **Income** — employed activity, pension/rentes, self-employment
4. **Deductions** — transport, meals, professional expenses, insurance/3rd pillar, rent, medical, debt interest, education
5. **Assets** — bank accounts, investment portfolios, cash, real estate, vehicles, movable objects
6. **Attached documents** — filename and size for each
7. **Cross-check results** — outcome of proactive PDF verification (see below)

Amounts are in CHF unless a different `devise` is specified.

**Only report what exists.** Do not mention sections that are empty, not initialized, or not applicable to this taxpayer. If `parse_vaudtax.py` reports no unknown sections, say nothing about sections at all.

**A summary is just a summary.** Do not run `compute_code800.py` or `calculate_taxes.py` unless the user explicitly asks for a tax estimate.

### Proactive cross-checks

Even for a basic summary, always cross-check attached documents against their XML values — discrepancies are high-value findings the user needs before filing. **Run all PDF reads in parallel** (spawn one sub-agent per document or issue all `open_attachment` + `read_pdf` calls in a single parallel batch).

**Pillar 3a attestations** (label contains "21 EDP", "cotisations", or "pilier 3a"):
1. Read each PDF with `read_pdf()` + `extract_form21_totals()` (or `extract_postfinance_3a()` for PostFinance) — see [`references/pillar-attestation.md`](references/pillar-attestation.md)
2. Sum per taxpayer; compare against `formesReconnuesPrevoyanceIndividuelleContribuable1` / `...Contribuable2`
3. Flag any discrepancy: **"⚠ Écart pilier 3a : attestations CHF X, déclaration CHF Y — vérifier avant envoi"**

**Salary certificates** (label contains "Certificat de salaire"):
1. Read the PDF and extract line 11 (salaire net) and line 10.1 (LPP) — see [`references/salary-certificate.md`](references/salary-certificate.md)
2. Compare against `salaireNet` and `cotisationOrdinaire` in the XML
3. Flag any mismatch beyond ±1 CHF rounding

Skip the cross-checks only if the user explicitly asks for a quick overview.

When verifying deductions, see [`references/deductions.md`](references/deductions.md) for official rules and caps.

## Full analysis — always include taux marginal

For any full analysis (running both `compute_code800.py` and `calculate_taxes.py`), **always also compute the taux marginal** with `--marginal-rate`:

```bash
python calculate_taxes.py \
  --periode YEAR --commune "Commune" \
  --revenu-icc N --fortune-icc N --revenu-ifd N \
  --marginal-rate
```

This makes two HTTP calls and returns the marginal rate for ICC, IFD, and the combined total. Include it in the output:

| | Taux marginal |
|---|---|
| ICC (cantonal + communal) | X.XX % |
| IFD (fédéral direct) | X.XX % |
| **Total** | **X.XX %** |

See [`references/tax-computation.md`](references/tax-computation.md) for ICC and IFD formulas.

## Reading attached PDFs

Use the bundled `${CLAUDE_SKILL_DIR}/scripts/pdf_utils.py`:

```python
from pdf_utils import read_pdf, extract_form21_totals, identify_taxpayer

text = read_pdf("/tmp/doc.pdf")               # text PDF or scanned — handled automatically
text = read_pdf("/tmp/doc.pdf", lang="deu")   # switch to German if needed
```

`read_pdf()` tries `pdfplumber` first; falls back to `pytesseract` OCR at 200 dpi. Use `lang="fra"` (default) for French, `"deu"` for German.

**Read multiple attachments in parallel** — spawn one sub-agent per document or issue all `open_attachment` + `read_pdf` calls concurrently. Wall-clock time scales with the slowest single document, not the total count.

For salary certificate field layout → [`references/salary-certificate.md`](references/salary-certificate.md)
For Form 21 EDP pillar attestation structure → [`references/pillar-attestation.md`](references/pillar-attestation.md)

## Extracting attached files

Always use the `open_attachment()` context manager from `parse_vaudtax.py` — it extracts to a temp file and deletes it on exit:

```python
from parse_vaudtax import open_attachment
from pdf_utils import read_pdf

with open_attachment("file.vaudtax", "doc17700000000000", suffix=".pdf") as path:
    text = read_pdf(path)
```

Use the `<key>` value (not the `<reference>` UUID) to match XML metadata to ZIP entries. Each `<documents>` element has: `<key>`, `<filename>`, `<mimeType>`, `<label>`, `<fileSize>`.

## VaudTax XML Schema

Proprietary format maintained by the Canton Vaud tax authority — no public XSD. Element names follow French naming conventions and may change across fiscal years.

### Known differences between fiscal years

| Section | 2023–2024 | 2025 |
|---|---|---|
| Medical expenses | `fraisMedicaux` | `fraisMedicauxDentaires` |
| Medical net amount | `montantACharge` | `montantFrais` |
| Real estate section | `immeubles` | `biensImmobiliers` |
| Real estate fiscal value | `valeurFiscale` | `estimationFiscale` |

`parse_vaudtax.py` handles both variants transparently.

If a parsed field returns `None` unexpectedly, inspect actual child element names:

```python
import zipfile, xml.etree.ElementTree as ET
NS = "http://www.vd.ch/fiscalite/vaudtax"
with zipfile.ZipFile("file.vaudtax") as z:
    xml_name = next(n for n in z.namelist() if n.endswith(".xml"))
    root = ET.parse(z.open(xml_name)).getroot()
for el in root.findall(f"{{{NS}}}sectionName"):
    print({c.tag.split("}")[1]: c.text for c in el})
```

## Official references

| Resource | URL | Notes |
|---|---|---|
| Instructions générales 2025 | [21001_2025.pdf](https://www.vd.ch/fileadmin/user_upload/organisation/dfin/aci/fichiers_pdf/21001_2025.pdf) | Main guide; URL is year-specific |
| ICC barème revenu 2025 | [barème_revenu_2025.pdf](https://www.vd.ch/fileadmin/user_upload/organisation/dfin/aci/fichiers_pdf/barème_revenu_2025.pdf) | Income tax table at CHF 100 intervals |
| ICC barème fortune 2025 | [barème_fortune_2025.pdf](https://www.vd.ch/fileadmin/user_upload/organisation/dfin/aci/fichiers_pdf/barème_fortune_2025.pdf) | Wealth tax table at CHF 1'000 intervals |
| IFD barème 2025 (form 58c) | [Bareme_IFD_58c-2025.pdf](https://www.vd.ch/fileadmin/user_upload/organisation/dfin/aci/fichiers_pdf/Bareme_IFD_58c-2025.pdf) | Single + married tables |
| Communal coefficients | [Arrêtés d'imposition](https://www.vd.ch/etat-droit-finances/communes/finances-communales/arretes-dimposition-et-tableaux-des-impots-communaux) | Current year XLS for all communes |

Update PDF URLs by replacing the year suffix (e.g. `21001_2024.pdf` for fiscal year 2024).

## Reporting unhandled content

When the file contains sections or fields the skill can't handle, tell the user and suggest opening a GitHub issue.

**Report when:**
- `parse_vaudtax.py` outputs a **"Sections non reconnues"** block
- A section marked "not yet parsed" above contains data (`isInitialized` is not `false` and child elements are non-empty)
- A script raises an exception or produces clearly wrong output

**Say:**
> This declaration contains content the vaudtax skill doesn't handle yet: **[describe what's missing]**. The analysis above may be incomplete.
>
> Please open an issue at **https://github.com/fredj/ai-stuff/issues** with: the fiscal year, the section name(s), and a brief description (no personal data needed).

Do **not** silently skip unhandled content.

## Guardrails

**Tax data is sensitive — being wrong is worse than being incomplete.**

**Sources** — Every number must trace back to script output or a direct XML field read. Never supply a value from general knowledge. If a field is absent, say so — absent ≠ zero ≠ "not applicable".

**No mental arithmetic** — Never compute ICC/IFD/fortune tax without running `compute_code800.py` + `calculate_taxes.py`. The only exception is explaining the method conceptually.

**Year-specific rules** — Always read `fiscalPeriod` before applying any deduction cap, barème table, or form field name. The limits in [`references/deductions.md`](references/deductions.md) are 2025 values and differ for other years.

**No guessing** — Never infer what an unhandled section contains, never fabricate totals from partial data, never guess XML field names (use the discovery snippet above).

**Estimates vs official figures** — `compute_code800.py` output is an estimate. When a `lastGesdemReference` or official bordereau is available, those figures take precedence.

**Commune rates** — Tax coefficients are commune-specific. Flag any mismatch between the commune in `identification` and the one passed to `calculate_taxes.py`.

**Réforme valeur locative (from 2029)** — Valeur locative suppressed, mortgage interest non-deductible (except primo-acquéreurs Art. 33a LIFD), code 660 disappears for IFD. Do not apply pre-2029 rules to post-2028 projections.

**Network** — The only network call is `calculate_taxes.py` → `https://www.vd.ch/...`. It sends three integers, the commune name, and marital status — no personal identifiers.

**When in doubt:** say what you found, say what you couldn't find, and let the user decide.
