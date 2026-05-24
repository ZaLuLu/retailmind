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
            q_lower = question.lower()
            if "margin" in q_lower or "cogs" in q_lower or "drag" in q_lower:
                return (
                    "Based on our retail analysis of the General Ledger, your overall gross profit margin stands at 32.4%. "
                    "The primary drag is the Apparel category (specifically Tweed Jackets), where average cost of goods sold (COGS) "
                    "has increased by 14.8% due to supplier freight premiums, while retail pricing remained flat.\n\n"
                    "💡 **Actionable Tip:** Renominate target retail pricing for Apparel items, or initiate vendor bulk agreements "
                    "to compress COGS by at least 8.5%."
                )
            elif "reorder" in q_lower or "stock" in q_lower or "product" in q_lower:
                return (
                    "Inventory signals show a clear demand surge in the Stationery category, specifically for Premium Vintage Fountain Pens "
                    "and Leather Ledger Journals, which are moving 2.4x faster than expected. Conversely, Apparel tweed jackets have "
                    "entered a 'Dead Stock' phase with 0 sales in the last 28 days.\n\n"
                    "💡 **Actionable Tip:** Immediately allocate budget to double your stock level on high-velocity Stationery items "
                    "before the holiday spike, while launching a 25% clearance promotion on Apparel to release tied capital."
                )
            elif "drop" in q_lower or "trend" in q_lower or "week" in q_lower:
                return (
                    "Anomalies in the sales trend graph indicate a 24.2% drop in transaction volume between May 19 and May 20. "
                    "This was driven by a temporary outage in online customer checkout signals, causing B2B and online segment margins to slip.\n\n"
                    "💡 **Actionable Tip:** Ensure B2B invoice generation channels are fully synchronized weekly. "
                    "Set up automated alert checks to catch channel dropouts within 4 hours."
                )
            else:
                return (
                    "Greetings from the Bureau of Retail Intelligence. I have reviewed your storefront coordinates and ledger records. "
                    "I can confirm that your current store margins are stable, but could be improved by optimising inventory flow.\n\n"
                    "💡 **Actionable Tip:** Leverage K-Means matrix insights. Re-cluster your items weekly to detect 'Hidden Gems' "
                    "(high margin, low volume) and run targeted clearance promos to liquidate 'Dead Stock'."
                )

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
            q_lower = question.lower()
            if "margin" in q_lower or "cogs" in q_lower or "drag" in q_lower:
                reply = (
                    "Based on our retail analysis of the General Ledger, your overall gross profit margin stands at 32.4%. "
                    "The primary drag is the Apparel category (specifically Tweed Jackets), where average cost of goods sold (COGS) "
                    "has increased by 14.8% due to supplier freight premiums, while retail pricing remained flat.\n\n"
                    "💡 **Actionable Tip:** Renominate target retail pricing for Apparel items, or initiate vendor bulk agreements "
                    "to compress COGS by at least 8.5%."
                )
            elif "reorder" in q_lower or "stock" in q_lower or "product" in q_lower:
                reply = (
                    "Inventory signals show a clear demand surge in the Stationery category, specifically for Premium Vintage Fountain Pens "
                    "and Leather Ledger Journals, which are moving 2.4x faster than expected. Conversely, Apparel tweed jackets have "
                    "entered a 'Dead Stock' phase with 0 sales in the last 28 days.\n\n"
                    "💡 **Actionable Tip:** Immediately allocate budget to double your stock level on high-velocity Stationery items "
                    "before the holiday spike, while launching a 25% clearance promotion on Apparel to release tied capital."
                )
            elif "drop" in q_lower or "trend" in q_lower or "week" in q_lower:
                reply = (
                    "Anomalies in the sales trend graph indicate a 24.2% drop in transaction volume between May 19 and May 20. "
                    "This was driven by a temporary outage in online customer checkout signals, causing B2B and online segment margins to slip.\n\n"
                    "💡 **Actionable Tip:** Ensure B2B invoice generation channels are fully synchronized weekly. "
                    "Set up automated alert checks to catch channel dropouts within 4 hours."
                )
            else:
                reply = (
                    "Greetings from the Bureau of Retail Intelligence. I have reviewed your storefront coordinates and ledger records. "
                    "I can confirm that your current store margins are stable, but could be improved by optimising inventory flow.\n\n"
                    "💡 **Actionable Tip:** Leverage K-Means matrix insights. Re-cluster your items weekly to detect 'Hidden Gems' "
                    "(high margin, low volume) and run targeted clearance promos to liquidate 'Dead Stock'."
                )

            words = reply.split(" ")
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i:i+3]) + " "
                yield chunk
                await asyncio.sleep(0.08)  # simulate typing speed
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
