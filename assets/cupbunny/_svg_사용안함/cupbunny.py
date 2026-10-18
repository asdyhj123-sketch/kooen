"""컵토끼 SVG 생성기.

포즈별 SVG를 assets/cupbunny/ 에 만들고, 미리보기를 저장한다.
- output/images/_컵토끼_미리보기.png : 전체 포즈
- output/images/_컵토끼_비교.png     : reference 원본과 나란히 비교

실행: python tools/cupbunny.py
새 포즈 추가: POSES 에 항목을 추가하고 다시 실행 (CLAUDE.md 7-2 pose 목록도 같이 수정)

비율 기준 (전체 키 = 귀 끝 ~ 발끝):
- 귀 약 25%, 머리 약 40%, 목 없이 머리 아래가 몸 위에 살짝 겹침
- 머리는 위보다 볼 쪽이 넓은 둥근 모양, 몸은 서양배 모양(배·엉덩이가 더 넓음)
- 옷은 어깨끈 있는 짧은 크롭 브라탑, 배는 털 색 그대로 (하의 없음)
"""
from io import BytesIO
from pathlib import Path

import resvg_py
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "assets" / "cupbunny"
PREVIEW = ROOT / "output" / "images" / "_컵토끼_미리보기.png"
COMPARE = ROOT / "output" / "images" / "_컵토끼_비교.png"
REF_DIR = ROOT / "reference"
FONT = ROOT / "assets" / "fonts" / "Jua-Regular.ttf"

# CLAUDE.md 2번 고정 색상 (절대 변경 금지)
FUR = "#FEFAF5"
PINK = "#F9CEC3"
LINE = "#3A3A3A"
TOP = "#2E2E2E"  # 검정 브라탑
TOP_LINE = "#4A4A4A"  # 브라탑 안쪽 밑선
STICK = "#B08A6A"  # 지시봉

W, H = 600, 900
SW = 8  # 외곽선 두께 (전체 동일)
ARM_W = 58  # 팔 굵기


# ---------- 부품 ----------

def arm(points):
    """짧고 통통한 팔. 끝이 둥근 손. points: [(x,y), ...] 어깨 → 손 순서."""
    d = "M " + " L ".join(f"{x} {y}" for x, y in points)
    common = 'fill="none" stroke-linecap="round" stroke-linejoin="round"'
    return (f'<path d="{d}" stroke="{LINE}" stroke-width="{ARM_W + SW * 2}" {common}/>'
            f'<path d="{d}" stroke="{FUR}" stroke-width="{ARM_W}" {common}/>')


def ears():
    out = []
    # 끝이 둥근 긴 타원, 위로 갈수록 바깥으로 벌어지는 V자
    for cx, rot in ((214, -15), (386, 15)):
        cy = 150
        pink = (f'M {cx} {cy - 100} C {cx + 30} {cy - 100} {cx + 26} {cy + 30} {cx} {cy + 86} '
                f'C {cx - 26} {cy + 30} {cx - 30} {cy - 100} {cx} {cy - 100} Z')
        out.append(f'<g transform="rotate({rot} {cx} {cy + 120})">'
                   f'<ellipse cx="{cx}" cy="{cy}" rx="56" ry="138" fill="{FUR}" stroke="{LINE}" stroke-width="{SW}"/>'
                   f'<path d="{pink}" fill="{PINK}"/>'
                   f'</g>')
    return "".join(out)


def tail():
    return f'<circle cx="116" cy="772" r="27" fill="{FUR}" stroke="{LINE}" stroke-width="{SW}"/>'


def body():
    # 서양배 모양 몸통에서 짧고 뭉툭한 두 다리가 이어짐 (다리 사이 작은 틈)
    return (f'<path d="M 300 520 C 380 520 420 560 425 610 C 466 670 480 752 452 810 '
            f'C 444 836 420 852 408 874 Q 398 890 354 888 Q 322 886 316 858 L 312 832 '
            f'Q 300 822 288 832 L 284 858 Q 278 886 246 888 Q 202 890 192 874 '
            f'C 180 852 156 836 148 810 C 120 752 134 670 175 610 C 180 560 220 520 300 520 Z" '
            f'fill="{FUR}" stroke="{LINE}" stroke-width="{SW}" stroke-linejoin="round"/>')


