import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the backend directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from app.services.gemini import gemini_service

async def test_questions():
    questions = [
        "How can I reduce my monthly grocery spending?",
        "Explain the 50/30/20 rule concisely.",
        "Is spending $100 on sneakers a good investment?"
    ]
    
    print("\n--- DocuMind AI Advisor Test ---\n")
    
    for q in questions:
        print(f"Question: {q}")
        print("Thinking...")
        answer = await gemini_service.ask_advisor(q)
        print(f"Answer: {answer}\n")
        print("-" * 30 + "\n")

if __name__ == "__main__":
    asyncio.run(test_questions())
