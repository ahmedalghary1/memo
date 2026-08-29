from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image, ImageOps


class Command(BaseCommand):
    help = "Create lightweight WebP variants without deleting original store images."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **options):
        jobs = [
            (settings.BASE_DIR / "static" / "images" / "memo-logo-transparent-v2.png", (384, 256)),
            (settings.BASE_DIR / "static" / "images" / "memo-campaign.png", (1672, 941)),
        ]
        for folder, size in (("products", (1200, 1500)), ("categories", (900, 900)), ("collections", (1600, 1000))):
            root = settings.MEDIA_ROOT / folder
            if root.exists():
                jobs.extend((path, size) for path in root.rglob("*") if path.suffix.lower() in {".png", ".jpg", ".jpeg"})

        converted = 0
        for source, max_size in jobs:
            destination = source.with_suffix(".webp")
            if destination.exists() and not options["force"] and destination.stat().st_mtime >= source.stat().st_mtime:
                continue
            with Image.open(source) as opened:
                image = ImageOps.exif_transpose(opened)
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                if image.mode not in {"RGB", "RGBA"}:
                    image = image.convert("RGBA" if "transparency" in image.info else "RGB")
                destination.parent.mkdir(parents=True, exist_ok=True)
                image.save(destination, "WEBP", quality=80, method=6)
            converted += 1
        self.stdout.write(self.style.SUCCESS(f"Created {converted} optimized WebP image(s)."))
