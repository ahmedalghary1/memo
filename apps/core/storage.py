from io import BytesIO
from pathlib import Path
import logging

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)


class WebPImageStorage(FileSystemStorage):
    """Store uploaded raster images as WebP while leaving WebP uploads intact."""

    quality = 82

    def _save(self, name, content):
        name_path = Path(name)
        if name_path.suffix.lower() == ".webp":
            return super()._save(name, content)

        try:
            content.seek(0)
            with Image.open(content) as source:
                try:
                    image = ImageOps.exif_transpose(source)
                except Exception:
                    image = source.copy() if hasattr(source, "copy") else source

                has_alpha = "A" in image.getbands() or "transparency" in image.info
                image = image.convert("RGBA" if has_alpha else "RGB")

                save_kwargs = {
                    "format": "WEBP",
                    "quality": self.quality,
                    "method": 6,
                }
                icc_profile = image.info.get("icc_profile")
                if icc_profile and isinstance(icc_profile, (bytes, bytearray)) and len(icc_profile) > 0:
                    save_kwargs["icc_profile"] = bytes(icc_profile)

                output = BytesIO()
                image.save(output, **save_kwargs)
                output.seek(0)

                webp_name = name_path.with_suffix(".webp").as_posix()
                return super()._save(webp_name, ContentFile(output.read()))
        except Exception as exc:
            logger.warning("Failed to convert uploaded image %s to WebP (%s). Saving original.", name, exc)
            content.seek(0)
            return super()._save(name, content)

