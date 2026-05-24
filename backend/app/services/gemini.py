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
    async def extract_transaction(self, file_content: bytes, mime_type: str):
        """
        Extract transaction data from a document using Gemini Flash.
        Returns an ExtractionResult dict, or None on failure.
        """
        if self.model is None:
            logger.warning("Gemini model not initialised — skipping extraction.")
            return None

        # Lazy import to avoid crash if schemas change
        try:
            from ..schemas.transaction import ExtractionResult
        except ImportError:
            logger.error("ExtractionResult schema not found; returning raw dict.")
            ExtractionResult = None

        prompt = """
        You are an Indian financial intelligence expert. Analyze the attached document (receipt/invoice from India) and extract the following in JSON format:
        - vendor_name: The name of the merchant/store.
        - amount: The total amount paid in INR (numeric).
        - category: One of [Food, Transport, Utilities, Entertainment, Health, Shopping, Other].
        - transaction_date: The date in YYYY-MM-DD format.
        - confidence: Your confidence score from 0.0 to 1.0.
        - notes: A brief summary. Mention if GST was detected.

        IMPORTANT: If the document uses INR or ₹, extract the numerical value only. If it's not a receipt, explain in 'notes'.
        """

        try:
            if "image" in mime_type and _PIL_AVAILABLE:
                import io
                img = PIL.Image.open(io.BytesIO(file_content))
                response = await self.model.generate_content_async([prompt, img])
            else:
                response = await self.model.generate_content_async([
                    prompt,
                    {"mime_type": mime_type, "data": file_content},
                ])

            data = json.loads(response.text)
            if ExtractionResult is not None:
                return ExtractionResult(**data)
            return data

        except Exception as e:
            logger.error(f"Gemini extraction failed: {e}")
            raise  # let tenacity handle retries

    @gemini_retry
    async def ask_advisor(self, question: str, context: Optional[str] = None) -> str:
        """
        Ask a general business intelligence question to the RetailMind advisor.
        Returns the advisor's answer as a string.
        """
        if self.chat_model is None:
            return "AI advisor is not configured. Please set GEMINI_API_KEY."

        full_prompt = f"""
        You are 'RetailMind Advisor', a helpful retail business intelligence assistant for the RetailMind application.
        Your goal is to make complex sales, margin, inventory, and demand data easy for store owners to understand.

        CRITICAL GUARDRAIL - SCOPE LIMITATION:
        You MUST ONLY answer questions related to retail business operations, store sales, margin analysis, product pricing, dead stock, demand signals, or the RetailMind application.
        If the user asks about ANYTHING else (e.g., personal topics like overthinking, coding, general history, general knowledge, recipes, general personal finances, generating stories), you MUST politely decline and state exactly:
        "I am RetailMind's Business Intelligence Advisor. I can only assist you with questions related to your retail store sales, margins, dead stock, demand spikes, and inventory trends."
        Do NOT fulfill requests outside this retail business scope under any circumstances.

        TONE RULES:
        - Use simple, direct English.
        - Avoid complex statistical jargon (if you use a complex term, explain it simply).
        - Be insightful, analytical, and professional.
        - Sound like a high-quality financial editor (like a 'Retail Insights' column).

        User Context (Current Store Dashboard Data): {context if context else "No specific context provided."}
        Question: {question}

        Provide a short, punchy answer (max 100 words) with one actionable retail tip.
        """

        try:
            response = await self.chat_model.generate_content_async(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini advisor failed: {e}")
            raise

    async def stream_advisor(self, question: str, context: Optional[str] = None):
        """
        Asynchronously stream answers from the RetailMind advisor.
        """
        if self.chat_model is None:
            yield "AI advisor is not configured. Please set GEMINI_API_KEY."
            return

        full_prompt = f"""
        You are 'RetailMind Advisor', a helpful retail business intelligence assistant for the RetailMind application.
        Your goal is to make complex sales, margin, inventory, and demand data easy for store owners to understand.

        CRITICAL GUARDRAIL - SCOPE LIMITATION:
        You MUST ONLY answer questions related to retail business operations, store sales, margin analysis, product pricing, dead stock, demand signals, or the RetailMind application.
        If the user asks about ANYTHING else (e.g., personal topics like overthinking, coding, general history, general knowledge, recipes, general personal finances, generating stories), you MUST politely decline and state exactly:
        "I am RetailMind's Business Intelligence Advisor. I can only assist you with questions related to your retail store sales, margins, dead stock, demand spikes, and inventory trends."
        Do NOT fulfill requests outside this retail business scope under any circumstances.

        TONE RULES:
        - Use simple, direct English.
        - Avoid complex statistical jargon (if you use a complex term, explain it simply).
        - Be insightful, analytical, and professional.
        - Sound like a high-quality financial editor (like a 'Retail Insights' column).

        User Context (Current Store Dashboard Data): {context if context else "No specific context provided."}
        Question: {question}

        Provide a short, punchy answer (max 100 words) with one actionable retail tip.
        """

        try:
            response = await self.chat_model.generate_content_async(full_prompt, stream=True)
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Gemini advisor streaming failed: {e}")
            raise


# Singleton instance
gemini_service = GeminiService()
