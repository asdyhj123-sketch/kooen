"""주간기획의 카드 데이터(CLAUDE.md 7-2)를 1254x1254 카드 이미지로 만든다. API 사용 안 함.

실행 (KOOEN 폴더에서):
  python tools/make_cards.py            최신 주간기획의 카드 전부
  python tools/make_cards.py 월         월요일 카드만
  python tools/make_cards.py 월_3       카드 하나만

출력: output/images/[주차]/[카드 id].png
템플릿: 현재 `칠판`만 구현 (공감·표지·본문·마무리는 추가 예정)
"""
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
PLAN_DIR = ROOT / "output" / "주간"
POSE_DIR = ROOT / "assets" / "cupbunny"
IMG_DIR = ROOT / "output" / "images"
FONT_MAIN = ROOT / "assets" / "fonts" / "Jua-Regular.ttf"
FONT_FALLBACK = next(
    (path for path in (
        Path(r"C:\Windows\Fonts\malgunbd.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ) if path.exists()),
    FONT_MAIN,
)  # Jua에 없는 기호(① → − · …)용. Windows와 Codex Linux 환경 모두 지원.

SIZE = 1254

# 색 (CLAUDE.md 2번 + 포인트 라벤더-퍼플·그레이)
INK = "#1F1F1F"
LINE = "#3A3A3A"
GRAY = "#8C8C8C"
LAVENDER = "#7E6BB5"
LAVENDER_BG = "#EEEAF7"
BOARD = "#3B3F42"
BOARD_FRAME = "#8F9396"
CHALK = "#F3F3EC"

# 없는 포즈 → 가장 비슷한 있는 포즈 (2026-10-15 포즈 생성 중단, 있는 포즈만 사용)
POSE_FALLBACK = {
    "OK": "기본",
    "놀람": "실망",
}
# 안경 포즈가 없으면 안경 쓴 토끼 선생님(설명_안경)으로 대체해 칠판 카드의 안경 느낌을 유지
GLASSES_FALLBACK = "설명_안경"
# 지시봉이 화면 오른쪽을 가리키는 포즈 → 컵토끼를 왼쪽, 칠판을 오른쪽에 둔다
POINTS_RIGHT = {"설명_안경"}


# ---------- 주간기획 읽기 ----------

def latest_plan():
    plans = sorted(PLAN_DIR.glob("*_주간기획.md"))
    if not plans:
        sys.exit("output/주간/ 에 주간기획 파일이 없어요.")
    return plans[-1]


def week_of(plan_path):
    return plan_path.name.split("_")[0]


def parse_cards(text):
    """```card 블록들을 dict 목록으로."""
    cards = []
    for block in re.findall(r"```card\n(.*?)```", text, re.S):
        card, body_lines, in_body = {}, [], False
        for line in block.splitlines():
            if in_body:
                if line.startswith("  ") or not line.strip():
                    body_lines.append(line[2:] if line.startswith("  ") else "")
                    continue
                in_body = False
            if line.startswith("body:"):
                in_body = True
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                card[k.strip()] = v.strip()
        card["body"] = [l for l in body_lines if l.strip()]
        card["seconds"] = float(card["seconds"]) if card.get("seconds") else None
        cards.append(card)
    return cards


def select(cards, arg):
    if not arg:
        return cards
    if "_" in arg:
        return [c for c in cards if c["id"] == arg]
    return [c for c in cards if c["id"].split("_")[0] == arg]


# ---------- 포즈 ----------

def resolve_pose(name):
    """요청 포즈 → 실제 파일. 없으면 안경 빼기 → 대체 포즈 순으로 찾는다."""
    if (POSE_DIR / f"{name}.png").exists():
        return name, None
    base = name[: -len("_안경")] if name.endswith("_안경") else name
    cands = [GLASSES_FALLBACK] if name.endswith("_안경") else []
    for cand in cands + [base, POSE_FALLBACK.get(base)]:
        if cand and (POSE_DIR / f"{cand}.png").exists():
            return cand, f"{name} 없음 → {cand}로 대체"
    sys.exit(f"포즈 '{name}'도, 대체할 포즈도 없어요. assets/cupbunny/ 를 확인해주세요.")


def load_pose(name, height):
    img = Image.open(POSE_DIR / f"{name}.png").convert("RGBA")
    img = img.crop(img.getchannel("A").getbbox())
    # 배경 제거 후 외곽선 바깥에 남은 1~2픽셀 흰 테두리를 깎아낸다 (어두운 칠판 위에서 보이지 않게)
    img.putalpha(img.getchannel("A").filter(ImageFilter.MinFilter(5)))
    return img.resize((round(img.width * height / img.height), height), Image.LANCZOS)


# ---------- 글자 ----------

_font_cache = {}


def fonts(size):
    if size not in _font_cache:
        _font_cache[size] = (ImageFont.truetype(str(FONT_MAIN), size),
                             ImageFont.truetype(str(FONT_FALLBACK), round(size * 0.86)))
    return _font_cache[size]


def _missing_sig(font):
    im = Image.new("L", (80, 80), 0)
    ImageDraw.Draw(im).text((5, 5), "\U0010FFFD", font=font, fill=255)
    return im.tobytes()


_glyph_cache = {}


def has_glyph(ch):
    if ch not in _glyph_cache:
        f = fonts(40)[0]
        im = Image.new("L", (80, 80), 0)
        ImageDraw.Draw(im).text((5, 5), ch, font=f, fill=255)
        _glyph_cache[ch] = ch.isspace() or im.tobytes() != _missing_sig(f)
    return _glyph_cache[ch]


def text_width(text, size):
    main, fb = fonts(size)
    return sum((main if has_glyph(c) else fb).getlength(c) for c in text)


def draw_text(draw, xy, text, size, fill):
    """한 줄 그리기. Jua에 없는 글자는 맑은 고딕 굵게로."""
    main, fb = fonts(size)
    x, y = xy
    for c in text:
        f = main if has_glyph(c) else fb
        dy = 0 if f is main else round(size * 0.1)
        draw.text((x, y + dy), c, font=f, fill=fill)
        x += f.getlength(c)


def wrap(line, size, max_w):
    """띄어쓰기 기준 자동 줄바꿈."""
    if text_width(line, size) <= max_w:
        return [line]
    out, cur = [], ""
    for word in line.split(" "):
        trial = (cur + " " + word).strip()
        if cur and text_width(trial, size) > max_w:
            out.append(cur)
            cur = word
        else:
            cur = trial
    out.append(cur)
    return out


def fit_lines(lines, start, minimum, max_w, max_h, spacing):
    """글자 크기 축소 → 그래도 안 되면 줄바꿈으로 상자 안에 맞춘다. (크기, 줄 목록, 축소 여부)

    줄을 먼저 쪼개면 '① …' 목록이 어색하게 끊기므로, 원래 줄을 지키며 75%까지 줄여보고
    그 다음에 줄바꿈을 허용한다.
    """
    for size in range(start, max(minimum, round(start * 0.75)) - 1, -2):
        if (all(text_width(l, size) <= max_w for l in lines)
                and len(lines) * size * spacing <= max_h):
            return size, list(lines), size < start
    for size in range(start, minimum - 1, -2):
        wrapped = [w for l in lines for w in wrap(l, size, max_w)]
        if (all(text_width(w, size) <= max_w for w in wrapped)
                and len(wrapped) * size * spacing <= max_h):
            return size, wrapped, size < start
    return minimum, [w for l in lines for w in wrap(l, minimum, max_w)], True


# ---------- 템플릿 ----------

def template_chalkboard(card):
    """칠판: 흰 배경 + 위 제목 + 차콜 칠판(본문) + 오른쪽 안경 컵토끼."""
    img = Image.new("RGB", (SIZE, SIZE), "#FFFFFF")
    d = ImageDraw.Draw(img)
    shrunk = False

    # 시리즈 라벨
    label = "브라사전"
    lw = text_width(label, 40)
    d.rounded_rectangle((70, 62, 70 + lw + 52, 62 + 70), radius=35, fill=LAVENDER_BG)
    draw_text(d, (96, 72), label, 40, LAVENDER)

    # 제목 (최대 2줄)
    t_size, t_lines, s1 = fit_lines([card.get("title", "")], 84, 56, SIZE - 140, 210, 1.22)
    shrunk |= s1
    y = 160
    for line in t_lines:
        draw_text(d, (70, y), line, t_size, INK)
        y += round(t_size * 1.22)

    # 컵토끼 위치: 보통은 칠판 오른쪽 앞, 지시봉이 오른쪽을 가리키는 포즈면 왼쪽 앞
    pose_name, note = resolve_pose(card.get("pose", "설명_안경"))
    bunny_left = pose_name in POINTS_RIGHT
    bunny = load_pose(pose_name, 820 if bunny_left else 860)
    bx = 10 if bunny_left else SIZE - bunny.width - 30
    by = SIZE - bunny.height - 40

    # 칠판 (제목 바로 아래부터)
    top = min(y + 40, 420)
    board = (SIZE - 60 - 820, top, SIZE - 60, 1110) if bunny_left else (60, top, 880, 1110)
    d.rounded_rectangle(board, radius=26, fill=BOARD_FRAME)
    inner = (board[0] + 16, board[1] + 16, board[2] - 16, board[3] - 16)
    d.rounded_rectangle(inner, radius=16, fill=BOARD)
    d.rounded_rectangle((board[0] + 50, board[3] - 2, board[2] - 50, board[3] + 18),
                        radius=8, fill="#B9BCBF")  # 분필 받침

    # 본문 (분필 글씨). 컵토끼 몸이 칠판에 겹치는 쪽은 비워둔다
    body = card.get("body") or []
    if body:
        pad = 56
        max_h = inner[3] - inner[1] - pad * 2
        if bunny_left:
            # 글자는 칠판 위쪽에 두고, 지시봉 끝(그림 높이의 약 40%)이 글자 바로 아래를 가리키게 한다
            body_right = bx + bunny.width * 0.72  # 지시봉을 뺀 몸 오른쪽 끝
            stick_tip_y = by + bunny.height * 0.40
            left, right = max(inner[0] + pad, body_right + 30), inner[2] - pad
            b_size, b_lines, s2 = fit_lines(body, 64, 38, right - left, stick_tip_y - 30 - (inner[1] + pad), 1.5)
            if len(b_lines) * b_size * 1.5 > stick_tip_y - 30 - (inner[1] + pad):
                # 글이 길어 지시봉까지 내려오면 지시봉 끝보다 오른쪽으로 옮긴다
                left = bx + bunny.width + 20
                b_size, b_lines, s2 = fit_lines(body, 64, 38, right - left, max_h, 1.5)
            y = inner[1] + pad
        else:
            left, right = inner[0] + pad, inner[2] - pad - 40
            b_size, b_lines, s2 = fit_lines(body, 64, 38, right - left, max_h, 1.5)
            y = inner[1] + pad + (max_h - len(b_lines) * b_size * 1.5) / 2
        shrunk |= s2
        for line in b_lines:
            draw_text(d, (left, y), line, b_size, CHALK)
            y += b_size * 1.5

    img.paste(bunny, (bx, by), bunny)

    # 계정 (컵토끼 반대쪽 아래)
    handle = "@kooen.official"
    hx = SIZE - 70 - text_width(handle, 34) if bunny_left else 70
    draw_text(d, (hx, SIZE - 92), handle, 34, GRAY)
    return img, shrunk, note


TEMPLATES = {"칠판": template_chalkboard}


def make(card, out_dir):
    tpl = card.get("template")
    if tpl not in TEMPLATES:
        print(f"건너뜀: {card['id']} — '{tpl}' 템플릿은 아직 없어요")
        return None
    img, shrunk, note = TEMPLATES[tpl](card)
    out = out_dir / f"{card['id']}.png"
    img.save(out)
    msg = f"저장: {out.relative_to(ROOT)}"
    if shrunk:
        msg += "  (글자 크기 줄어듦)"
    if note:
        msg += f"  (포즈 {note})"
    print(msg)
    return out


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    plan = latest_plan()
    cards = select(parse_cards(plan.read_text(encoding="utf-8")), arg)
    if not cards:
        sys.exit(f"'{arg}'에 해당하는 카드가 없어요.")
    out_dir = IMG_DIR / week_of(plan)
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"주간기획: {plan.name}")
    for c in cards:
        make(c, out_dir)


if __name__ == "__main__":
    main()
