from __future__ import annotations

import json
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path("output/collection/2026-10-28/COL-005_브라사전10-브라용어번역집")
SOURCE = ROOT / "01_source"
CARDS = ROOT / "02_cards"
REVIEW = ROOT / "05_review"
CAPTION = ROOT / "04_caption"
FONT_PATH = Path("assets/fonts/Jua-Regular.ttf")
CUPBUNNY = Path("assets/cupbunny")
BRA_PATH = Path("assets/bras/3분의4컵_투명.png")
PLAN_PATH = Path("output/planning/2026-10-28_브라사전10-상세페이지용어번역집.md")

WIDTH = 1080
HEIGHT = 1920
BLACK = "#050505"
DARK = "#3A3A3A"
GRAY = "#6E6E6E"
PINK = "#F9CEC3"
PALE_PINK = "#FFF0EF"
CORAL = "#FF7478"
GREEN = "#315C45"
BROWN = "#B8845A"


CARDS_DATA = [
    {
        "file": "01_표지.png",
        "kind": "cover",
    },
    {
        "file": "02_몰드컵.png",
        "kind": "mold",
        "term": "몰드컵",
        "definition": "열로 모양을 잡은 컵",
        "meta": "예: 티셔츠 브라",
        "point": "몰드의 깊이와 내 가슴 모양이\n맞는지가 중요해요",
    },
    {
        "file": "03_재단컵.png",
        "kind": "cutsew",
        "term": "재단컵",
        "definition": "원단 조각을 이어 만든 컵",
        "meta": "예: 3피스컵, 절개선이 있는 풀컵 브라",
        "point": "절개선 방향에 따라 모아주는 모양과\n지지감이 달라져요",
    },
    {
        "file": "04_홑겹.png",
        "kind": "unlined",
        "term": "홑겹",
        "definition": "패드 없이 원단만으로 만든 컵",
        "meta": "예: 레이스 홑겹 브라, 메시 홑겹 브라",
        "point": "볼륨을 더하지 않아 가볍지만\n원단과 절개선의 지지력을 함께 봐야 해요",
        "detail": "레이스·메시 원단 자체가\n컵 모양을 만들어요",
        "footnote": "참고: 재단컵이면서 홑겹일 수도 있어요",
    },
    {
        "file": "05_중심고어.png",
        "kind": "gore",
        "term": "중심고어",
        "definition": "양쪽 컵 사이 가운데 부분",
        "meta": "위치: 양쪽 컵 사이 가슴뼈 앞",
        "point": "와이어 브라는 가운데 들뜸으로\n컵 용량과 모양 궁합을 확인할 수 있어요",
    },
    {
        "file": "06_옆날개.png",
        "kind": "wing",
        "term": "옆날개",
        "definition": "컵 옆에서 등까지 감싸는 부분",
        "meta": "위치: 컵 옆에서 등 후크까지",
        "point": "넓고 탄탄한 옆날개는 가슴의 무게를\n몸통으로 나누는 데 도움을 줘요",
        "diagram_note": "후크를 풀어 좌우로 펼친 모습",
    },
    {
        "file": "07_사이드본.png",
        "kind": "sidebone",
        "term": "사이드본",
        "definition": "옆날개 안의 세로 지지대",
        "meta": "위치: 겨드랑이 아래 옆날개 안쪽",
        "point": "옆날개가 접히거나 말리지 않게\n잡아주는 역할이 중요해요",
        "diagram_note": "후크를 풀어 좌우로 펼친 모습",
    },
    {
        "file": "08_저장CTA.png",
        "kind": "cta",
    },
]


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size)


def text_width(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> int:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0]


def fit_font(draw: ImageDraw.ImageDraw, text: str, start: int, max_width: int, minimum: int = 28):
    size = start
    while size > minimum:
        fnt = font(size)
        if max(text_width(draw, line, fnt) for line in text.split("\n")) <= max_width:
            return fnt
        size -= 2
    return font(size)


