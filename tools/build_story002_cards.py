from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("output/storytoon/2026-10-30/STORY-002_여행용-속옷파우치")
SOURCE = ROOT / "01_source"
CARDS = ROOT / "02_cards"
REVIEW = ROOT / "05_review"
DOWNLOADS = ROOT / "06_download"
FONT = Path("assets/fonts/Jua-Regular.ttf")

W, H = 1080, 1920
BLACK = "#111111"
CORAL = "#FF807A"
GRAY = "#9B9B9B"


def font(size):
    return ImageFont.truetype(str(FONT), size)


def fit_cover(image, size=(W, H)):
    ratio = max(size[0] / image.width, size[1] / image.height)
    resized = image.resize((round(image.width * ratio), round(image.height * ratio)), Image.Resampling.LANCZOS)
    left = (resized.width - size[0]) // 2
    top = (resized.height - size[1]) // 2
    return resized.crop((left, top, left + size[0], top + size[1]))


def base_card():
    return Image.new("RGB", (W, H), "white")


def place_scene(canvas, source_name, crop_box, max_size, bottom=1770):
    scene = Image.open(SOURCE / source_name).convert("RGB").crop(crop_box)
    ratio = min(max_size[0] / scene.width, max_size[1] / scene.height)
    scene = scene.resize((round(scene.width * ratio), round(scene.height * ratio)), Image.Resampling.LANCZOS)
    x = (W - scene.width) // 2
    y = bottom - scene.height
    canvas.paste(scene, (x, y))


def build_clean_card(source_name, target_name, crop_box, max_size, bottom=1770):
    canvas = base_card()
    place_scene(canvas, source_name, crop_box, max_size, bottom)
    canvas.save(CARDS / target_name)


def build_review():
    cards = sorted(CARDS.glob("*.png"))
    thumb_w = 270
    thumb_h = 480
    canvas = Image.new("RGB", (thumb_w * len(cards), thumb_h + 60), "#EEEEEE")
    draw = ImageDraw.Draw(canvas)
    label_font = font(20)
    for i, card_path in enumerate(cards):
        image = Image.open(card_path).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        canvas.paste(image, (i * thumb_w, 0))
        draw.text((i * thumb_w + 10, thumb_h + 15), card_path.stem, font=label_font, fill=BLACK)
    canvas.save(REVIEW / "STORY-002_전체검수.jpg", quality=92)


def build_downloads():
    for old in DOWNLOADS.glob("*.zip"):
        old.unlink()
    for card in sorted(CARDS.glob("*.png")):
        with ZipFile(DOWNLOADS / f"{card.stem}.zip", "w", ZIP_DEFLATED) as archive:
            archive.write(card, arcname=card.name)


def main():
    for directory in (CARDS, REVIEW, DOWNLOADS):
        directory.mkdir(parents=True, exist_ok=True)
    for old in CARDS.glob("*.png"):
        old.unlink()
    build_clean_card("01_사연도착_무문구.png", "01_표지.png", (175, 380, 855, 1470), (850, 1280), 1750)
    build_clean_card("02_여행준비_무문구.png", "02_여행준비.png", (45, 260, 1024, 1536), (1000, 1370))
    build_clean_card("03_하나만넣어도_무문구.png", "03_하나만넣어도.png", (165, 230, 920, 1425), (930, 1370))
    build_clean_card("04_꾸겨넣기_무문구.png", "04_꾸겨넣기.png", (55, 240, 980, 1435), (1000, 1370))
    build_clean_card("05_사연모집_무문구.png", "05_사연모집.png", (40, 390, 970, 1470), (1000, 1280), 1750)
    build_review()
    build_downloads()


if __name__ == "__main__":
    main()
