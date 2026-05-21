import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from app.services.gemini import gemini_service

async def test_valid_questions():
    questions = [
        "What are some strategies to minimize dead stock in my retail store?",
        "How do I analyze my store's gross margins?",
        "How can I detect demand spikes early?"
    ]
    
    print("\n--- RetailMind AI Advisor VALID Questions Test ---\n")
    
    for q in questions:
        print(f"Question: {q}")
        print("Thinking...")
        answer = await gemini_service.ask_advisor(q, context="{'total_revenue': 120000, 'total_cogs': 80000, 'dead_stock_alerts': [{'product': 'A', 'days': 90}]}")
        print(f"Answer: {answer}\n")
        print("-" * 30 + "\n")

if __name__ == "__main__":
    asyncio.run(test_valid_questions())