def draw_centered(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    size: int,
    color: str = BLACK,
    max_width: int = 940,
    spacing: int | None = None,
):
    fnt = fit_font(draw, text, size, max_width)
    if spacing is None:
        spacing = max(6, round(fnt.size * 0.12))
    box = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=spacing, align="center")
    w = box[2] - box[0]
    draw.multiline_text(((WIDTH - w) / 2, y), text, font=fnt, fill=color, spacing=spacing, align="center")
    return fnt


def paste_contain(canvas: Image.Image, asset: Image.Image, box: tuple[int, int, int, int]):
    x1, y1, x2, y2 = box
    item = asset.copy().convert("RGBA")
    item.thumbnail((x2 - x1, y2 - y1), Image.Resampling.LANCZOS)
    x = x1 + (x2 - x1 - item.width) // 2
    y = y1 + (y2 - y1 - item.height) // 2
    canvas.alpha_composite(item, (x, y))
    return x, y, item.width, item.height


def draw_heart(draw: ImageDraw.ImageDraw, center: tuple[int, int], size: int, fill: str = CORAL):
    cx, cy = center
    r = size // 4
    draw.ellipse((cx - 2 * r, cy - r, cx, cy + r), fill=fill)
    draw.ellipse((cx, cy - r, cx + 2 * r, cy + r), fill=fill)
    draw.polygon([(cx - 2 * r, cy), (cx + 2 * r, cy), (cx, cy + 3 * r)], fill=fill)


