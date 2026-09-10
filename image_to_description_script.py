#!/usr/bin/env python
"""
Minimal script: run Marker with ``ImageToDescriptionProcessor``.
"""

from pathlib import Path

from image_to_description import ImageToDescriptionProcessor
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser

PDF_PATH = Path(
    "Design Patterns in C# A Hands-on Guide with Real-World Examples - Vaskaran Sarcar.pdf"
)
PAGE_RANGE = [31]
OUTPUT_DIR = Path("test_output")

# Prepare config
config = {
    "extract_images": False,  # Must be False for processor to run!
    "output_dir": str(OUTPUT_DIR),
    "page_range": ",".join(str(p) for p in PAGE_RANGE),
    "output_format": "markdown",
    "use_llm": True,
    # Add any other LLM config keys needed (e.g., API key)
    # "gemini_api_key": "your_key_here",
}

# Create converter with the processor class
converter = PdfConverter(
    artifact_dict=create_model_dict(),
    config=ConfigParser(config).generate_config_dict(),
    processor_list=[ImageToDescriptionProcessor],
    # Replace with your actual LLM service if needed
    llm_service="marker.services.ollama.OllamaService",
)

# Run conversion and save markdown
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
rendered = converter(str(PDF_PATH))
final_md_path = OUTPUT_DIR / f"{PDF_PATH.stem}_processed.md"
final_md_path.write_text(rendered.markdown, encoding="utf-8")
print(f"✅ Processed markdown saved to: {final_md_path}")
