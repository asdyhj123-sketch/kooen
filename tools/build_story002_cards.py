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


def center_text(draw, text, y, size, fill=BLACK):
    f = font(size)
    box = draw.textbbox((0, 0), text, font=f)
    x = (W - (box[2] - box[0])) // 2
    draw.text((x, y), text, font=f, fill=fill)


def base_card():
    return Image.new("RGB", (W, H), "white")


def place_scene(canvas, source_name, crop_box, max_size, bottom=1770):
    scene = Image.open(SOURCE / source_name).convert("RGB").crop(crop_box)
    ratio = min(max_size[0] / scene.width, max_size[1] / scene.height)
    scene = scene.resize((round(scene.width * ratio), round(scene.height * ratio)), Image.Resampling.LANCZOS)
    x = (W - scene.width) // 2
    y = bottom - scene.height
    canvas.paste(scene, (x, y))


def add_footer(draw):
    center_text(draw, "@kooen.official", 1840, 22, GRAY)


def build_fixed_card(source_name, target_name):
    image = Image.open(SOURCE / source_name).convert("RGB")
    fit_cover(image).save(CARDS / target_name, quality=95)


def build_scene2():
    canvas = base_card()
    draw = ImageDraw.Draw(canvas)
    center_text(draw, "여행을 자주 다니는 편이라", 120, 63)
    center_text(draw, "속옷 파우치를 꼭 챙겨요", 205, 63, CORAL)
    place_scene(canvas, "02_여행준비_무문구.png", (45, 260, 1024, 1536), (1000, 1370))
    add_footer(draw)
    canvas.save(CARDS / "02_여행준비.png")


def build_scene3():
    canvas = base_card()
    draw = ImageDraw.Draw(canvas)
    center_text(draw, "그런데 브라 하나만 넣어도", 120, 63)
    center_text(draw, "파우치가 벌써 꽉—", 205, 72, CORAL)
    place_scene(canvas, "03_하나만넣어도_무문구.png", (165, 230, 920, 1425), (930, 1370))
    add_footer(draw)
    canvas.save(CARDS / "03_하나만넣어도.png")


def build_scene4():
    canvas = base_card()
    draw = ImageDraw.Draw(canvas)
    center_text(draw, "결국 꾸겨 넣어야 해서", 120, 68, CORAL)
    center_text(draw, "챙길 때마다 좀 그랬어요…", 210, 63)
    place_scene(canvas, "04_꾸겨넣기_무문구.png", (55, 240, 980, 1435), (1000, 1370))
    add_footer(draw)
    canvas.save(CARDS / "04_꾸겨넣기.png")


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
    build_fixed_card("01_사연도착_승인본.png", "01_표지.png")
    build_scene2()
    build_scene3()
    build_scene4()
    build_fixed_card("05_사연모집_승인본.png", "05_사연모집.png")
    build_review()
    build_downloads()


if __name__ == "__main__":
    main()
