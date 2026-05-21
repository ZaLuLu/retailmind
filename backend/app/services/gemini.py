import google.generativeai as genai
from ..core.config import settings
from ..schemas.transaction import ExtractionResult
import json
import logging
from typing import Optional
import PIL.Image
import io
import asyncio

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

gemini_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)

class GeminiService:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is not set. Extraction will fail.")
            return
            
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config={
                "response_mime_type": "application/json",
            }
        )
        self.chat_model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL
        )

    @gemini_retry
    async def extract_transaction(self, file_content: bytes, mime_type: str) -> Optional[ExtractionResult]:
        """
        Extract transaction data from a document using Gemini 1.5.
        """
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

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Handle different file types
                if "image" in mime_type:
                    img = PIL.Image.open(io.BytesIO(file_content))
                    response = await self.model.generate_content_async([prompt, img])
                else:
                    # For PDF, we send bytes with mime_type
                    response = await self.model.generate_content_async([
                        prompt,
                        {"mime_type": mime_type, "data": file_content}
                    ])

                data = json.loads(response.text)
                return ExtractionResult(**data)
                
            except Exception as e:
                logger.error(f"Gemini Extraction failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt) # Exponential backoff
                else:
                    return None

    @gemini_retry
    async def ask_advisor(self, question: str, context: Optional[str] = None) -> str:
        """
        Ask a general business intelligence question to the RetailMind advisor.
        """
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
            logger.error(f"Gemini Advisor failed: {str(e)}")
            raise e

# Singleton instance
gemini_service = GeminiService()
