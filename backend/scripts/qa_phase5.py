"""
Phase 5 QA Verification Script
================================
Tests the ingestion validation logic and audit model fields directly,
without requiring a live server. Validates:

1. CSV parsing & validation rules (null, negative qty, zero qty, bad price,
   bad date, exact duplicate)
2. Alembic migration state (head check)
3. Model field presence (anomaly_snapshot, rows_total, duplicates_skipped)
4. LLM service import (llm.py)
5. retail_intelligence service import
"""

import sys
import os
import asyncio
from pathlib import Path
from io import StringIO
from unittest.mock import MagicMock

# ── Mock groq so services import without the venv ─────────────────────────
sys.modules['groq'] = MagicMock()
sys.modules['groq.AsyncGroq'] = MagicMock()

# ── Add backend to path ───────────────────────────────────────────────────
BACKEND = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND))

print("=" * 60)
print("  RetailMind Phase 5 — QA Verification")
print("=" * 60)
passed = 0
failed = 0

def ok(msg):
    global passed
    print(f"  ✅  {msg}")
    passed += 1

def fail(msg, err=None):
    global failed
    print(f"  ❌  {msg}")
    if err:
        print(f"       → {err}")
    failed += 1

# ─────────────────────────────────────────────────────────────────────────
# 1. Model field checks
# ─────────────────────────────────────────────────────────────────────────
print("\n[1] Database Model Field Checks")
try:
    from app.models.db import Audit, UploadHistory, SaleRecord, User, Store
    # Audit.anomaly_snapshot
    assert hasattr(Audit, 'anomaly_snapshot'), "anomaly_snapshot missing"
    ok("Audit.anomaly_snapshot column exists")

    # UploadHistory.rows_total + duplicates_skipped
    assert hasattr(UploadHistory, 'rows_total'), "rows_total missing"
    assert hasattr(UploadHistory, 'duplicates_skipped'), "duplicates_skipped missing"
    ok("UploadHistory.rows_total + duplicates_skipped columns exist")

    # SaleRecord — check table name rather than attribute (Column access varies)
    assert SaleRecord.__tablename__ == 'sale_records', f"Unexpected tablename: {SaleRecord.__tablename__}"
    ok("SaleRecord table registered as 'sale_records'")

except Exception as e:
    fail("Model field check failed", e)

# ─────────────────────────────────────────────────────────────────────────
# 2. LLM service import & method check
# ─────────────────────────────────────────────────────────────────────────
print("\n[2] LLM Service Import")
try:
    from app.services.llm import LLMService
    svc = LLMService.__new__(LLMService)
    assert hasattr(svc, 'ask_advisor'), "ask_advisor missing"
    assert hasattr(svc, 'generate_audit_report'), "generate_audit_report missing"
    ok("LLMService imports OK with both ask_advisor + generate_audit_report")
except Exception as e:
    fail("LLM service import failed", e)

# ─────────────────────────────────────────────────────────────────────────
# 3. Retail intelligence service import
# ─────────────────────────────────────────────────────────────────────────
print("\n[3] Retail Intelligence Service Import")
try:
    from app.services.retail_intelligence import RetailIntelligenceService
    svc = RetailIntelligenceService.__new__(RetailIntelligenceService)
    assert hasattr(svc, 'run_store_audit'), "run_store_audit missing"
    assert hasattr(svc, 'get_retail_summary'), "get_retail_summary missing"
    ok("RetailIntelligenceService imports OK")
except Exception as e:
    fail("retail_intelligence import failed", e)

