"""Download Arabic + Latin fonts for PDF rendering into backend/assets/fonts.

Idempotent: skips files that already exist with non-zero size.
Fonts: Noto Sans Arabic, Noto Naskh Arabic (headings fallback), Inter.
All under OFL license.
"""

from pathlib import Path

import requests
from django.core.management.base import BaseCommand
from django.conf import settings

FONTS = {
    "NotoSansArabic-Regular.ttf": "https://github.com/notofonts/notofonts.github.io/raw/main/fonts/NotoSansArabic/hinted/ttf/NotoSansArabic-Regular.ttf",
    "NotoSansArabic-Bold.ttf": "https://github.com/notofonts/notofonts.github.io/raw/main/fonts/NotoSansArabic/hinted/ttf/NotoSansArabic-Bold.ttf",
    "Inter-Regular.ttf": "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Regular.woff2",
    "Inter-Bold.ttf": "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Bold.woff2",
}

FONTS_CSS = """/* Font faces for WeasyPrint PDF rendering */
@font-face {{
    font-family: 'Noto Sans Arabic';
    src: url('NotoSansArabic-Regular.ttf');
    font-weight: normal;
}}
@font-face {{
    font-family: 'Noto Sans Arabic';
    src: url('NotoSansArabic-Bold.ttf');
    font-weight: bold;
}}
"""


class Command(BaseCommand):
    help = "Download PDF fonts (Noto Sans Arabic + Inter) into backend/assets/fonts."

    def handle(self, *args, **options):
        fonts_dir = Path(settings.BASE_DIR) / "assets" / "fonts"
        fonts_dir.mkdir(parents=True, exist_ok=True)

        for filename, url in FONTS.items():
            target = fonts_dir / filename
            if target.exists() and target.stat().st_size > 0:
                self.stdout.write(f"exists: {filename}")
                continue
            self.stdout.write(f"downloading: {filename} ...")
            try:
                r = requests.get(url, timeout=60)
                r.raise_for_status()
                target.write_bytes(r.content)
                self.stdout.write(self.style.SUCCESS(f"ok: {filename} ({len(r.content)} bytes)"))
            except requests.RequestException as exc:
                self.stdout.write(self.style.WARNING(f"FAILED: {filename}: {exc}"))

        css_path = fonts_dir / "fonts.css"
        css_path.write_text(FONTS_CSS.format(), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS("fonts.css written"))
        self.stdout.write("Note: Arabic PDF requires NotoSansArabic-Regular/Bold.ttf to be present.")
