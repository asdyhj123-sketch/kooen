"""브라 상품 그림 정리 (API 사용 안 함).

reference/의 브라 상품 그림을 그대로 쓰되, 카드에 넣기 좋게 크기·여백·배경을 맞춘다.
- assets/bras/[이름].png       : 1254x1254 흰 배경
- assets/bras/[이름]_투명.png  : 같은 그림, 바깥 흰 배경만 투명

실행: python tools/make_bra_images.py
새 브라 추가: BRAS 에 "이름": "reference 파일명" 추가
"""
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from make_pose import remove_background  # noqa: E402

OUT = ROOT / "assets" / "bras"
SIZE = 1254
MARGIN = 90

BRAS = {
    "미니마이저": "미니마이저 브라.png",
    "3분의4컵": "3분의4컵 브라.png",
    "풀컵": "풀컵 브라.png",  # 사용자가 넣을 예정
}


def trim(img):
    gray = img.convert("L").point(lambda v: 255 if v < 240 else 0)
    box = gray.getbbox()
    return img.crop(box) if box else img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fname in BRAS.items():
        src = ROOT / "reference" / fname
        if not src.exists():
            print(f"건너뜀: reference/{fname} 없음")
            continue
        img = trim(Image.open(src).convert("RGB"))
        img.thumbnail((SIZE - MARGIN * 2, SIZE - MARGIN * 2), Image.LANCZOS)
        canvas = Image.new("RGB", (SIZE, SIZE), "#FFFFFF")
        canvas.paste(img, ((SIZE - img.width) // 2, (SIZE - img.height) // 2))
        canvas.save(OUT / f"{name}.png")
        remove_background(canvas).save(OUT / f"{name}_투명.png")
        print(f"저장: assets/bras/{name}.png, {name}_투명.png")


if __name__ == "__main__":
    main()