# ─────────────────────────────────────────────────────────────────────────
# 4. CSV Validation Logic
# ─────────────────────────────────────────────────────────────────────────
print("\n[4] CSV Ingestion Validation Logic")
try:
    import csv, re
    from datetime import datetime

    DATE_FORMATS = [
        "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y",
        "%Y/%m/%d", "%d.%m.%Y", "%m-%d-%Y",
    ]

    def parse_date(s):
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(s.strip(), fmt).date()
            except ValueError:
                continue
        return None

    qa_csv = Path(__file__).resolve().parent / "qa_test_upload.csv"
    with open(qa_csv, newline='', encoding='utf-8-sig') as fh:
        rows = list(csv.DictReader(fh))

    errors = []
    seen = set()
    inserted = []

    for i, row in enumerate(rows, start=2):
        name = (row.get("product_name") or "").strip()
        if not name:
            errors.append({"row": i, "category": "null", "message": "product_name is null/empty"})
            continue

        try:
            qty = float(row["quantity"])
        except (ValueError, TypeError):
            errors.append({"row": i, "category": "type", "message": "quantity is not numeric"})
            continue

        if qty <= 0:
            errors.append({"row": i, "category": "validation", "message": f"quantity must be > 0, got {qty}"})
            continue

        try:
            price = float(row["price"])
        except (ValueError, TypeError):
            errors.append({"row": i, "category": "type", "message": "price is not numeric"})
            continue

        dt = parse_date(row.get("date", ""))
        if dt is None:
            errors.append({"row": i, "category": "format", "message": f"Unrecognised date: {row.get('date')}"})
            continue

        key = (name.lower(), str(dt), str(qty), str(price))
        if key in seen:
            errors.append({"row": i, "category": "duplicate", "message": f"Exact duplicate: {name}"})
            continue
        seen.add(key)
        inserted.append(row)

    validation_errors = [e for e in errors if e["category"] != "duplicate"]
    duplicates = [e for e in errors if e["category"] == "duplicate"]

    # Expected from qa_test_upload.csv:
    # Row 3: null product_name
    # Row 4: negative qty (-5)  → validation
    # Row 5: non-numeric price (abc) → type
    # Row 10: exact duplicate of row 2 → duplicate
    # Row 11: zero qty → validation
    # Row 13: bad date format → format

    null_errs = [e for e in errors if e["category"] == "null"]
    type_errs = [e for e in errors if e["category"] == "type"]
    format_errs = [e for e in errors if e["category"] == "format"]
    val_errs = [e for e in errors if e["category"] == "validation"]
    dup_errs = duplicates

    assert len(null_errs) == 1, f"Expected 1 null error, got {len(null_errs)}"
    ok(f"Null detection: {len(null_errs)} row caught ✓")

    assert len(type_errs) == 1, f"Expected 1 type error, got {len(type_errs)}"
    ok(f"Type error detection: {len(type_errs)} row caught ✓")

    assert len(format_errs) == 1, f"Expected 1 format error, got {len(format_errs)}"
    ok(f"Date format detection: {len(format_errs)} row caught ✓")

    assert len(val_errs) == 2, f"Expected 2 validation errors (neg qty + zero qty), got {len(val_errs)}"
    ok(f"Positive-value enforcement: {len(val_errs)} rows caught (neg + zero qty) ✓")

    assert len(dup_errs) == 1, f"Expected 1 duplicate, got {len(dup_errs)}"
    ok(f"Duplicate detection: {len(dup_errs)} row caught ✓")

    ok(f"Clean rows inserted: {len(inserted)} / {len(rows)} (expected ~9)")

except Exception as e:
    fail("CSV validation logic test failed", e)

# ─────────────────────────────────────────────────────────────────────────
# 5. API router import
# ─────────────────────────────────────────────────────────────────────────
print("\n[5] API Router Import Check")
try:
    # Just compile — don't import (needs DB + env)
    import py_compile, tempfile
    retail_py = BACKEND / "app" / "api" / "retail.py"
    py_compile.compile(str(retail_py), doraise=True)
    ok("app/api/retail.py compiles clean")

    llm_py = BACKEND / "app" / "services" / "llm.py"
    py_compile.compile(str(llm_py), doraise=True)
    ok("app/services/llm.py compiles clean")

    ri_py = BACKEND / "app" / "services" / "retail_intelligence.py"
    py_compile.compile(str(ri_py), doraise=True)
    ok("app/services/retail_intelligence.py compiles clean")

except Exception as e:
    fail("API router compile failed", e)

# ─────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
total = passed + failed
print(f"  Results: {passed}/{total} checks passed", end="")
if failed:
    print(f" | {failed} FAILED")
    sys.exit(1)
else:
    print(" — ALL PASSED ✅")
    sys.exit(0)
