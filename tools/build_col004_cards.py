from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path("output/collection/2026-10-27/COL-004_가슴크면-공감하는-순간들-4")
SOURCE = ROOT / "01_source"
CARDS = ROOT / "02_cards"
FONT_PATH = Path("assets/fonts/Jua-Regular.ttf")

WIDTH = 1080
HEIGHT = 1920
BLACK = "#050505"
CORAL = "#FF6F70"
GRAY = "#777777"
PALE_PINK = "#FFE0E0"
SHOW_TEXT = False


CARD_TEXT = {
    "01_표지.png": "가슴 크면 공감하는\n순간들 4탄",
    "02_안전벨트.png": "안전벨트 위치가\n자꾸 애매해질 때",
    "03_크로스백.png": "크로스백 끈이 가슴 정가운데에\n껴서 안 나올 때",
    "04_프린트티.png": "프린트 그림이 가슴 부분만\n쭉 늘어날 때",
    "05_원피스허리선.png": "원피스 허리선이\n가슴 아래까지 올라올 때",
    "06_작은내장캡.png": "내장캡 옷의 컵이\n너무 작을 때",
    "07_마무리.png": "큰컵언니들은 어떤 순간이\n제일 공감돼요?",
}

ACTIVE_CARDS = [
    ("02_안전벨트.png", "01_안전벨트.png"),
    ("03_크로스백.png", "02_크로스백.png"),
    ("04_프린트티.png", "03_프린트티.png"),
    ("05_원피스허리선.png", "04_원피스허리선.png"),
    ("06_작은내장캡.png", "05_작은내장캡.png"),
]


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size)


def fitted_font(draw: ImageDraw.ImageDraw, text: str, start_size: int, max_width: int):
    size = start_size
    while size > 44:
        fnt = font(size)
        widest = max(draw.textbbox((0, 0), line, font=fnt)[2] for line in text.split("\n"))
        if widest <= max_width:
            return fnt
        size -= 2
    return font(size)


def draw_heading(draw: ImageDraw.ImageDraw, text: str):
    fnt = fitted_font(draw, text, 76, 940)
    spacing = round(fnt.size * 0.16)
    box = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=spacing, align="center")
    width = box[2] - box[0]
    x = (WIDTH - width) / 2
    draw.multiline_text((x, 82), text, font=fnt, fill=BLACK, spacing=spacing, align="center")


def draw_label(draw: ImageDraw.ImageDraw, text: str, center, fill, outline):
    fnt = font(34)
    box = draw.textbbox((0, 0), text, font=fnt)
    w = box[2] - box[0]
    h = box[3] - box[1]
    x = center[0] - w / 2
    y = center[1] - h / 2
    pad_x, pad_y = 16, 10
    draw.rounded_rectangle(
        (x - pad_x, y - pad_y, x + w + pad_x, y + h + pad_y),
        radius=18,
        fill="#FFFFFF",
        outline=outline,
        width=3,
    )
    draw.text((x, y), text, font=fnt, fill=fill)


def content_bbox(image: Image.Image):
    background = Image.new("RGB", image.size, "white")
    difference = ImageChops.difference(image, background).convert("L")
    mask = difference.point(lambda value: 255 if value > 10 else 0)
    bbox = mask.getbbox()
    if not bbox:
        return (0, 0, image.width, image.height)
    left, top, right, bottom = bbox
    margin = 24
    return (
        max(0, left - margin),
        max(0, top - margin),
        min(image.width, right + margin),
        min(image.height, bottom + margin),
    )


def draw_arrow(draw: ImageDraw.ImageDraw, start, end, fill=CORAL, width=6):
    draw.line((start, end), fill=fill, width=width)
    ex, ey = end
    draw.polygon([(ex, ey), (ex - 13, ey - 24), (ex + 14, ey - 18)], fill=fill)


def build_card(source_name: str, output_name: str):
    source = Image.open(SOURCE / source_name).convert("RGB")

    if source_name == "05_원피스허리선.png":
        source_draw = ImageDraw.Draw(source)
        draw_label(source_draw, "허리선", (755, 860), CORAL, CORAL)
        draw_arrow(source_draw, (710, 905), (645, 1000), CORAL, 6)

    crop = source.crop(content_bbox(source))
    crop.thumbnail((980, 1370), Image.Resampling.LANCZOS)
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    art_top = 430 + (1370 - crop.height) // 2
    image.paste(crop, ((WIDTH - crop.width) // 2, art_top))

    if SHOW_TEXT:
        draw = ImageDraw.Draw(image)
        draw_heading(draw, CARD_TEXT[source_name])

    image.save(CARDS / output_name, format="PNG", compress_level=6)


def main():
    CARDS.mkdir(parents=True, exist_ok=True)
    for old_card in CARDS.glob("*.png"):
        old_card.unlink()
    for source_name, output_name in ACTIVE_CARDS:
        build_card(source_name, output_name)


if __name__ == "__main__":
    main()