def draw_save_icon(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=30, fill=PALE_PINK, outline=CORAL, width=8)
    pad = 42
    draw.line((x1 + pad, y1 + pad, x1 + pad, y2 - pad), fill=CORAL, width=16)
    draw.line((x2 - pad, y1 + pad, x2 - pad, y2 - pad), fill=CORAL, width=16)
    draw.line((x1 + pad, y1 + pad, x2 - pad, y1 + pad), fill=CORAL, width=16)
    draw.line((x1 + pad, y2 - pad, (x1 + x2) // 2, y2 - 92), fill=CORAL, width=16)
    draw.line(((x1 + x2) // 2, y2 - 92, x2 - pad, y2 - pad), fill=CORAL, width=16)


def bra_asset(size: int = 620) -> Image.Image:
    bra = Image.open(BRA_PATH).convert("RGBA")
    bra.thumbnail((size, size), Image.Resampling.LANCZOS)
    return bra


def tint_asset(asset: Image.Image, color: tuple[int, int, int], strength: float) -> Image.Image:
    base = asset.copy().convert("RGBA")
    overlay = Image.new("RGBA", base.size, (*color, 255))
    mixed = Image.blend(base, overlay, strength)
    mixed.putalpha(base.getchannel("A"))
    return mixed


def draw_bra_and_bunny(base: Image.Image, kind: str):
    draw = ImageDraw.Draw(base)
    bunny = Image.open(CUPBUNNY / "설명.png").convert("RGBA")

    if kind in {"wing", "sidebone"}:
        # Complete front bra with wide side wings and a visible hook end.
        left_wing = [(310, 770), (92, 725), (72, 975), (345, 1030)]
        right_wing = [(770, 770), (990, 725), (1010, 975), (735, 1030)]
        draw.polygon(left_wing, fill="#F3D2C3", outline=DARK)
        draw.polygon(right_wing, fill="#F3D2C3", outline=DARK)
        # Clearly separated hook-and-eye ends: hooks on the left, eyes on the right.
        draw.rectangle((72, 760, 112, 940), fill="#E7BDAA", outline=DARK, width=4)
        draw.rectangle((968, 760, 1010, 940), fill="#E7BDAA", outline=DARK, width=4)
        for hy in (790, 850, 910):
            draw.arc((76, hy - 10, 108, hy + 12), 70, 290, fill=DARK, width=4)
            draw.ellipse((980, hy - 9, 998, hy + 9), outline=DARK, width=4)

        full_bra = bra_asset(660)
        paste_contain(base, full_bra, (210, 500, 880, 1160))

        if kind == "wing":
            overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            od.polygon(left_wing, fill=(255, 116, 120, 105))
            od.polygon(right_wing, fill=(255, 116, 120, 105))
            base.alpha_composite(overlay)
            draw = ImageDraw.Draw(base)
            draw.line((175, 650, 190, 745), fill=CORAL, width=7)
            draw.polygon([(190, 745), (171, 715), (203, 711)], fill=CORAL)
            draw.line((905, 650, 890, 745), fill=CORAL, width=7)
            draw.polygon([(890, 745), (877, 710), (909, 716)], fill=CORAL)
        else:
            draw.rounded_rectangle((785, 765, 827, 1000), radius=16, fill=CORAL, outline=DARK, width=5)
            draw.line((806, 690, 806, 748), fill=CORAL, width=7)
            draw.polygon([(806, 748), (790, 716), (822, 716)], fill=CORAL)
        paste_contain(base, bunny, (20, 1030, 300, 1360))
        return

    paste_contain(base, bunny, (25, 820, 335, 1300))
    bra = bra_asset(660)

    if kind == "unlined":
        bra = tint_asset(bra, (255, 218, 221), 0.33)
        pattern = Image.new("RGBA", bra.size, (0, 0, 0, 0))
        pd = ImageDraw.Draw(pattern)
        # Sparse floral lace cue. It is clipped to the bra silhouette below.
        for py in range(210, bra.height - 80, 70):
            for px in range(70 + (py // 70 % 2) * 35, bra.width - 50, 80):
                petal = 9
                for dx, dy in ((-10, 0), (10, 0), (0, -10), (0, 10)):
                    pd.ellipse(
                        (px + dx - petal, py + dy - petal, px + dx + petal, py + dy + petal),
                        outline=(255, 116, 120, 125),
                        width=3,
                    )
                pd.ellipse((px - 5, py - 5, px + 5, py + 5), fill=(255, 116, 120, 100))
        clipped_alpha = ImageChops.multiply(pattern.getchannel("A"), bra.getchannel("A"))
        pattern.putalpha(clipped_alpha)
        bra.alpha_composite(pattern)

    x, y, w, h = paste_contain(base, bra, (330, 505, 1040, 1235))
    diagram = ImageDraw.Draw(base)

    if kind == "cutsew":
        # Three-piece cup seam guides.
        for side in (0, 1):
            cx = x + int(w * (0.29 if side == 0 else 0.71))
            diagram.line((cx, y + int(h * 0.82), cx, y + int(h * 0.48)), fill=CORAL, width=7)
            dx = -1 if side == 0 else 1
            diagram.line((cx, y + int(h * 0.65), cx + dx * int(w * 0.18), y + int(h * 0.46)), fill=CORAL, width=7)
    elif kind == "gore":
        gx = x + w // 2
        gy = y + int(h * 0.69)
        diagram.rounded_rectangle((gx - 35, gy - 95, gx + 35, gy + 70), radius=22, fill=CORAL, outline=DARK, width=4)
        diagram.line((gx, gy + 110, gx, gy + 165), fill=CORAL, width=6)
        diagram.polygon([(gx, gy + 165), (gx - 15, gy + 135), (gx + 15, gy + 135)], fill=CORAL)


def cover_art() -> Image.Image:
    image = Image.new("RGBA", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)
    # Chalkboard without text.
    board = (360, 650, 1000, 1280)
    draw.rounded_rectangle(board, radius=18, fill=BROWN, outline=DARK, width=6)
    draw.rectangle((380, 670, 980, 1240), fill=GREEN, outline=DARK, width=5)
    # Simple bra diagram on board.
    draw.ellipse((500, 800, 700, 1010), outline="white", width=10)
    draw.ellipse((690, 800, 890, 1010), outline="white", width=10)
    draw.line((700, 960, 690, 960), fill="white", width=10)
    draw.line((510, 970, 880, 970), fill="white", width=8)
    bunny = Image.open(CUPBUNNY / "설명_안경.png").convert("RGBA")
    paste_contain(image, bunny, (20, 610, 610, 1500))
    return image


def cta_art() -> Image.Image:
    image = Image.new("RGBA", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)
    bunny = Image.open(CUPBUNNY / "설명.png").convert("RGBA")
    paste_contain(image, bunny, (80, 650, 700, 1580))
    draw_save_icon(draw, (690, 850, 980, 1190))
    draw_heart(draw, (830, 1350), 220)
    return image


def term_art(kind: str) -> Image.Image:
    image = Image.new("RGBA", (WIDTH, HEIGHT), "white")
    draw_bra_and_bunny(image, kind)
    return image


def draw_cover_text(image: Image.Image):
    draw = ImageDraw.Draw(image)
    fnt = font(70)
    left = "브라사전"
    lw = text_width(draw, left, fnt)
    badge = 112
    total = lw + 18 + badge
    x = (WIDTH - total) // 2
    draw.text((x, 92), left, font=fnt, fill=BLACK)
    bx = x + lw + 18
    draw.ellipse((bx, 78, bx + badge, 78 + badge), fill=PINK, outline=DARK, width=5)
    ten = font(66)
    tw = text_width(draw, "10", ten)
    draw.text((bx + (badge - tw) / 2, 91), "10", font=ten, fill=BLACK)
    draw_centered(draw, "브라 상세페이지에서\n자주 보는 용어 6개\n쉽게 번역해드림", 245, 64, max_width=930)


def draw_term_text(image: Image.Image, item: dict):
    draw = ImageDraw.Draw(image)
    draw_centered(draw, item["term"], 70, 98, max_width=930)
    draw_centered(draw, item["definition"], 200, 51, max_width=920, color=DARK)

    meta = item["meta"]
    mf = fit_font(draw, meta, 40, 820, 30)
    mb = draw.textbbox((0, 0), meta, font=mf)
    mw = mb[2] - mb[0]
    mh = mb[3] - mb[1]
    mx = (WIDTH - mw) / 2
    draw.rounded_rectangle((mx - 28, 292, mx + mw + 28, 292 + mh + 28), radius=22, fill=PALE_PINK)
    draw.text((mx, 302), meta, font=mf, fill=DARK)

    if item.get("detail"):
        draw_centered(draw, item["detail"], 382, 35, color=GRAY, max_width=870, spacing=6)
    elif item.get("diagram_note"):
        draw_centered(draw, item["diagram_note"], 400, 34, color=GRAY, max_width=850)

    point_box = (65, 1390, 1015, 1745)
    draw.rounded_rectangle(point_box, radius=36, fill=PALE_PINK, outline=CORAL, width=5)
    draw_centered(draw, "큰컵 POINT", 1430, 45, color=CORAL, max_width=840)
    draw_centered(draw, item["point"], 1515, 48, color=BLACK, max_width=850, spacing=10)

    if item.get("footnote"):
        draw_centered(draw, item["footnote"], 1780, 33, color=GRAY, max_width=900)


def draw_cta_text(image: Image.Image):
    draw = ImageDraw.Draw(image)
    draw_centered(draw, "큰컵언니들,", 120, 68, max_width=900)
    draw_centered(draw, "브라 살 때 참고할 수 있도록", 235, 62, max_width=930)
    fnt = font(80)
    text = "저장하고"
    tw = text_width(draw, text, fnt)
    heart_w = 100
    gap = 22
    x = (WIDTH - (tw + gap + heart_w)) / 2
    draw.text((x, 345), text, font=fnt, fill=BLACK)
    draw_heart(draw, (int(x + tw + gap + heart_w / 2), 398), 100)


def build_card(item: dict):
    kind = item["kind"]
    if kind == "cover":
        art = cover_art()
    elif kind == "cta":
        art = cta_art()
    else:
        art = term_art(kind)

    SOURCE.mkdir(parents=True, exist_ok=True)
    source_path = SOURCE / item["file"]
    art.convert("RGB").save(source_path, format="PNG", compress_level=6)

    card = art.copy()
    if kind == "cover":
        draw_cover_text(card)
    elif kind == "cta":
        draw_cta_text(card)
    else:
        draw_term_text(card, item)

    CARDS.mkdir(parents=True, exist_ok=True)
    card.convert("RGB").save(CARDS / item["file"], format="PNG", compress_level=6)


def build_review():
    cards = [CARDS / item["file"] for item in CARDS_DATA]
    thumb_w, thumb_h = 270, 480
    sheet = Image.new("RGB", (thumb_w * 4, thumb_h * 2), "white")
    for index, path in enumerate(cards):
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (index % 4) * thumb_w + (thumb_w - image.width) // 2
        y = (index // 4) * thumb_h + (thumb_h - image.height) // 2
        sheet.paste(image, (x, y))
    REVIEW.mkdir(parents=True, exist_ok=True)
    sheet.save(REVIEW / "COL-005_전체검수.jpg", quality=94, subsampling=0)


def write_metadata():
    ROOT.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PLAN_PATH, ROOT / "00_제작안.md")
    CAPTION.mkdir(parents=True, exist_ok=True)
    caption = """브라 상세페이지를 보다 보면
몰드컵, 재단컵, 홑겹, 중심고어, 옆날개, 사이드본처럼
익숙한 듯 헷갈리는 말이 자주 보여요.

어려운 용어보다 브라의 어느 부분인지,
큰컵에게 왜 중요한지가 바로 보여야 고르기 쉽잖아요.

큰컵언니들, 브라 살 때 참고할 수 있도록 저장하고 💗
"""
    (CAPTION / "caption.txt").write_text(caption, encoding="utf-8")

    manifest = {
        "id": "COL-005",
        "date": "2026-10-28",
        "title": "브라사전 10 브라 상세페이지 용어 번역집",
        "status": "cards_review_pending",
        "reel_created": False,
        "canvas": "1080x1920",
        "card_count": len(CARDS_DATA),
        "font": "Jua-Regular",
        "cards": [
            {"order": index + 1, "file": item["file"], "kind": item["kind"]}
            for index, item in enumerate(CARDS_DATA)
        ],
        "notes": [
            "몰드컵/재단컵/홑겹은 예시를 표기",
            "중심고어/옆날개/사이드본은 위치를 표기",
            "각 용어에 큰컵 POINT 한 줄 표기",
            "마지막 컷은 저장 CTA와 하트만 사용",
            "이미지 검수 후 릴스 제작",
        ],
    }
    (ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    REVIEW.mkdir(parents=True, exist_ok=True)
    review_md = """# COL-005 이미지 검수

- 1080×1920 PNG 8장
- 순서: 표지 / 몰드컵 / 재단컵 / 홑겹 / 중심고어 / 옆날개 / 사이드본 / 저장 CTA
- 모든 용어 컷에 뜻, 예시 또는 위치, 큰컵 포인트 포함
- 마지막 컷 팔로우 문구 제거, `저장하고`와 하트 적용
- 릴스 미제작: 사용자 이미지 검수 대기
"""
    (REVIEW / "00_검수목록.md").write_text(review_md, encoding="utf-8")


def build_zip():
    zip_path = ROOT / "COL-005_이미지검수용.zip"
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
        for item in CARDS_DATA:
            path = CARDS / item["file"]
            archive.write(path, arcname=f"02_cards/{path.name}")
        archive.write(REVIEW / "COL-005_전체검수.jpg", arcname="05_review/COL-005_전체검수.jpg")
        archive.write(ROOT / "00_제작안.md", arcname="00_제작안.md")
        archive.write(ROOT / "manifest.json", arcname="manifest.json")


def main():
    for directory in (SOURCE, CARDS, REVIEW, CAPTION):
        directory.mkdir(parents=True, exist_ok=True)
    for directory in (SOURCE, CARDS):
        for old in directory.glob("*.png"):
            old.unlink()
    for item in CARDS_DATA:
        build_card(item)
    write_metadata()
    build_review()
    build_zip()


if __name__ == "__main__":
    main()
