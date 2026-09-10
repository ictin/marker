from typing import Annotated, List

from pydantic import BaseModel

from marker.processors.llm import BaseLLMSimpleBlockProcessor, PromptData, BlockData
from marker.schema import BlockTypes
from marker.schema.document import Document


class ImageToDescriptionProcessor(BaseLLMSimpleBlockProcessor):
    """Simple processor that replaces images with generated text."""

    block_types = (
        BlockTypes.Picture,
        BlockTypes.Figure,
    )

    extract_images: Annotated[bool, "Extract images from the document."] = True

    def inference_blocks(self, document: Document) -> List[BlockData]:
        blocks = super().inference_blocks(document)
        if self.extract_images:
            return []
        return blocks

    def block_prompts(self, document: Document) -> List[PromptData]:
        prompts = []
        for block_data in self.inference_blocks(document):
            block = block_data["block"]
            prompts.append(
                {
                    "prompt": "",
                    "image": self.extract_image(document, block),
                    "block": block,
                    "schema": ImageDescriptionSchema,
                    "page": block_data["page"],
                }
            )
        return prompts

    def rewrite_block(
        self, response: dict, prompt_data: PromptData, document: Document
    ):
        block = prompt_data["block"]
        image_name = block.id.to_path()
        description = f"This is the image {image_name}"
        block.html = f"<p>{description}</p>"


class ImageDescriptionSchema(BaseModel):
    description: str
