from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path("output/collection/2026-10-26/COL-003_올바른-브라-세탁법")
SRC = ROOT / "01_source"
OUT = ROOT / "02_cards"
FONT_PATH = Path("assets/fonts/Jua-Regular.ttf")

BLACK = "#111111"
PINK = "#FF6668"
PALE_PINK = "#FFD5D5"


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size)


def centered(draw: ImageDraw.ImageDraw, text: str, y: int, fnt, fill=BLACK, spacing=8):
    box = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=spacing, align="center")
    w = box[2] - box[0]
    stroke = 2 if getattr(fnt, "size", 0) >= 70 else 1
    draw.multiline_text(
        ((941 - w) / 2, y), text, font=fnt, fill=fill, spacing=spacing, align="center",
        stroke_width=stroke, stroke_fill=fill,
    )


def pill(draw: ImageDraw.ImageDraw, text: str, y: int, fnt=None):
    fnt = fnt or font(58)
    box = draw.textbbox((0, 0), text, font=fnt)
    w, h = box[2] - box[0], box[3] - box[1]
    x = (941 - w) / 2
    draw.rounded_rectangle((x - 28, y - 10, x + w + 28, y + h + 15), radius=30, fill=PALE_PINK)
    draw.text((x, y), text, font=fnt, fill=BLACK, stroke_width=1, stroke_fill=BLACK)


def highlighted(draw: ImageDraw.ImageDraw, text: str, y: int, fnt, fill=BLACK):
    box = draw.textbbox((0, 0), text, font=fnt)
    w, h = box[2] - box[0], box[3] - box[1]
    x = (941 - w) / 2
    draw.rounded_rectangle((x - 22, y + 4, x + w + 22, y + h + 11), radius=24, fill=PALE_PINK)
    stroke = 2 if getattr(fnt, "size", 0) >= 70 else 1
    draw.text((x, y), text, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=fill)


def add_text(src_name: str, out_name: str, badge: str | None, title: str, subtitle: str = "", title_size=78):
    im = Image.open(SRC / src_name).convert("RGB")
    im = im.resize((941, 1672), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(im)
    if badge:
        pill(draw, badge, 70)
        title_y = 175
    else:
        title_y = 105
    centered(draw, title, title_y, font(title_size), BLACK, 10)
    if subtitle:
        title_box = draw.multiline_textbbox((0, 0), title, font=font(title_size), spacing=10, align="center")
        title_h = title_box[3] - title_box[1]
        sub_y = title_y + title_h + 30
        lines = subtitle.split("\n")
        sub_font = font(45)
        if len(lines) == 1:
            highlighted(draw, lines[0], sub_y, sub_font)
        else:
            centered(draw, lines[0], sub_y, sub_font, BLACK)
            highlighted(draw, lines[1], sub_y + 56, sub_font)
    im.save(OUT / out_name, quality=100)


def cover():
    im = Image.open(SRC / "01_base.png").convert("RGB").resize((941, 1672), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(im)
    centered(draw, "브라사전", 58, font(58))
    cx, cy, r = 638, 93, 52
    draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=PALE_PINK)
    box = draw.textbbox((0, 0), "9", font=font(68))
    draw.text(
        (cx-(box[2]-box[0])/2, cy-(box[3]-box[1])/2-5), "9",
        font=font(68), fill=BLACK, stroke_width=1, stroke_fill=BLACK,
    )
    centered(draw, "올바른 브라", 170, font(103), BLACK)
    highlighted(draw, "세탁 방법", 285, font(103))
    im.save(OUT / "01_표지.png", quality=100)


def closing():
    im = Image.open(SRC / "07_base.png").convert("RGB").resize((941, 1672), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(im)
    highlighted(draw, "큰컵언니들", 55, font(57), BLACK)
    centered(draw, "되도록 손세탁하고", 145, font(79), BLACK)
    centered(draw, "세탁기를 쓸 때는", 250, font(83), PINK)
    centered(draw, "라벨과 세탁망 확인!", 355, font(76), BLACK)
    centered(draw, "저장해두고 세탁할 때 다시 봐요", 485, font(43), PINK)
    im.save(OUT / "07_저장유도.png", quality=100)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cover()
    add_text("02_base.png", "02_기본원칙.png", "기본 원칙", "브라는 되도록\n손세탁을 권장해요", "세탁 전 제품의 케어라벨을\n먼저 확인해주세요", 79)
    add_text("03_base.png", "03_손세탁1_중성세제.png", "손세탁 1단계", "미지근한 물에\n중성세제를 풀어주세요", "울샴푸처럼 제품에 '중성'이라고\n표시된 세제를 사용해요", 76)
    add_text("04_base.png", "04_손세탁2_눌러세탁.png", "손세탁 2단계", "문지르거나 비틀지 말고\n부드럽게 눌러 세탁해요", "헹군 뒤 마른 수건으로 감싸\n물기를 눌러주세요", 70)
    add_text("05_base.png", "05_세탁기사용시.png", "세탁기 사용 시", "케어라벨에서\n사용 가능 여부를 확인해요", "후크를 잠그고 세탁망에 넣어\n찬물·섬세 코스로 세탁해요", 72)
    add_text("06_base.png", "06_건조시.png", "건조 시", "컵 모양을 정리해\n그늘에서 자연 건조해요", "건조기와 뜨거운 바람은 피해주세요", 74)
    closing()


if __name__ == "__main__":
    main()
