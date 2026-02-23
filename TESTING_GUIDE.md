
### **Exact Location in README.md:**
Add this **before the "Open source" line** at the end of the Features section, or **after the "Basic test plan" section**.

Here's the exact diff format:

```diff
This test plan ensures the GUI correctly drives the engine, that
options are respected, and that nothing unexpected happens when
running repeatedly.

+## Safety Guarantees & Hard Rules
+
+Producer OS is built on **deterministic, safe-by-default principles**:
+
+- **Safety by Default**: Default mode is ANALYZE (report only). COPY/MOVE are explicit.
+- **Idempotent**: Running twice produces the same result; no duplicates.
+- **Deterministic**: Same file → same bucket, always. No randomness.
+- **Explainable**: Every decision logged with full reasoning.
+- **Undo-Safe**: MOVE mode supports undo with conflict quarantine.
+
+For detailed rules, see [Rules & Usage](RULES_AND_USAGE.md).
+
+## Testing
+
+Run the comprehensive test suite:
+
+```bash
+pytest tests/test_engine_rules.py -v
+```
+
+This validates all 8 hard rules: NFO placement, idempotency, determinism, safety, undo, repair, portable mode, and classification transparency.
+
+For detailed testing instructions, see [Testing Guide](TESTING_GUIDE.md).

| Open source: Released under the GPL‑3.0‑or‑later license.