from __future__ import annotations

import base64
import io
from copy import deepcopy
from typing import Optional, List

import markdown2
import requests
from PIL import Image

from marker.processors import BaseProcessor
from marker.schema import BlockTypes
from marker.schema.document import Document
from marker.schema.registry import get_block_class


class ImageToTextProcessor(BaseProcessor):
    """Replace image blocks with markdown descriptions."""

    block_types = (BlockTypes.Picture, BlockTypes.Figure)

    def __init__(self, config: Optional[dict] = None) -> None:
        super().__init__(config)
        if config is None:
            config = {}
        self.ollama_url = config.get("ollama_url", "http://localhost:11434").rstrip("/")
        self.ollama_model = config.get("ollama_model", "llama3.2-vision:11b")
        self.vision_prompt = config.get(
            "vision_prompt",
            "Describe this image precisely in technical terms. Focus on diagrams, code, text, and technical content.",
        )

    def process_image_to_text(self, image: Image.Image) -> str:
        """Convert an image to a markdown description using the Ollama service."""
        try:
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            image_b64 = base64.b64encode(buffer.getvalue()).decode()
            payload = {
                "model": self.ollama_model,
                "prompt": self.vision_prompt,
                "images": [image_b64],
                "stream": False,
            }
            resp = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=120)
            resp.raise_for_status()
            result = resp.json()
            description = result.get("response", "").strip()
            return f"[Image Description: {description}]"
        except Exception as e:  # pragma: no cover - external service
            return f"[Image processing failed: {str(e)}]"

    def __call__(self, document: Document) -> None:
        TextClass = get_block_class(BlockTypes.Text)
        for page in document.pages:
            for block in list(page.contained_blocks(document, self.block_types)):
                try:
                    image = block.get_image(document, highres=True)
                    if image is None:
                        continue
                    markdown_text = self.process_image_to_text(image)
                    html = markdown2.markdown(markdown_text, extras=["tables"])
                    new_block = TextClass(
                        polygon=deepcopy(block.polygon),
                        page_id=block.page_id,
                        structure=deepcopy(block.structure),
                        text_extraction_method=block.text_extraction_method,
                        source="processor",
                        top_k=block.top_k,
                        metadata=block.metadata,
                        html=html,
                    )
                    page.replace_block(block, new_block)
                except Exception:
                    continue



def create_converter_with_image_to_text(
    config: Optional[dict] = None,
    ollama_url: str = "http://localhost:11434",
    ollama_model: str = "llama3.2-vision:11b",
    vision_prompt: str = (
        "Describe this image precisely in technical terms. Focus on diagrams, code, text, and technical content."
    ),
) -> "PdfConverter":
    """Return a PdfConverter that applies ImageToTextProcessor."""
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.config.parser import ConfigParser
    from marker.util import classes_to_strings

    if config is None:
        config = {"extract_images": True, "output_dir": "output"}

    if "page_range" in config and isinstance(config["page_range"], list):
        config["page_range"] = ",".join(str(p) for p in config["page_range"])

    # Store ollama params so the processor can access them
    config.update({
        "ollama_url": ollama_url,
        "ollama_model": ollama_model,
        "vision_prompt": vision_prompt,
    })

    config_parser = ConfigParser(config)
    processors = config_parser.get_processors()
    if processors is None:
        processors = classes_to_strings(list(PdfConverter.default_processors) + [ImageToTextProcessor])
    else:
        processors.append("marker.processors.image_to_text.ImageToTextProcessor")

    converter = PdfConverter(
        artifact_dict=create_model_dict(),
        config=config_parser.generate_config_dict(),
        processor_list=processors,
        renderer=config_parser.get_renderer(),
    )
    return converter