def bra_top():
    # 어깨끈 + 둥근 목선 + 가슴을 감싸고 아래가 둥글게 끝나는 크롭 브라탑 (배는 드러남)
    return (f'<path d="M 194 596 L 214 546 L 244 546 Q 300 620 356 546 L 386 546 L 406 596 '
            f'C 462 614 472 698 432 720 Q 366 742 300 728 Q 234 742 168 720 '
            f'C 128 698 138 614 194 596 Z" '
            f'fill="{TOP}" stroke="{LINE}" stroke-width="{SW}" stroke-linejoin="round"/>'
            f'<path d="M 186 710 Q 244 728 300 716 Q 356 728 414 710" fill="none" stroke="{TOP_LINE}" '
            f'stroke-width="4" stroke-linecap="round"/>')


def head():
    # 위보다 아래(볼 쪽)가 더 넓은 둥근 머리
    return (f'<path d="M 300 234 C 402 234 458 292 476 368 C 504 478 452 560 300 560 '
            f'C 148 560 96 478 124 368 C 142 292 198 234 300 234 Z" '
            f'fill="{FUR}" stroke="{LINE}" stroke-width="{SW}" stroke-linejoin="round"/>')


# 얼굴 기준점: 눈은 얼굴 가운데보다 약간 아래, 간격 넓게
EYE_L, EYE_R, EYE_Y = 230, 370, 420


def blush():
    return (f'<ellipse cx="{EYE_L - 32}" cy="{EYE_Y + 36}" rx="28" ry="15" fill="{PINK}"/>'
            f'<ellipse cx="{EYE_R + 32}" cy="{EYE_Y + 36}" rx="28" ry="15" fill="{PINK}"/>')


def eyes(kind):
    if kind == "dot":
        return (f'<ellipse cx="{EYE_L}" cy="{EYE_Y}" rx="9" ry="13" fill="{LINE}"/>'
                f'<ellipse cx="{EYE_R}" cy="{EYE_Y}" rx="9" ry="13" fill="{LINE}"/>')
    if kind == "wide":
        return (f'<ellipse cx="{EYE_L}" cy="{EYE_Y}" rx="13" ry="18" fill="{LINE}"/>'
                f'<ellipse cx="{EYE_R}" cy="{EYE_Y}" rx="13" ry="18" fill="{LINE}"/>'
                f'<circle cx="{EYE_L + 4}" cy="{EYE_Y - 6}" r="4.5" fill="#FFFFFF"/>'
                f'<circle cx="{EYE_R + 4}" cy="{EYE_Y - 6}" r="4.5" fill="#FFFFFF"/>')
    if kind == "happy":
        return "".join(f'<path d="M {x - 15} {EYE_Y + 6} Q {x} {EYE_Y - 14} {x + 15} {EYE_Y + 6}" fill="none" '
                       f'stroke="{LINE}" stroke-width="6" stroke-linecap="round"/>' for x in (EYE_L, EYE_R))
    raise ValueError(kind)


def brows(kind):
    if kind == "up":
        return "".join(f'<path d="M {x - 15} {EYE_Y - 36} Q {x} {EYE_Y - 48} {x + 15} {EYE_Y - 38}" fill="none" '
                       f'stroke="{LINE}" stroke-width="5" stroke-linecap="round"/>' for x in (EYE_L, EYE_R))
    return ""


def mouth(kind):
    y = EYE_Y + 44
    if kind == "o":
        return f'<ellipse cx="300" cy="{y}" rx="9" ry="12" fill="{PINK}" stroke="{LINE}" stroke-width="4"/>'
    if kind == "big_o":
        return f'<ellipse cx="300" cy="{y + 2}" rx="12" ry="17" fill="{PINK}" stroke="{LINE}" stroke-width="4"/>'
    if kind == "smile":
        return (f'<path d="M 284 {y - 6} Q 300 {y + 14} 316 {y - 6}" fill="{PINK}" stroke="{LINE}" '
                f'stroke-width="4" stroke-linejoin="round"/>')
    raise ValueError(kind)


