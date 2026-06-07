import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure standard output uses UTF-8 to prevent charmap errors on Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add the backend directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from app.services.llm import llm_service

async def test_questions():
    questions = [
        "What products in my store have the lowest gross margin?",
        "How should I manage dead stock?",
        "Explain margin erosion to a small business owner.",
        "What is the capital of France?" # Off-topic to test guardrail
    ]
    
    print("\n--- RetailMind AI Advisor (Groq) Test ---\n")
    
    for q in questions:
        print(f"Question: {q}")
        print("Thinking...")
        answer = await llm_service.ask_advisor(q)
        print(f"Answer: {answer}\n")
        print("-" * 30 + "\n")

if __name__ == "__main__":
    asyncio.run(test_questions())
