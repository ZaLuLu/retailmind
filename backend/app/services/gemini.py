import google.generativeai as genai
from ..core.config import settings
import json
import logging
from typing import Optional
import asyncio

try:
    import PIL.Image
    import io as _io
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

gemini_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)


class GeminiService:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is not set. Gemini features will be unavailable.")
            self.model = None
            self.chat_model = None
            return

        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config={
                "response_mime_type": "application/json",
            },
        )
        self.chat_model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL
        )

    @gemini_retry
    async def ask_advisor(self, question: str, context: Optional[str] = None) -> str:
        """
        Ask a retail business intelligence question to the RetailMind advisor.
        Returns the advisor's answer as a string.
        
        Security: question is pre-validated and sanitized by the API layer before
        reaching this method. Context is system-generated (not user-controlled).
        """
        if self.chat_model is None:
            return self._fallback_answer(question)

        # Truncate context to prevent token exhaustion attacks
        safe_context = (context or "No specific context provided.")[:2000]
        # Escape any curly braces in context to prevent f-string injection
        safe_context = safe_context.replace("{", "{{").replace("}", "}}")

        system_instruction = (
            "You are 'RetailMind Advisor', a retail business intelligence assistant. "
            "You ONLY answer questions about retail operations: sales, margins, inventory, "
            "dead stock, demand signals, pricing, and the RetailMind application. "
            "For ANY other topic, respond exactly: "
            "'I am RetailMind's Business Intelligence Advisor. I can only assist with "
            "retail store sales, margins, dead stock, demand spikes, and inventory trends.' "
            "Be concise (max 100 words), professional, and provide one actionable tip."
        )

        user_message = f"Store Dashboard Data: {safe_context}\n\nQuestion: {question}"

        try:
            response = await asyncio.wait_for(
                self.chat_model.generate_content_async([system_instruction, user_message]),
                timeout=settings.GEMINI_TIMEOUT_SECONDS
            )
            return response.text
        except Exception as e:
            logger.error("Gemini advisor failed: %s", type(e).__name__)
            raise

    async def stream_advisor(self, question: str, context: Optional[str] = None):
        """
        Asynchronously stream answers from the RetailMind advisor.
        """
        if self.chat_model is None:
            reply = self._fallback_answer(question)
            words = reply.split(" ")
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i:i+3]) + " "
                yield chunk
                await asyncio.sleep(0.08)
            return

        safe_context = (context or "No specific context provided.")[:2000]
        safe_context = safe_context.replace("{", "{{").replace("}", "}}")

        system_instruction = (
            "You are 'RetailMind Advisor', a retail business intelligence assistant. "
            "You ONLY answer questions about retail operations: sales, margins, inventory, "
            "dead stock, demand signals, pricing, and the RetailMind application. "
            "For ANY other topic, respond exactly: "
            "'I am RetailMind's Business Intelligence Advisor. I can only assist with "
            "retail store sales, margins, dead stock, demand spikes, and inventory trends.' "
            "Be concise (max 100 words), professional, and provide one actionable tip."
        )

        user_message = f"Store Dashboard Data: {safe_context}\n\nQuestion: {question}"

        try:
            response = await asyncio.wait_for(
                self.chat_model.generate_content_async(
                    [system_instruction, user_message], stream=True
                ),
                timeout=settings.GEMINI_TIMEOUT_SECONDS
            )
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error("Gemini advisor streaming failed: %s", type(e).__name__)
            raise

    def _fallback_answer(self, question: str) -> str:
        """
        Rule-based fallback when Gemini API key is not configured.
        Returns generic but useful retail intelligence responses.
        """
        q_lower = question.lower()
        if any(k in q_lower for k in ("margin", "cogs", "drag", "profit")):
            return (
                "Your overall gross profit margin performance depends on your COGS relative to revenue. "
                "Review your Apparel and high-cost categories first — these typically drive margin drag. "
                "💡 Tip: Negotiate vendor bulk agreements or adjust retail pricing to improve margin by 5-10%."
            )
        elif any(k in q_lower for k in ("reorder", "stock", "inventory", "product")):
            return (
                "Inventory signals show demand variance across product categories. "
                "Focus reorder budgets on high-velocity items and run clearance on dead stock. "
                "💡 Tip: Use the Forecast tab to identify products needing reorder before the next cycle."
            )
        elif any(k in q_lower for k in ("drop", "trend", "week", "spike")):
            return (
                "Sales trend anomalies can indicate channel outages, seasonal patterns, or data gaps. "
                "Check your upload schedule and B2B channel synchronisation. "
                "💡 Tip: Set up weekly review checkpoints to catch trend drops within 4 hours."
            )
        else:
            return (
                "I can help you analyse your store's sales, margins, inventory, and demand signals. "
                "Connect a Gemini API key in your environment settings to unlock AI-powered insights. "
                "💡 Tip: Upload your sales data via CSV to get started with demand forecasting."
            )


# Singleton instance
gemini_service = GeminiService()
