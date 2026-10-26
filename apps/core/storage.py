from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from PIL import Image, ImageOps


class WebPImageStorage(FileSystemStorage):
    """Store uploaded raster images as WebP while leaving WebP uploads intact."""

    quality = 82

    def _save(self, name, content):
        if Path(name).suffix.lower() == ".webp":
            return super()._save(name, content)

        try:
            content.seek(0)
            with Image.open(content) as source:
                image = ImageOps.exif_transpose(source)
                icc_profile = image.info.get("icc_profile")
                has_alpha = "A" in image.getbands() or "transparency" in image.info
                image = image.convert("RGBA" if has_alpha else "RGB")
                output = BytesIO()
                image.save(
                    output,
                    format="WEBP",
                    quality=self.quality,
                    method=6,
                    icc_profile=icc_profile,
                )
        except (OSError, ValueError) as exc:
            raise ValueError("Uploaded image could not be converted to WebP.") from exc

        output.seek(0)
        webp_name = str(Path(name).with_suffix(".webp"))
        return super()._save(webp_name, ContentFile(output.read()))
