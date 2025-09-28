# Pitch-Deck-Analyzer

> **One-line:** A CLI tool that extracts text and images from a PDF or PPTX pitch deck, optionally enriches that content with online search results and LLM image/text analysis via OpenRouter, and synthesizes an investor-focused Markdown report.

---

## Overview

`Pitch-Deck-Analyzer` is a small Python package + CLI that takes a company pitch deck (`.pdf` or `.pptx`) and generates a concise, investor-style Markdown report summarising problem, product, traction, team, market, risks and sources. The tool:

- extracts text and images from slides or PDF pages,
- searches the web to gather extra context for the company,
- uses an LLM (OpenRouter-compatible) to analyze images and synthesize a final report in Markdown,
- writes a `report.md` output and stores extracted assets in a temporary folder.

---

## Quick start (install & run)

1. Clone the repo:

```bash
git clone https://github.com/Dhruvil-CS/Pitch-Deck-Analyzer.git
cd Pitch-Deck-Analyzer
```

2. Create and activate a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
.\.venv\Scripts\activate  # Windows (PowerShell/CMD)
```

3. Install runtime dependencies:

```bash
pip install -r requirements.txt
```

4. Configure environment variables (for optional OpenRouter LLM usage):

Create a `.env` file (or set env vars in your shell):

```
OPENROUTER_API_URL=https://api.openrouter.example/v1/chat
OPENROUTER_API_KEY=sk-...
OPENROUTER_MODEL=<default-model-name>           # optional
OPENROUTER_VISION_MODEL=<vision-model-name>     # optional
```

5. Run the CLI (example):

```bash
python main.py --input /path/to/deck/
```

CLI flags (use `python main.py -h` for help):

- `--input` / `-i` — path to `.pdf` or `.pptx` (required)
- `--output` / `-o` — output Markdown filename (defaults to `report.md`)
- `--no-search-online` — disable the DuckDuckGo web search stage
- `--model` — override the configured OpenRouter text model
- `--vision-model` — override the vision-capable model (if available)
- `--no-openrouter` — disable all OpenRouter API calls and produce a local-only report

> Note: the CLI automatically checks for required Python packages and will exit with a message if any are missing.

---

## Supported input formats

- `.pdf` — extracted using **PyMuPDF** (fast, extracts text and embedded images). Works well for native PDFs.
- `.pptx` — extracted using **python-pptx**, iterates slides, extracts shapes with text and picture shapes.

If a deck is scanned (images-only PDF), I am planning to add an OCR step (see Future improvements).

---

## Output produced

When you run the tool it produces:

- `report.md` (or whatever you set with `--output`): a Markdown investor-style report. If OpenRouter is enabled the report will be synthesized by the LLM; otherwise a minimal local report with extracted text and per-image summaries is written.
- `.pda_tmp/<slug>/` — a temporary folder where extracted images and supporting assets are saved. The folder name is generated from the input filename (slugified) and printed at the end of the run.

Example CLI output messages (the CLI prints progress):

- `Analyzing: company_deck.pdf`
- `Extracted {N} characters of text and {M} images`
- `Searching web for: <company_hint>` (if search enabled)
- `Wrote report to <output>`
- `Assets and extracted images are in: .pda_tmp/<slug>`

---

## How it works — pipeline & code map

**Top-level entrypoint**: `main.py` calls `pitch_deck_analyzer.cli.cli()` which runs the pipeline. The CLI performs basic checks, parses arguments and invokes `analyze_pitchdeck(...)`.

**Extraction**
- `pitch_deck_analyzer.extractors.pdf.extract_from_pdf` — uses `PyMuPDF (fitz)` to iterate pages, collect text and save embedded images.
- `pitch_deck_analyzer.extractors.pptx.extract_from_pptx` — uses `python-pptx` to iterate slides and extract text and pictures.

**Web enrichment**
- `pitch_deck_analyzer.web.duckduckgo_search` — performs a DuckDuckGo HTML search and returns a cleaned list of URLs.
- `pitch_deck_analyzer.web.fetcher.fetch_page_text` — fetches each URL and extracts title/description and a few paragraph snippets (BeautifulSoup).

**LLM & image analysis (optional)**
- `pitch_deck_analyzer.analysis.openrouter.OpenRouterClient` — small client that sends chat requests to an OpenRouter-compatible API. It also converts images to base64 data-URIs (with resizing/compression) subject to `IMAGE_SEND_MAX_BYTES`.
- `pitch_deck_analyzer.analysis.image_analyzer.ImageAnalyzer` — wrapper that uses `OpenRouterClient.analyze_image()` to produce a concise investor-focused summary per image.
- `pitch_deck_analyzer.report_generator.ReportGenerator` — builds a prompt from deck text, image summaries and web texts and asks the LLM to synthesize a structured Markdown report.

**Utilities**
- `pitch_deck_analyzer.utils.ensure_requirements()` — checks for required libraries and exits with a helpful message if they are missing.
- `pitch_deck_analyzer.utils.slugify_filename()` — makes a filesystem-safe name for the assets folder.

**Configuration**
- `pitch_deck_analyzer.config` reads environment variables (OpenRouter URL/key, default models) and contains image limits and user-agent defaults.

---

## Configuration / environment variables

The following environment variables (or `.env`) are supported:

- `OPENROUTER_API_URL` — base URL for the OpenRouter chat API.
- `OPENROUTER_API_KEY` — API key (required if you enable OpenRouter calls).
- `OPENROUTER_MODEL` — default text model to use if not specified in CLI.
- `OPENROUTER_VISION_MODEL` — preferred vision-capable model name (optional).

If you choose not to set these, run the CLI with `--no-openrouter` to avoid LLM calls and still get a local extraction report.

---

## Dependencies

All required Python packages are listed in `requirements.txt` — the primary ones are:

- `PyMuPDF` (fitz) — PDF text & image extraction
- `python-pptx` — PPTX parsing
- `Pillow` — image handling and thumbnails
- `requests` — HTTP requests
- `beautifulsoup4` — HTML parsing for simple web scraping
- `tqdm` — progress bars
- `python-dotenv` — optional .env loading

Install them via `pip install -r requirements.txt`.

---

## Example: run with no external LLM

If you want to run entirely locally (no network calls to OpenRouter):

```bash
python main.py -i /path/to/your/deck --no-openrouter --no-search-online
```

This will extract text and images and write a minimal local report containing the extracted text and image placeholders.

---

## Troubleshooting

- **Missing packages**: The CLI runs `ensure_requirements()` and exits with a list of missing packages. Run `pip install -r requirements.txt` inside a virtualenv.
- **OPENROUTER_API_KEY missing**: If you enable OpenRouter usage but did not set `OPENROUTER_API_KEY`, the OpenRouter client will raise a runtime error. Either set the env var or run with `--no-openrouter`.
- **Large images**: The OpenRouter client tries to compress thumbnails to fit under `IMAGE_SEND_MAX_BYTES`. If compression fails or the network call errors, image analysis will be skipped with a warning.
- **Scanned PDFs**: This tool does not run OCR by default. For image-only PDFs add an OCR preprocessing step (Tesseract or an OCR model) and feed the resulting text into the pipeline.

---

## Potential improvements / roadmap

This is a compact, useful prototype. Suggestions for practical improvements if you want to take it to production:

- **More robust parsing**: detect tables & extract structured financial tables (use `camelot`, `tabula` or vision models).
- **Parallelization**: analyze images in parallel to reduce total runtime.
- **Caching & rate-limits**: cache web search results and LLM outputs and add exponential backoff for API calls.
- **Add Dockerfile and CI**: reproducible environment and GitHub Actions to run lint/test and optionally publish a pip package.
- **Support additional LLM backends**: (Optional) adapters for OpenAI, Vertex, Anthropic, and local LLMs (for private deployments).
- **Add JSON output**: in addition to Markdown, export machine-readable JSON for downstream automation and indexing.
- **Improve prompt engineering**: (I believe this is really important) add a few-shot prompt template and a validation pass to reduce hallucinations.
- **Web UI**: a simple web frontend that allows uploading a deck and downloading the report.
- **Security improvements**: sanitize fetched web content, respect robots.txt, and limit bandwidth/timeout.

---

## Code layout (quick map)

```
main.py                         # CLI entrypoint
pitch_deck_analyzer/            # package
  __init__.py
  cli.py                        # CLI pipeline implementation
  utils.py                      # small helpers & requirement checks
  extractors/                   # extraction for .pdf/.pptx
    __init__.py
    pdf.py
    pptx.py
  web/                          # simple DuckDuckGo search + fetcher
    __init__.py
    search.py
    fetcher.py
  analysis/                     # LLM & image analysis helper(s)
    openrouter.py
    image_analyzer.py
  report_generator.py           # assembles the prompt and synthesizes Markdown
  config.py                     # env-based configuration & constants
requirements.txt
```

---

## License & attribution

N/A

---


