import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure standard output uses UTF-8 to prevent charmap errors on Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from app.core.db import engine, async_session_factory
from app.services.retail_intelligence import retail_intelligence_service
from sqlalchemy import select
from app.models.db import User

async def main():
    async with async_session_factory() as db:
        # Find the seed user
        stmt = select(User).where(User.email == "demo@retailmind.com")
        res = await db.execute(stmt)
        user = res.scalars().first()
        if not user:
            print("User demo@retailmind.com not found!")
            return
        
        print(f"Running audit calculations for user: {user.email} (ID: {user.id})")
        audit = await retail_intelligence_service.run_store_audit(db, user.id)
        
        print(f"\nAudit completed! ID: {audit.id}")
        print(f"Audit Date: {audit.audit_date}")
        print(f"Total Products Checked: {audit.total_products_checked}")
        print(f"Anomalies Detected: {audit.anomalies_detected}")
        print("\nAI Commentary / Executive Briefing:\n")
        print(audit.ai_audit_summary)

if __name__ == "__main__":
    asyncio.run(main())