def glasses():
    r = 46
    return (f'<circle cx="{EYE_L}" cy="{EYE_Y}" r="{r}" fill="none" stroke="{LINE}" stroke-width="5"/>'
            f'<circle cx="{EYE_R}" cy="{EYE_Y}" r="{r}" fill="none" stroke="{LINE}" stroke-width="5"/>'
            f'<path d="M {EYE_L + r} {EYE_Y - 4} Q 300 {EYE_Y - 16} {EYE_R - r} {EYE_Y - 4}" fill="none" stroke="{LINE}" stroke-width="5"/>'
            f'<path d="M {EYE_L - r} {EYE_Y - 6} L {EYE_L - r - 18} {EYE_Y - 12}" stroke="{LINE}" stroke-width="5" stroke-linecap="round"/>'
            f'<path d="M {EYE_R + r} {EYE_Y - 6} L {EYE_R + r + 18} {EYE_Y - 12}" stroke="{LINE}" stroke-width="5" stroke-linecap="round"/>')


# ---------- 포즈 ----------
# side: 몸 위·머리 아래에 그리는 팔 (어깨가 머리에 가려짐)
# front: 머리 위에 그리는 팔 (얼굴 앞으로 오는 손)
# extra: 팔보다 먼저 그리는 소품 (지시봉 등)
HIP_L = [(194, 606), (146, 650), (176, 700)]          # 화면 왼쪽 팔, 허리에 손
HIP_R = [(406, 606), (454, 650), (424, 700)]          # 화면 오른쪽 팔, 허리에 손
DOWN_L = [(192, 606), (160, 656), (162, 698)]
DOWN_R = [(408, 606), (440, 656), (438, 698)]
CHIN_R = [(406, 612), (438, 586), (352, 532)]         # 화면 오른쪽 팔, 턱에 손


def stick(x1, y1, x2, y2):
    return (f'<path d="M {x1} {y1} L {x2} {y2}" stroke="{LINE}" stroke-width="16" stroke-linecap="round"/>'
            f'<path d="M {x1} {y1} L {x2} {y2}" stroke="{STICK}" stroke-width="8" stroke-linecap="round"/>')


def ok_ring(x, y):
    return (f'<circle cx="{x}" cy="{y}" r="24" fill="{FUR}" stroke="{LINE}" stroke-width="{SW}"/>'
            f'<circle cx="{x}" cy="{y - 2}" r="8" fill="none" stroke="{LINE}" stroke-width="4"/>')


POSES = {
    # 원본 기준 포즈: 한 손은 허리, 한 손은 턱
    "고민": dict(side=[HIP_L], front=[CHIN_R], eyes="dot", brows="", mouth="o"),
    "기본": dict(side=[DOWN_L, DOWN_R], front=[], eyes="dot", brows="", mouth="o"),
    # 화면 왼쪽을 지시봉으로 가리킴 → 카드에서는 컵토끼를 오른쪽에 둔다
    "설명": dict(side=[HIP_R], front=[[(194, 608), (142, 592), (110, 556)]],
                extra=stick(110, 556, 50, 452), eyes="dot", brows="", mouth="o"),
    "놀람": dict(side=[], front=[[(196, 612), (150, 575), (162, 515)], [(404, 612), (450, 575), (438, 515)]],
                eyes="wide", brows="up", mouth="big_o"),
    "OK": dict(side=[HIP_L], front=[[(406, 608), (462, 575), (476, 512)]],
               after=ok_ring(478, 492), eyes="happy", brows="", mouth="smile"),
}


