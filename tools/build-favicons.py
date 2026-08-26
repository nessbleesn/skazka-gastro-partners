from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "assets" / "images"
MASTER = IMAGES / "favicon-master.png"


def prepare_master() -> Image.Image:
    image = Image.open(MASTER).convert("RGBA")
    mask = Image.new("L", image.size, 0)
    radius = round(image.width * 0.19)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, image.width - 1, image.height - 1), radius=radius, fill=255)
    image.putalpha(mask)
    return image


def resized(image: Image.Image, size: int) -> Image.Image:
    result = image.resize((size, size), Image.Resampling.LANCZOS)
    if size <= 48:
        result = result.filter(ImageFilter.UnsharpMask(radius=0.55, percent=115, threshold=2))
    return result


master = prepare_master()
for size in (16, 32, 180, 192, 512):
    name = "apple-touch-icon.png" if size == 180 else f"favicon-{size}.png"
    resized(master, size).save(IMAGES / name, optimize=True)

resized(master, 256).save(
    ROOT / "favicon.ico",
    format="ICO",
    sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
