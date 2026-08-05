"""Image Provider Abstractions."""

import logging
import os
from abc import ABC, abstractmethod
from typing import Tuple
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


class BaseImageProvider(ABC):
    """Abstract base class for providing images to the renderer."""
    
    @abstractmethod
    def generate_image(self, prompt: str, dimensions: Tuple[int, int], output_path: str) -> str:
        """Generate an image and save it to the output path. Returns the path."""
        pass


class MockImageProvider(BaseImageProvider):
    """Returns a deterministic, simple colored background for tests."""
    
    def generate_image(self, prompt: str, dimensions: Tuple[int, int], output_path: str) -> str:
        logger.info(f"Mocking image generation for prompt: {prompt}")
        # Create a simple blue image
        img = Image.new('RGB', dimensions, color=(73, 109, 137))
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), f"Mock Image\nPrompt: {prompt[:30]}...", fill=(255, 255, 0))
        img.save(output_path)
        return output_path


class OpenAIImageProvider(BaseImageProvider):
    """Uses OpenAI's DALL-E to generate images."""
    
    def generate_image(self, prompt: str, dimensions: Tuple[int, int], output_path: str) -> str:
        # Check for API key
        if not os.environ.get("OPENAI_API_KEY"):
            logger.warning("No OPENAI_API_KEY found, falling back to Mock provider.")
            return MockImageProvider().generate_image(prompt, dimensions, output_path)
            
        import requests
        from openai import OpenAI
        
        client = OpenAI()
        # DALL-E 3 supports 1024x1024. For 1080x1350, it needs resizing or using DALL-E 2.
        # We will request 1024x1024 and let Pillow crop/resize it later.
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        img_data = requests.get(image_url).content
        with open(output_path, 'wb') as handler:
            handler.write(img_data)
            
        return output_path


class GeminiImageProvider(BaseImageProvider):
    """Uses Google Gemini to generate images."""
    
    def generate_image(self, prompt: str, dimensions: Tuple[int, int], output_path: str) -> str:
        # Check for API key
        if not os.environ.get("GEMINI_API_KEY"):
            logger.warning("No GEMINI_API_KEY found, falling back to Mock provider.")
            return MockImageProvider().generate_image(prompt, dimensions, output_path)
            
        # TODO: Implement Gemini Imagen 3 integration when SDK supports it.
        # For now, fallback to Mock.
        return MockImageProvider().generate_image(prompt, dimensions, output_path)


class ManualImageRequestProvider(BaseImageProvider):
    """Placeholder for manual request flow via Telegram."""
    
    def generate_image(self, prompt: str, dimensions: Tuple[int, int], output_path: str) -> str:
        logger.warning(f"Manual image requested for prompt: {prompt}")
        return MockImageProvider().generate_image(prompt, dimensions, output_path)


def get_image_provider(provider_type: str = "mock") -> BaseImageProvider:
    """Factory for getting the configured image provider."""
    providers = {
        "mock": MockImageProvider,
        "openai": OpenAIImageProvider,
        "gemini": GeminiImageProvider,
        "manual": ManualImageRequestProvider
    }
    return providers.get(provider_type.lower(), MockImageProvider)()
