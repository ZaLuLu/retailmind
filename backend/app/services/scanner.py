import json
import logging
from typing import Optional, List, Dict, Any
from datetime import date
import google.generativeai as genai
from ..core.config import settings

logger = logging.getLogger(__name__)

class GeminiScannerService:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is not set. Gemini features will be unavailable.")
            self.model = None
            return
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config={
                "response_mime_type": "application/json",
            },
        )

    async def scan_invoice(self, file_content: bytes, mime_type: str) -> List[Dict[str, Any]]:
        """
        Scan a PDF/image receipt or invoice using Gemini 2.5 Flash.
        Returns a list of extracted sales records (line items).
        """
        if self.model is None:
            logger.warning("Gemini scanner model not initialised.")
            return []

        prompt = """
        You are an elite retail financial audit assistant. Analyze the attached document (receipt/invoice/bill) and extract the individual product line items/transactions.
        Return a JSON array of objects representing each product sale, containing:
        - product_name: The name of the product or item sold.
        - quantity_sold: The quantity of the item purchased (numeric float, e.g. 1.0 or 3.0).
        - unit_price: The price of a single unit of the item (numeric float, e.g. 129.99).
        - product_category: The predicted category of the item from: [Electronics, Apparel, Food & Beverage, Home & Garden, Stationery, Other].
        - sale_date: The date of the sale/invoice in YYYY-MM-DD format. If not found, use today's date.
        - product_sku: Any SKU, model number or barcode if visible on the line item.
        - customer_segment: Predict the customer segment based on the nature of purchase (usually "Walk-in" or "Online" or "B2B").
        - currency: The currency abbreviation (e.g. INR or USD). If INR or ₹ is shown, use "INR".

        Your response must be a valid JSON array of objects matching this schema, with no leading or trailing markdown blocks.
        """

        try:
            # Check if PDF or image and use correct API signature
            if "image" in mime_type:
                import PIL.Image
                import io
                img = PIL.Image.open(io.BytesIO(file_content))
                response = await self.model.generate_content_async([prompt, img])
            else:
                response = await self.model.generate_content_async([
                    prompt,
                    {"mime_type": mime_type, "data": file_content},
                ])

            text = response.text.strip()
            # Clean markdown codeblocks if Gemini added them despite config
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            items = json.loads(text)
            if not isinstance(items, list):
                if isinstance(items, dict) and "items" in items:
                    items = items["items"]
                else:
                    items = [items]

            # Normalise and compute total revenues
            normalised = []
            for item in items:
                qty = float(item.get("quantity_sold", 1.0))
                price = float(item.get("unit_price", 0.0))
                total = qty * price
                
                # Estimate a COGS fallback (around 60% of price) to calculate a mock margin
                cogs = round(price * 0.6, 2)
                margin = round(((total - (cogs * qty)) / total * 100), 2) if total > 0 else 0.0

                normalised.append({
                    "product_name": str(item.get("product_name", "Unknown Product")).strip(),
                    "product_sku": str(item.get("product_sku", "")).strip() or None,
                    "product_category": str(item.get("product_category", "Other")).strip(),
                    "quantity_sold": qty,
                    "unit_price": price,
                    "total_revenue": round(total, 2),
                    "cogs": round(cogs * qty, 2),
                    "gross_margin": margin,
                    "sale_date": str(item.get("sale_date", date.today().isoformat())),
                    "customer_segment": str(item.get("customer_segment", "Walk-in")).strip(),
                    "currency": str(item.get("currency", "INR")).strip(),
                })
            
            return normalised

        except Exception as e:
            logger.error(f"Gemini scanning failed: {e}")
            raise

scanner_service = GeminiScannerService()
