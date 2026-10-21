#!/usr/bin/env python3
from pathlib import Path
from shutil import copy2

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "collection" / "2026-10-21" / "COL-001_브라-관리-습관"
SRC = OUT / "01_source"
CARDS = OUT / "02_cards"
FONT = ROOT / "assets" / "fonts" / "Jua-Regular.ttf"

IMAGES = [
    Path("/workspace/generated_images/exec-cbadd04a-640a-4a96-b951-3d013e9ba898.png"),
    Path("/workspace/generated_images/exec-2ee84c56-05c2-47ea-83dd-c01957cef04c.png"),
    Path("/workspace/generated_images/exec-a5e73260-d19d-43f9-b0c3-54e4a0d89be2.png"),
    Path("/workspace/generated_images/exec-d2fad506-9cc4-44ff-9eab-8fc23e5e5c1b.png"),
    Path("/workspace/generated_images/exec-adb41417-dc46-44fa-9413-72e232c6a3b1.png"),
    Path("/workspace/generated_images/exec-28c4fb28-5b6d-464d-a9a4-2966e7c4ae3c.png"),
]

BLACK = "#111111"
PINK = "#F8B8BB"
DEEP_PINK = "#C95866"
WHITE = "#FFFFFF"


def font(size: int):
    return ImageFont.truetype(str(FONT), size)


def centered(draw, text, y, fnt, fill=BLACK, x0=45, x1=896, stroke=0, stroke_fill=None):
    box = draw.textbbox((0, 0), text, font=fnt, stroke_width=stroke)
    x = (x0 + x1 - (box[2] - box[0])) / 2
    draw.text((x, y), text, font=fnt, fill=fill, stroke_width=stroke,
              stroke_fill=stroke_fill or fill)


def pill(draw, text, y):
    fnt = font(38)
    box = draw.textbbox((0, 0), text, font=fnt)
    w = box[2] - box[0] + 50
    x = (941 - w) / 2
    draw.rounded_rectangle((x, y, x + w, y + 58), radius=29, fill="#FCE1E2")
    centered(draw, text, y + 7, fnt, DEEP_PINK)


def cover(im):
    d = ImageDraw.Draw(im)
    f = font(67)
    left, number, right = "브라사전", "6", "브라 관리법"
    gap = 18
    lbox = d.textbbox((0, 0), left, font=f)
    rbox = d.textbbox((0, 0), right, font=f)
    lw, rw = lbox[2] - lbox[0], rbox[2] - rbox[0]
    circle = 92
    total = lw + gap + circle + gap + rw
    x = (941 - total) / 2
    d.text((x, 150), left, font=f, fill=BLACK)
    cx = x + lw + gap
    d.ellipse((cx, 141, cx + circle, 233), fill=PINK, outline=BLACK, width=3)
    nbox = d.textbbox((0, 0), number, font=font(69))
    d.text((cx + (circle - (nbox[2]-nbox[0]))/2, 148), number, font=font(69), fill=BLACK)
    d.text((cx + circle + gap, 150), right, font=f, fill=BLACK)
    centered(d, "브라 오래 입으려면", 900, font(48), WHITE, x0=440, x1=890)
    centered(d, "이 5가지는 피해주세요", 968, font(45), WHITE, x0=435, x1=895)


def standard(im, idx, title, sub, note=None, footer=None):
    d = ImageDraw.Draw(im)
    pill(d, f"관리 습관 {idx}", 110)
    size = 64
    while size > 42 and d.textbbox((0, 0), title, font=font(size))[2] > 850:
        size -= 2
    centered(d, title, 205, font(size), BLACK)
    centered(d, sub, 315, font(40), DEEP_PINK)
    if note:
        centered(d, note, 380, font(31), BLACK)
    if footer:
        box = (65, 1515, 876, 1600)
        d.rounded_rectangle(box, radius=30, fill="#FFF1F1")
        centered(d, footer, 1534, font(31), BLACK, x0=75, x1=866)


def main():
    SRC.mkdir(parents=True, exist_ok=True)
    CARDS.mkdir(parents=True, exist_ok=True)
    for i, src in enumerate(IMAGES, 1):
        copy2(src, SRC / f"{i:02d}_base.png")

    cards = []
    im = Image.open(IMAGES[0]).convert("RGB")
    cover(im)
    cards.append(im)

    specs = [
        (1, "뜨거운 물로 세탁하기", "미지근한 물이나 찬물, 케어라벨부터 확인", None, None),
        (2, "락스 같은 표백제 쓰기", "락스 계열이 염소계 표백제예요", "피죤은 보통 섬유유연제라 다른 종류예요", None),
        (3, "비틀어 꽉 짜기", "수건으로 톡톡 눌러 물기를 빼주세요", None, None),
        (4, "건조기, 뜨거운 바람 쓰기", "모양을 잡아 그늘에서 자연 건조", None, None),
        (5, "몰드컵을 눌러 보관하기", "컵 모양 그대로 포개어 보관", None,
         "소재마다 달라요. 제품 케어라벨이 가장 먼저!"),
    ]
    for src, spec in zip(IMAGES[1:], specs):
        im = Image.open(src).convert("RGB")
        standard(im, *spec)
        cards.append(im)

    for i, im in enumerate(cards, 1):
        im.save(CARDS / f"{i:02d}.png", quality=95)


if __name__ == "__main__":
    main()
