"""
Report generation functionality
"""

from pitch_deck_analyzer.analysis.openrouter import OpenRouterClient, model_supports_vision
from pitch_deck_analyzer.config import MAX_SEARCH_RESULTS

class ReportGenerator:
    def __init__(self, openrouter_client: OpenRouterClient):
        self.client = openrouter_client

    def synthesize_report(self, deck_text: str, images_analyses: dict, web_texts: list, 
                         company_hint: str = None, model: str = None, vision_model: str = None) -> str:
        """Synthesize final report from all data sources"""
        image_section = "\n\n".join(f"Image {i+1}:\n{images_analyses[p]}" for i, p in enumerate(images_analyses))
        web_section = "\n\n---\n\n".join(web_texts[:5]) if web_texts else ""

        instruction = """
You are an expert Venture Capital analyst preparing a report in MARKDOWN for an Investment Manager focused on early-stage startups. Use the data below which contains: 1) text extracted from a pitch deck, 2) summaries of images from the deck, and 3) text fetched from the web.\n\n
Produce a well-structured markdown document with the following sections: Title header with company name; Quick investment snapshot; Problem & Solution; Product / Technology & IP; Founders & Team; Market & TAM estimates; Traction & KPIs; Business model & monetization; Competitors & competitive advantage; Key risks & 3 quick red flags; Sources.\n\n
Search online to find latest information about the company and consider that as well while responding. If something is uncertain, label it as a guess. Prioritize correctness over imaginative claims.
"""

        context_parts = []
        if company_hint:
            context_parts.append(f"Company hint: {company_hint}")
        if deck_text:
            context_parts.append("=== DECK TEXT START ===\n" + (deck_text[:6000]) + "\n=== DECK TEXT END ===")
        if image_section:
            context_parts.append("=== IMAGE SUMMARIES START ===\n" + image_section + "\n=== IMAGE SUMMARIES END ===")
        if web_section:
            context_parts.append("=== WEB TEXTS START ===\n" + web_section + "\n=== WEB TEXTS END ===")

        big_prompt = "\n\n".join(context_parts) + "\n\n" + instruction
        messages = [{"role": "user", "content": big_prompt}]
        return self.client.chat(messages, model=model, max_tokens=5000)

    def generate_local_report(self, deck_text: str, images_analyses: dict) -> str:
        """Generate report without OpenRouter (local only)"""
        report = "# Quick Pitch Deck Extract\n\n"
        report += "## Extracted deck text (truncated)\n\n```\n" + deck_text + "\n```\n\n"
        
        if images_analyses:
            report += "## Images\n\n"
            for k, v in images_analyses.items():
                report += f"### {k}\n\n{v}\n\n"
        
        return report