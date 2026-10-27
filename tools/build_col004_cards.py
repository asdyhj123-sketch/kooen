from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


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


CARD_TEXT = {
    "01_표지.png": "가슴 크면 공감하는\n순간들 4탄",
    "02_안전벨트.png": "안전벨트 위치가\n자꾸 애매해질 때",
    "03_크로스백.png": "크로스백 끈이 가슴 정가운데에\n껴서 안 나올 때",
    "04_프린트티.png": "프린트 그림이 가슴 부분만\n쭉 늘어날 때",
    "05_원피스허리선.png": "원피스 허리선이\n가슴 아래까지 올라올 때",
    "06_작은내장캡.png": "내장캡 옷의 컵이\n너무 작을 때",
    "07_마무리.png": "큰컵언니들은 어떤 순간이\n제일 공감돼요?",
}


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


def build_card(name: str, heading: str):
    image = Image.open(SOURCE / name).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(image)
    draw_heading(draw, heading)

    if name == "05_원피스허리선.png":
        draw_label(draw, "가슴 아래 허리선", (825, 1055), CORAL, CORAL)
        draw_label(draw, "원래 허리선", (780, 1275), GRAY, "#A8A8A8")

    image.save(CARDS / name, format="PNG", compress_level=6)


def main():
    CARDS.mkdir(parents=True, exist_ok=True)
    for name, heading in CARD_TEXT.items():
        build_card(name, heading)


if __name__ == "__main__":
    main()
