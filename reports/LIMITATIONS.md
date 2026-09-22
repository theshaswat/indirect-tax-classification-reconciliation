# Limitations

- **No real transaction or vendor data.** Every invoice line is synthetic and labelled as such. The
  engine's logic is validated against a known, deterministic error-injection rate — not against a
  real tax-ops exception queue, because no such data is available to this project.
- **9 of 20 rules are `stable_fact_verify_before_filing`.** These are well-established rates (e.g.
  Ireland's 23% VAT, India's TDS section rates) not independently re-confirmed against a live
  primary source in this session. The engine surfaces this distinction in its own output
  (`OK — VERIFY RATE`) rather than treating all rates as equally certain.
- **US rates are state-level base only.** Local county/city add-ons (e.g. Chicago's combined ~10.5%)
  are explicitly out of scope and not modelled.
- **India TDS/withholding is mid-transition.** The Income-tax Act 2025 consolidates TDS provisions
  under Section 393 from 1 April 2026, replacing the old section numbers used here for readability.
  Re-verify section references before any real filing use.
- **No RCSA, SAP, or tax-engine (Vertex/OneSource) exposure claimed anywhere.** This project
  demonstrates classification logic, not familiarity with any specific enterprise tax software.
- **No number from this project should reach a resume until this file has been re-read and is still
  accurate.**
