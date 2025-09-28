"""
Image analysis functionality
"""

from pathlib import Path
from pitch_deck_analyzer.analysis.openrouter import OpenRouterClient

class ImageAnalyzer:
    def __init__(self, openrouter_client: OpenRouterClient):
        self.client = openrouter_client

    def analyze_images(self, images: list, model: str, vision_model: str = None) -> dict:
        """Analyze multiple images"""
        images_analyses = {}
        chosen_model = vision_model or model
        
        for img_path in images:
            try:
                img_analysis = self.client.analyze_image(img_path, chosen_model)
                images_analyses[str(img_path.name)] = img_analysis
            except Exception as e:
                images_analyses[str(img_path.name)] = f"Failed to analyze image: {e}"
        
        return images_analyses