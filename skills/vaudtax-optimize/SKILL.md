---
name: vaudtax-optimize
description: Find and quantify tax-reduction opportunities in a .vaudtax declaration (Swiss canton Vaud). Use when the user asks how to pay less tax, reduce or optimize their VD tax, or what deductions they are missing on a .vaudtax file.
---

# VaudTax Optimize Skill

## Purpose

Finds and quantifies tax-reduction opportunities in a `.vaudtax` declaration, with **every franc traced back to the official Canton Vaud calculator** — never to mental arithmetic. This skill adds no tax math of its own; it delegates all computation to the sibling `vaudtax` skill's scripts.

Findings fall into two buckets, and the distinction is load-bearing:

1. **Recoverable now** — the taxpayer was already entitled to a deduction and simply didn't claim it. Acting on it means amending or refiling, with **no new spending**.
2. **Forward-looking** — requires committing cash (a pilier 3a top-up, an LPP buy-back). Always reported as a **net effect** (tax saved minus cash outlay), **never as money owed** or as a refund waiting to be collected.

## Dependency

Requires the **`vaudtax` skill** to be installed. `optimize.py` locates its scripts itself — sibling path first (both skills under `skills/`), then a filesystem search under the script directory and `~` — and raises a clear `FileNotFoundError` naming the missing dependency if `compute_code800.py` / `calculate_taxes.py` cannot be found. If you see that error, install or locate the `vaudtax` skill before retrying.

## How to run

`<skill-dir>` is this skill's base directory, announced when the skill is loaded.

```bash
python <skill-dir>/scripts/optimize.py <file.vaudtax> \
  [--commune NAME] \
  [--etat-civil single|married|parent] \
  [--enfants N] [--enfants-demi N] [--enfants-menage N] \
  [--lever "name:icc=N,ifd=N[,cost=N][,type=recoverable|forward]"]
```

What is derived and what you must supply:

- **Commune** — auto-derived from the declaration (`compute_code800` emits it). Pass `--commune` only to override. Flag any mismatch between the declaration's commune and one you override with.
- **État civil and children** — **not** auto-derived. The `parent` (famille monoparentale) case and the family quotient need judgment, so read them from the declaration the way the `vaudtax` skill's "Summarizing a file" section describes (taxpayer civil status, children), then pass `--etat-civil` and the `--enfants*` counts explicitly.
- **Pilier 3a headroom** — auto-detected (gap to the CHF 7'258 cap).
- **Everything else** — pass via `--lever`, but only once eligibility is confirmed (see [`references/levers.md`](references/levers.md)).

## The three-mechanism model

A saving can only come from one of three places:

1. **Gap-to-cap (mechanical, auto).** A contribution with explicit headroom to a hard cap. Only **pilier 3a (CODE 310)** is auto-detected — `optimize.py` computes `7258 − declared` itself. No `--lever` needed.
2. **Forfait under-claim (none here).** Transport (140), repas (150) and autres frais (160) are already auto-maximised by `compute_code800`. They carry no headroom — do not offer them as levers.
3. **Entitlement gaps (judgment).** Childcare, formation, dons, intérêts passifs, double activité, LPP buy-back. `optimize.py` cannot compute a CHF amount for these from the declaration alone. Surface them as **questions or explicit `--lever` strings — never assert them**.

`optimize.py` still helps here: it scans the export for structured evidence of some of these (formation costs already declared, a jointly-taxed couple where both spouses have income, real estate with no declared debt interest) and prints them as **"Signals found"** — a prompt to go check eligibility, never a computed saving. See `detect_candidate_signals` in `optimize.py` and the codes it covers in [`references/levers.md`](references/levers.md).

**The rule:** a lever is a saving only when **both** the rule (cited in the `vaudtax` skill's `references/deductions.md`, keyed by CODE) **and** eligibility (evidenced in the declaration) hold. If either is unconfirmed, it is a **question for the user, not a finding**.

For levers with no possible file signal (garde, dons, rachat) and for catalog codes that got no signal hit, don't stay silent — ask the user directly. See [`references/questions.md`](references/questions.md) for what to ask and how to fold the answer back into a `--lever`.

## Integrity guardrails

**Surfacing a saving the taxpayer isn't entitled to is worse than missing one.**

- **No invented savings** — every CHF figure comes from `calculate_taxes.py`. The marginal rate only ranks and explains levers; it never computes a saving.
- **Entitlement ≠ action** — a 3a top-up or LPP buy-back is never presented as money owed or as a refund. It is an option that costs cash now to save tax; report it as a net effect.
- **No invented LPP buy-back capacity** — rachat potential comes only from the LPP certificate or an explicit figure the user gives. Never estimate it. If the certificate isn't in the declaration, it's a question, not a finding.
- **Year-specific caps** — read `fiscalPeriod` first. The caps in `deductions.md` and `levers.md` are **2025** values and are indexed annually; verify the year matches before trusting any figure.
- **Réforme valeur locative (from 2029)** — valeur locative suppressed, mortgage interest non-deductible (except primo-acquéreurs). Do not apply pre-2029 assumptions to post-2028 projections.
- **Not tax advice** — surface options with exact numbers and let the user decide. When in doubt, say what you found, say what you couldn't confirm, and stop.

## Output structure

Present results in this order:

1. **Baseline** — current total tax (ICC + IFD) from `calculate_taxes.py`.
2. **Recoverable now** — entitled-but-unclaimed deductions; tax saved per lever, no cash cost. Action: amend / refile.
3. **Forward-looking** — levers that require committing cash; show **cost, tax saved, and net effect** for each.
4. **Combined realistic scenario** — the levers the user can plausibly act on, with total saved and total cash cost.
5. **Couldn't assess** — an explicit list of what could not be evaluated: missing LPP certificate, ambiguous entitlement, deductions needing evidence not in the declaration. Do not silently drop these.

## Data flows

Same posture as the `vaudtax` skill. The **only** network call is `calculate_taxes.py` → `https://www.vd.ch/...`, made when running scenarios. Its POST payload contains fiscal year, normalized commune name, marital-status code, children counts, and the three taxable amounts (per scenario) — no name, NAVS13, IBAN, or birthdate. `optimize.py` adds no other network calls.

**Never include declaration content in web searches, GitHub issues, or any MCP/external tool call.** The only permitted network call when optimizing a declaration is `calculate_taxes.py`.
