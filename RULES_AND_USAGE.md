# Producer OS – Rules, Usage & Safety Guarantees

## HARD RULES (Non-Negotiable Guarantees)

### Rule 1: Safety by Default
**ANALYZE is the default mode.** It reports only, changing nothing.

```bash
# Safe: reports classification, zero changes
python -m producer_os.cli analyze /inbox /hub

# Read the report
cat hub/logs/<run_id>/run_report.json
