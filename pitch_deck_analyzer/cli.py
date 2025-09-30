"""
Command-line interface
"""

import argparse
from pathlib import Path
from tqdm import tqdm

from pitch_deck_analyzer.utils import ensure_requirements, slugify_filename
from pitch_deck_analyzer.extractors import extract_from_pdf, extract_from_pptx
from pitch_deck_analyzer.web import duckduckgo_search, fetch_page_text
from pitch_deck_analyzer.analysis.openrouter import OpenRouterClient, model_supports_vision
from pitch_deck_analyzer.analysis.image_analyzer import ImageAnalyzer
from pitch_deck_analyzer.report_generator import ReportGenerator
from pitch_deck_analyzer.config import DEFAULT_MODEL, VISION_MODEL

def analyze_pitchdeck(input_path: str, output_path: str, search_online: bool = True, 
                     model: str = None, vision_model: str = None, use_openrouter: bool = True):
    """Main analysis pipeline"""
    model = model or DEFAULT_MODEL
    vision_model = vision_model or VISION_MODEL or model
    in_path = Path(input_path)
    out_path = Path(output_path)
    tmp_dir = Path(".pda_tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = tmp_dir / slugify_filename(in_path.stem)
    assets_dir.mkdir(parents=True, exist_ok=True)

    if not in_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    print(f"Analyzing: {in_path.name}")
    print(f"Using model (text): {model}")
    print(f"Vision model: {vision_model}")
    print(f"OpenRouter enabled: {use_openrouter}")

    # Extract content
    if in_path.suffix.lower() == ".pdf":
        print("Extracting from PDF...")
        extracted = extract_from_pdf(str(in_path), assets_dir)
    elif in_path.suffix.lower() == ".pptx":
        print("Extracting from PPTX...")
        extracted = extract_from_pptx(str(in_path), assets_dir)
    else:
        raise ValueError("Unsupported input format. Only .pdf and .pptx are supported.")

    deck_text = extracted.get("text", "")
    images = extracted.get("images", [])
    print(f"Extracted {len(deck_text)} characters of text and {len(images)} images")

    # Get company hint
    company_hint = None
    if deck_text:
        first_lines = [ln.strip() for ln in deck_text.splitlines() if ln.strip()]
        company_hint = first_lines
        # if first_lines:
        #     candidate = first_lines[0]
        #     if len(candidate.split()) <= 12:
        #         company_hint = candidate

    client = OpenRouterClient()
    instruction = "You are an expert analyzer. The provided information is the extracted text from the first page of a pitcher deck. Identify the name of the company from the text. The name is there in the text. Return from you should be just the name of the company, and nothing else."
    prompt = "\n\n".join(company_hint) + "\n\n" + instruction 
    messages = [{"role": "user", "content": prompt}]
    company_hint = client.chat(messages, model=model, max_tokens=1800)

    # Analyze images
    images_analyses = {}
    if images and use_openrouter:
        if not model_supports_vision(vision_model):
            print(f"Warning: chosen vision model '{vision_model}' does not look vision-capable. Skipping image analyses.")
            for p in images:
                images_analyses[str(p.name)] = f"(skipped) model '{vision_model}' not vision-capable"
        else:
            
            analyzer = ImageAnalyzer(client)
            images_analyses = analyzer.analyze_images(images, model, vision_model)

    # Web search
    web_texts = []
    if search_online:
        query = company_hint or (deck_text.strip().split('\n')[0] if deck_text else "")
        if query:
            print(f"Searching web for: {query}")
            try:
                results = duckduckgo_search(query)
                for r in results:
                    t = fetch_page_text(r)
                    if t:
                        web_texts.append(f"Source: {r}\n\n{t}")
                    if len(web_texts) >= 5:
                        break
            except Exception as e:
                print(f"Web search failed: {e}")

    # Generate report
    if use_openrouter:
        try:
            client = OpenRouterClient()
            generator = ReportGenerator(client)
            final_markdown = generator.synthesize_report(
                deck_text, images_analyses, web_texts, company_hint, model, vision_model
            )
        except Exception as e:
            print(f"OpenRouter synthesis failed: {e}")
            final_markdown = f"# Analysis failed\nOpenRouter synthesis failed: {e}\n\nRaw extracted text attached below.\n\n---\n\n" + deck_text[:10000]
    else:
        generator = ReportGenerator(None)
        final_markdown = generator.generate_local_report(deck_text, images_analyses)

    # Clean and write report
    cleaned_markdown = final_markdown
    if cleaned_markdown.startswith("```markdown"):
        cleaned_markdown = cleaned_markdown[len("```markdown"):].lstrip("\n")
    if cleaned_markdown.endswith("```"):
        cleaned_markdown = cleaned_markdown[:-len("```")].rstrip("\n")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(cleaned_markdown)

    print(f"Wrote report to {out_path}")
    print(f"Assets and extracted images are in: {assets_dir}")

def cli():
    """Command-line interface"""
    parser = argparse.ArgumentParser(description="PitchDeck Analyzer: PDF/PPTX -> investor Markdown brief")
    parser.add_argument("--input", "-i", required=True, help="Input .pdf or .pptx file path")
    parser.add_argument("--output", "-o", default="report.md", help="Output markdown file path")
    
    # default = True, and allow disabling it explicitly
    parser.add_argument("--no-search-online", action="store_false", dest="search_online", 
                        help="Disable web search for company info")
    
    parser.add_argument("--model", default=None, help="OpenRouter model name to use (override default)")
    parser.add_argument("--vision-model", default=None, help="Explicit vision-capable OpenRouter model name (optional)")
    parser.add_argument("--no-openrouter", action="store_true", help="Disable OpenRouter calls and run local-only extraction")
    
    args = parser.parse_args()
    ensure_requirements()

    analyze_pitchdeck(
        args.input, 
        args.output, 
        search_online=args.search_online,   # now defaults to True
        model=args.model, 
        vision_model=args.vision_model, 
        use_openrouter=not args.no_openrouter
    )
