"""
OpenRouter API client
"""

import base64
import json
import requests
from io import BytesIO
from pathlib import Path
from PIL import Image
from pitch_deck_analyzer.config import OPENROUTER_API_URL, OPENROUTER_API_KEY, USER_AGENT
from pitch_deck_analyzer.config import THUMB_MAX_DIM, THUMB_QUALITY, IMAGE_SEND_MAX_BYTES

def model_supports_vision(model_name: str) -> bool:
    """Check if model supports vision capabilities"""
    if not model_name:
        return False
    low = model_name.lower()
    return any(k in low for k in ("vision", "image", "multimodal", "clip", "gpt-4o", "gpt-4"))

class OpenRouterClient:
    def __init__(self, api_url: str = None, api_key: str = None):
        self.api_url = api_url or OPENROUTER_API_URL
        self.api_key = api_key or OPENROUTER_API_KEY
        
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY not set in environment")
        if not self.api_url:
            raise RuntimeError("OPENROUTER_API_URL not configured")

    def _image_to_dataurl(self,image_path: Path) -> tuple[str, int]:
        """Convert image to base64 data URL with optional compression."""
        orig_bytes = image_path.read_bytes()
        ext = image_path.suffix.lower()
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".png": "image/png", ".gif": "image/gif"}
        mime = mime_map.get(ext, "application/octet-stream")

        # If already small enough, return as-is
        if len(orig_bytes) <= IMAGE_SEND_MAX_BYTES:
            return f"data:{mime};base64,{base64.b64encode(orig_bytes).decode()}", len(orig_bytes)

        try:
            img = Image.open(image_path)
            img.thumbnail((THUMB_MAX_DIM, THUMB_MAX_DIM))  # resize in place
            thumb_bytes = self._compress_to_limit(img)

            return f"data:image/jpeg;base64,{base64.b64encode(thumb_bytes).decode()}", len(thumb_bytes)
        except Exception:
            # Fallback: return original file, even if oversized
            return f"data:application/octet-stream;base64,{base64.b64encode(orig_bytes).decode()}", len(orig_bytes)


    def _compress_to_limit(self,img: Image.Image) -> bytes:
        """Compress an image to fit under IMAGE_SEND_MAX_BYTES, reducing size/quality iteratively."""
        scale, quality = 1.0, THUMB_QUALITY
        while True:
            new_w, new_h = int(img.width * scale), int(img.height * scale)
            resized = img.resize((max(1, new_w), max(1, new_h)), Image.LANCZOS)
            bio = BytesIO()
            resized.save(bio, format="JPEG", quality=max(30, int(quality * scale)))
            data = bio.getvalue()

            if len(data) <= IMAGE_SEND_MAX_BYTES or scale <= 0.2:
                return data
            scale -= 0.15

    def chat(self, messages, model: str, max_tokens: int = 1500, temperature: float = 0.0) -> str:
        """Send chat completion request to OpenRouter"""
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }

        try:
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            try:
                body = resp.text
            except Exception:
                body = "(no body)"
            raise RuntimeError(f"OpenRouter API request failed: {e} - response body: {body}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OpenRouter API request failed: {e}")

        data = resp.json()
        if isinstance(data, dict):
            if "choices" in data and data["choices"]:
                choice = data["choices"][0]
                if isinstance(choice, dict) and "message" in choice:
                    return choice["message"].get("content", "")
                if isinstance(choice, dict) and "text" in choice:
                    return choice["text"]
            if "error" in data:
                raise RuntimeError(f"OpenRouter API error: {data['error']}")
        
        return json.dumps(data)

    def analyze_image(self, image_path: Path, model: str) -> str:
        """Analyze image using vision-capable model"""
        if not model_supports_vision(model):
            return f"(skipped) Model '{model}' does not appear to support vision."

        try:
            data_url, sent_bytes = self._image_to_dataurl(image_path)
            print(f"Analyzing image {image_path.name} ({sent_bytes} bytes)...")
            if len(data_url) > 250_000:
                embedded = f"[base64 image omitted due to size: {sent_bytes} bytes]"
            else:
                embedded = data_url

            prompt = f"""
You are an expert early-stage investor analyst with vision capabilities.
Analyze the image attached from a pitch deck and provide a concise (<=200 words) investor-focused summary.
Focus on: visible text or numbers, image type (logo, chart, screenshot, team photo), and any red flags or notable signals for due diligence.

Image reference: {image_path.name} (size {sent_bytes} bytes)
Image data: {embedded}

Start with: SUMMARY:
"""
            messages = [{"role": "user", "content": prompt}]
            out = self.chat(messages, model=model)
            
            if out and isinstance(out, str) and any(phrase in out.lower() for phrase in ("cannot analyze images", "unable to analyze", "i'm sorry")):
                return f"[Image analysis unavailable from model '{model}']: {out}"
            return f"Image analysis ({sent_bytes} bytes sent):\n{out}"
        except Exception as e:
            return f"[Image analysis failed: {e}]"

    def summarize_text(self, text: str, model: str, instruction: str = None) -> str:
        """Summarize text using OpenRouter"""
        if not instruction:
            instruction = (
                "You are an expert early-stage investor analyst. Given the text from a startup pitch deck or web pages, extract the most important information an Investment Manager needs: one-line summary, company name (if any), founder names and backgrounds, product description, business model, target market and TAM (explicit if present), traction metrics (revenue, users, growth %), fundraising history / ask, competitors and moat, risks/uncertainties, and 3 quick red flags (if any). Return the answer in MARKDOWN with headings and short bullet points, and include a \"Sources:\" section listing short URLs or snippets of where the info came from (if known). If you are guessing, mark it as a guess."
            )

        max_chunk = 4000
        if len(text) > max_chunk:
            text = text[:max_chunk] + "\n\n[TRUNCATED]"

        prompt = f"Context:\n\n{text}\n\n{instruction}"
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, model=model, max_tokens=1500)