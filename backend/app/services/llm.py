from ..core.config import settings
import json
import logging
from typing import Optional
import asyncio
from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

groq_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)


class LLMService:
    def __init__(self):
        # Configure Groq
        if settings.GROQ_API_KEY:
            try:
                self.groq_client = AsyncGroq(
                    api_key=settings.GROQ_API_KEY,
                    timeout=settings.GROQ_TIMEOUT_SECONDS
                )
            except Exception as e:
                logger.error("Failed to configure Groq client: %s", e)
                self.groq_client = None
        else:
            logger.warning("GROQ_API_KEY is not set. Groq features will be unavailable.")
            self.groq_client = None

    @groq_retry
    async def ask_advisor(
        self,
        question: str,
        context: Optional[str] = None,
        history: Optional[list[dict]] = None,
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Ask a retail business intelligence question to the RetailMind advisor.
        Returns the advisor's answer as a string.
        """
        # Truncate context to prevent token exhaustion attacks
        safe_context = (context or "No specific context provided.")[:2000]
        # Escape any curly braces in context to prevent f-string injection
        safe_context = safe_context.replace("{", "{{").replace("}", "}}")

        if not system_instruction:
            if "You are a retail business intelligence analyst" in question:
                system_instruction = (
                    "You are a retail business intelligence analyst. "
                    "Write ONE sharp, actionable sentence (max 20 words) summarising the most important insight from this data. "
                    "Sound like a Financial Times headline — factual, direct, no fluff."
                )
                question = "Summarise the data."
            else:
                system_instruction = (
                    "You are RetailMind's AI Business Advisor — a world-class retail analytics expert. "
                    "You have access to the user's real store data. Give specific, data-driven advice. "
                    "You ONLY answer questions about retail operations: sales, margins, inventory, dead stock, demand signals, pricing, and the RetailMind application. "
                    "\nRules:\n"
                    "- Always cite real numbers from the data (product names, percentages, revenue figures)\n"
                    "- End every response with ONE concrete action the owner can take today\n"
                    "- Use markdown: **bold** numbers, bullet points for lists, avoid walls of text\n"
                    "- For off-topic questions: professionally redirect to retail analytics. Respond exactly: 'I am RetailMind's Business Intelligence Advisor. I can only assist with retail store sales, margins, dead stock, demand spikes, and inventory trends.'\n"
                    "- Never invent numbers not in the data; say 'I need more data' if insufficient\n"
                    "- Keep responses under 200 words unless the user asks for detail"
                )

        user_message = f"Store Dashboard Data: {safe_context}\n\nQuestion: {question}"

        # Try Groq
        if self.groq_client is not None:
            try:
                messages = [{"role": "system", "content": system_instruction}]
                if history:
                    for msg in history:
                        role = "assistant" if msg.get("role") in ("advisor", "model") else "user"
                        content = msg.get("content", "")
                        if content:
                            messages.append({"role": role, "content": content})
                messages.append({"role": "user", "content": user_message})

                response = await asyncio.wait_for(
                    self.groq_client.chat.completions.create(
                        model=settings.GROQ_MODEL,
                        messages=messages,
                        max_tokens=600,
                        temperature=0.2,
                    ),
                    timeout=settings.GROQ_TIMEOUT_SECONDS
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error("Groq advisor failed: %s. Using static fallback.", type(e).__name__)

        return self._fallback_answer(question)

    async def stream_advisor(
        self,
        question: str,
        context: Optional[str] = None,
        history: Optional[list[dict]] = None,
        system_instruction: Optional[str] = None
    ):
        """
        Asynchronously stream answers from the RetailMind advisor.
        """
        safe_context = (context or "No specific context provided.")[:2000]
        safe_context = safe_context.replace("{", "{{").replace("}", "}}")

        if not system_instruction:
            system_instruction = (
                "You are RetailMind's AI Business Advisor — a world-class retail analytics expert. "
                "You have access to the user's real store data. Give specific, data-driven advice. "
                "You ONLY answer questions about retail operations: sales, margins, inventory, dead stock, demand signals, pricing, and the RetailMind application. "
                "\nRules:\n"
                "- Always cite real numbers from the data (product names, percentages, revenue figures)\n"
                "- End every response with ONE concrete action the owner can take today\n"
                "- Use markdown: **bold** numbers, bullet points for lists, avoid walls of text\n"
                "- For off-topic questions: professionally redirect to retail analytics. Respond exactly: 'I am RetailMind's Business Intelligence Advisor. I can only assist with retail store sales, margins, dead stock, demand spikes, and inventory trends.'\n"
                "- Never invent numbers not in the data; say 'I need more data' if insufficient\n"
                "- Keep responses under 200 words unless the user asks for detail"
            )

        user_message = f"Store Dashboard Data: {safe_context}\n\nQuestion: {question}"

        # Try Groq streaming
        if self.groq_client is not None:
            try:
                messages = [{"role": "system", "content": system_instruction}]
                if history:
                    for msg in history:
                        role = "assistant" if msg.get("role") in ("advisor", "model") else "user"
                        content = msg.get("content", "")
                        if content:
                            messages.append({"role": role, "content": content})
                messages.append({"role": "user", "content": user_message})

                response = await asyncio.wait_for(
                    self.groq_client.chat.completions.create(
                        model=settings.GROQ_MODEL,
                        messages=messages,
                        max_tokens=600,
                        temperature=0.2,
                        stream=True,
                    ),
                    timeout=settings.GROQ_TIMEOUT_SECONDS
                )
                async for chunk in response:
                    text = chunk.choices[0].delta.content
                    if text:
                        yield text
                return
            except Exception as e:
                logger.error("Groq advisor streaming failed: %s. Using static fallback streaming.", type(e).__name__)

        reply = self._fallback_answer(question)
        words = reply.split(" ")
        for i in range(0, len(words), 3):
            chunk = " ".join(words[i:i+3]) + " "
            yield chunk
            await asyncio.sleep(0.08)

    async def generate_audit_report(
        self,
        anomaly_snapshot: dict,
        system_instruction: Optional[str] = None,
    ) -> str:
        """
        Generate a structured executive audit report from the anomaly snapshot.

        Uses a dedicated system prompt tuned for audit reports, a higher token
        budget (1200 tokens), and lower temperature (0.15) for deterministic,
        professional output.

        Falls back to a template-filled local report if Groq is unavailable.
        """
        import json

        if not system_instruction:
            system_instruction = (
                "You are RetailMind's AI Lead Auditor — a world-class retail operations analyst. "
                "You receive a structured JSON bundle of store metrics, demand anomalies, and forecast data. "
                "Write a professional executive audit report in Markdown with EXACTLY these four sections:\n\n"
                "### 1. Executive Summary\n"
                "One sharp paragraph summarising overall health, revenue trend, and the top concern.\n\n"
                "### 2. Anomaly & Risk Breakdown\n"
                "Bullet-point each detected anomaly (demand spikes, dead stock, margin erosion). "
                "Cite product names and exact numbers. Skip empty categories.\n\n"
                "### 3. Demand Outlook (14-Day Forecast)\n"
                "Summarise the revenue forecast trend in one sentence. "
                "Call out the forecast peak day and trough day if available.\n\n"
                "### 4. Recommended Action Plan\n"
                "Provide 3-5 concrete, prioritised actions the store owner should take within the next 7 days. "
                "Each action must be specific to the data (name the product, the percentage, the timeline).\n\n"
                "Rules:\n"
                "- Never invent numbers; cite only what is in the JSON\n"
                "- Use **bold** for all numeric values\n"
                "- Keep the total report under 400 words\n"
                "- No generic advice — everything must be data-specific"
            )

        context = json.dumps(anomaly_snapshot, default=str)[:3000]
        user_message = f"Audit Data Bundle:\n{context}\n\nGenerate the executive audit report."

        if self.groq_client is not None:
            try:
                response = await asyncio.wait_for(
                    self.groq_client.chat.completions.create(
                        model=settings.GROQ_MODEL,
                        messages=[
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": user_message},
                        ],
                        max_tokens=1200,
                        temperature=0.15,
                    ),
                    timeout=settings.GROQ_TIMEOUT_SECONDS,
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error("Groq audit report generation failed: %s", type(e).__name__)

        # ── Structured fallback (no Groq) ─────────────────────────────────────
        total_revenue = anomaly_snapshot.get("total_revenue", 0.0)
        margin_pct = anomaly_snapshot.get("overall_margin_pct", 0.0)
        mom_pct = anomaly_snapshot.get("mom_revenue_change_pct", 0.0)
        products_checked = anomaly_snapshot.get("total_products_checked", 0)
        anomalies = anomaly_snapshot.get("anomalies_detected", 0)

        demand_spikes = anomaly_snapshot.get("demand_signals", [])
        dead_stock = anomaly_snapshot.get("dead_stock_alerts", [])
        margin_erosion = anomaly_snapshot.get("margin_erosion_alerts", [])

        spike_lines = "\n".join(
            f"  - **{s['product_name']}** — Z-score {s.get('z_score', 'N/A')}, +{s.get('deviation_pct', 0):.0f}% vs rolling avg"
            for s in demand_spikes[:5]
        ) or "  - None detected"

        dead_lines = "\n".join(
            f"  - **{d['product_name']}** — no sales in **{d['last_sale_days_ago']} days**"
            for d in dead_stock[:5]
        ) or "  - None detected"

        margin_lines = "\n".join(
            f"  - **{m['product_name']}** — margin at **{m['margin_pct']:.1f}%**"
            for m in margin_erosion[:5]
        ) or "  - None detected"

        return (
            f"### 1. Executive Summary\n"
            f"Audit covered **{products_checked}** products. Total revenue is "
            f"**₹{total_revenue:,.2f}** at a gross margin of **{margin_pct:.1f}%** "
            f"({'+' if mom_pct >= 0 else ''}{mom_pct:.1f}% vs prior period). "
            f"**{anomalies}** operational risk(s) require attention.\n\n"
            f"### 2. Anomaly & Risk Breakdown\n"
            f"**Demand Spikes ({len(demand_spikes)}):**\n{spike_lines}\n\n"
            f"**Dead Stock ({len(dead_stock)}):**\n{dead_lines}\n\n"
            f"**Margin Erosion ({len(margin_erosion)}):**\n{margin_lines}\n\n"
            f"### 3. Demand Outlook (14-Day Forecast)\n"
            f"Holt-Winters revenue projection is available in the Forecast tab. "
            f"Connect Groq API for a narrative forecast interpretation.\n\n"
            f"### 4. Recommended Action Plan\n"
            f"1. Clear dead-stock items older than 30 days with a promotional discount.\n"
            f"2. Reorder top demand-spiking products before next weekly cycle.\n"
            f"3. Review pricing for all products below {settings.MARGIN_EROSION_THRESHOLD_PCT}% margin threshold.\n"
            f"4. Configure the Groq API key in `.env` to unlock AI-generated insights.\n"
        )

    def _fallback_answer(self, question: str) -> str:
        """
        Rule-based fallback when Groq API key is not configured.
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
                "Connect a Groq API key in your environment settings to unlock AI-powered insights. "
                "💡 Tip: Use the dynamic pricing simulator to optimize your category margins."
            )


# Singleton instance
llm_service = LLMService()