def build_svg(pose, with_glasses):
    p = POSES[pose]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">']
    parts += [tail(), body(), bra_top()]
    parts += [arm(pts) for pts in p["side"]]
    parts += [ears(), head(), blush(), brows(p["brows"]), eyes(p["eyes"]), mouth(p["mouth"])]
    if with_glasses:
        parts.append(glasses())
    parts.append(p.get("extra", ""))
    parts += [arm(pts) for pts in p["front"]]
    parts.append(p.get("after", ""))
    parts.append("</svg>")
    return "".join(parts)


def render(svg, width):
    return Image.open(BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=svg, width=width)))).convert("RGBA")


def trim(img):
    """흰 여백을 잘라낸다."""
    gray = img.convert("L").point(lambda v: 255 if v < 235 else 0)
    return img.crop(gray.getbbox())


def fit_height(img, h):
    return img.resize((round(img.width * h / img.height), h), Image.LANCZOS)


def make_compare(font):
    """reference 원본과 새 컵토끼를 같은 키로 나란히 놓은 비교 이미지."""
    pairs = [
        ("앞을 보는 귀여운 토끼 캐릭터.png", "고민", "원본 (정면)", "새 컵토끼: 고민"),
        ("안경 쓴 토끼 선생님.png", "설명_안경", "원본 (안경, 칠판)", "새 컵토끼: 설명_안경"),
    ]
    ch, pad, label_h = 640, 50, 60
    rows = []
    for ref_name, pose, l1, l2 in pairs:
        ref_path = REF_DIR / ref_name
        if not ref_path.exists():
            continue
        ref = fit_height(trim(Image.open(ref_path).convert("RGB")), ch)
        svg = (OUT_DIR / f"{pose}.svg").read_text(encoding="utf-8")
        new = fit_height(trim(_flatten(render(svg, 1200))), ch)
        rows.append((ref, new, l1, l2))
    if not rows:
        return
    col_w = max(max(r[0].width, r[1].width) for r in rows) + pad * 2
    sheet = Image.new("RGB", (col_w * 2, (ch + label_h + pad) * len(rows) + pad), "#FFFFFF")
    draw = ImageDraw.Draw(sheet)
    for i, (ref, new, l1, l2) in enumerate(rows):
        y = pad + i * (ch + label_h + pad)
        for j, (img, label) in enumerate(((ref, l1), (new, l2))):
            x = j * col_w + (col_w - img.width) // 2
            sheet.paste(img, (x, y))
            tw = draw.textlength(label, font=font)
            draw.text((j * col_w + (col_w - tw) / 2, y + ch + 12), label, font=font, fill=LINE)
    draw.line((col_w, pad, col_w, sheet.height - pad), fill="#E5E2EC", width=3)
    sheet.save(COMPARE)
    print(f"비교: {COMPARE}")


def _flatten(rgba):
    bg = Image.new("RGB", rgba.size, "#FFFFFF")
    bg.paste(rgba, (0, 0), rgba)
    return bg


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    names = []
    for pose in POSES:
        for g in (False, True):
            name = pose + ("_안경" if g else "")
            (OUT_DIR / f"{name}.svg").write_text(build_svg(pose, g), encoding="utf-8")
            names.append(name)

    # 미리보기: 5열 × 2행 (위: 기본, 아래: 안경)
    cw, ch, label_h = 300, 450, 60
    sheet = Image.new("RGB", (cw * 5, (ch + label_h) * 2), "#FFFFFF")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(FONT), 34)
    for i, name in enumerate(names):
        col, row = i // 2, i % 2
        x, y = col * cw, row * (ch + label_h)
        img = render((OUT_DIR / f"{name}.svg").read_text(encoding="utf-8"), cw)
        sheet.paste(img, (x, y), img)
        tw = draw.textlength(name, font=font)
        draw.text((x + (cw - tw) / 2, y + ch + 8), name, font=font, fill=LINE)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(PREVIEW)
    print(f"{len(names)}개 포즈 저장: {OUT_DIR}")
    print(f"미리보기: {PREVIEW}")
    make_compare(font)


if __name__ == "__main__":
    main()
