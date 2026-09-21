# Questions to Ask

`detect_candidate_signals` in `optimize.py` only covers levers whose eligibility
evidence can live in the XML (618, 610). Garde (670), dons (720), and
rachat LPP (320) carry no such evidence — children, donations, and LPP
buy-back capacity are not data the `.vaudtax` file contains. For these,
silence is wrong: after running `optimize.py`, ask the user directly instead
of omitting them.

For every catalog lever in [`levers.md`](levers.md) that received **neither**
an auto-detected value **nor** a "Signals found" line, ask a closed
eligibility question citing its cap before finalizing the report:

- **CODE 670 (garde):** children under 14 with documented childcare costs,
  incurred because the parent(s) work/train/cannot work? Cap: ICC 15'200 /
  IFD 25'800 per child.
- **CODE 720 (dons):** any charitable donations this year? Cap: 20% of code
  700 (ICC) / 20% of revenu intermédiaire I (IFD), min CHF 100 total.
- **CODE 320 (rachat):** an LPP certificate showing rachat/buy-back capacity?
  Never estimate this — it must come from the certificate.
- **CODE 540 (entretien):** if real estate is declared, is it a **built**
  property (not raw land) that you occupy or rent out? If so: building age,
  and either documented maintenance costs or willingness to use the flat-rate
  option (ICC 10–30% of valeur locative / revenu net immeuble by age and use;
  IFD 10%/20% by a 10-year age threshold — see `deductions.md` CODE 540).
  This one has **no file signal at all** — `parse_vaudtax.py` doesn't extract
  building age or maintenance costs yet, so always ask when real estate is
  present, don't wait for a signal that will never fire.

`optimize.py` auto-detects one more gap-to-cap signal, on **CODE 300
(assurances)** — declared premiums below the ICC cap, computed the same way
as the pilier 3a gap. Unlike 3a, there's no top-up: the gap is only a real
saving if the taxpayer already holds an undeclared, deductible premium
(accident, life/death, health for a dependent). When this signal fires, ask:
*"You have CHF X of headroom below the insurance cap — any other deductible
premium not yet declared?"*

Also ask for any of 618 / 610 that had **no** signal fire, unless the
signal check itself makes the code structurally inapplicable (no real estate
means 610 can't apply).

A "yes" with a number becomes a `--lever` string and gets rerun through
`calculate_taxes.py`. A "no" or "unsure" goes into **Couldn't assess** —
never dropped silently.
