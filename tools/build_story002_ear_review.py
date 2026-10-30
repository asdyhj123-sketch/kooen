from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("output/storytoon/2026-10-30/STORY-002_여행용-속옷파우치")
SOURCE = ROOT / "01_source" / "ear_fix"
CARDS = ROOT / "02_귀수정_검수"
REVIEW = ROOT / "05_review"
DOWNLOADS = ROOT / "06_download" / "귀수정_4컷"
FONT = Path("assets/fonts/Jua-Regular.ttf")
W, H = 1080, 1920


ITEMS = [
    ("01_가득찬파우치_귀수정_무문구.png", "01_가득찬파우치_귀수정.png", (145, 180, 900, 1420), (930, 1370), 1760),
    ("02_큰파우치꾸겨넣기_귀수정_무문구.png", "02_큰파우치꾸겨넣기_귀수정.png", (60, 220, 990, 1450), (1000, 1370), 1770),
    ("03_작은파우치눌러담기_귀수정_무문구.png", "03_작은파우치눌러담기_귀수정.png", (145, 180, 880, 1400), (930, 1370), 1760),
    ("04_파우치브라비교_귀수정_무문구.png", "04_파우치브라비교_귀수정.png", (35, 315, 990, 1470), (1000, 1370), 1770),
]


def place(source_name, target_name, crop_box, max_size, bottom):
    canvas = Image.new("RGB", (W, H), "white")
    image = Image.open(SOURCE / source_name).convert("RGB").crop(crop_box)
    ratio = min(max_size[0] / image.width, max_size[1] / image.height)
    image = image.resize((round(image.width * ratio), round(image.height * ratio)), Image.Resampling.LANCZOS)
    canvas.paste(image, ((W - image.width) // 2, bottom - image.height))
    canvas.save(CARDS / target_name)


def build_review():
    cards = sorted(CARDS.glob("*.png"))
    tw, th = 270, 480
    canvas = Image.new("RGB", (tw * len(cards), th + 60), "#EEEEEE")
    draw = ImageDraw.Draw(canvas)
    label_font = ImageFont.truetype(str(FONT), 19)
    for i, card in enumerate(cards):
        thumb = Image.open(card).convert("RGB").resize((tw, th), Image.Resampling.LANCZOS)
        canvas.paste(thumb, (i * tw, 0))
        draw.text((i * tw + 8, th + 15), card.stem, font=label_font, fill="#111111")
    canvas.save(REVIEW / "STORY-002_귀수정4컷_검수.jpg", quality=92)


def build_downloads():
    for old in DOWNLOADS.glob("*.zip"):
        old.unlink()
    for card in sorted(CARDS.glob("*.png")):
        with ZipFile(DOWNLOADS / f"{card.stem}.zip", "w", ZIP_DEFLATED) as archive:
            archive.write(card, arcname=card.name)


def main():
    for directory in (SOURCE, CARDS, REVIEW, DOWNLOADS):
        directory.mkdir(parents=True, exist_ok=True)
    for old in CARDS.glob("*.png"):
        old.unlink()
    for item in ITEMS:
        place(*item)
    build_review()
    build_downloads()


if __name__ == "__main__":
    main()
