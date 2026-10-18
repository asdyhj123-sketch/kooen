"""컵토끼 포즈 만들기 (OpenAI 이미지 편집 API, 마스크로 일부만 수정).

원본(reference/의 정면 컵토끼)에서 팔·얼굴·안경 영역만 바꿔 포즈 PNG를 만든다.
API는 포즈를 만들 때만 쓴다. 매주 카드·릴스 생성에는 쓰지 않는다.

사용법 (KOOEN 폴더에서):
  python tools/make_pose.py list                 포즈 목록과 상태
  python tools/make_pose.py original             고민 포즈 = 원본 그대로 (API 사용 안 함)
  python tools/make_pose.py original 실망 "파일.png"  reference/의 다른 그림을 그대로 포즈로 (API 사용 안 함)
  python tools/make_pose.py mask 기본            바꿀 영역 확인용 이미지 저장 (API 사용 안 함)
  python tools/make_pose.py estimate 기본 --n 2  장수·예상 비용만 출력 (API 사용 안 함)
  python tools/make_pose.py make 기본 --n 2 --yes  실제 생성 (비용 발생, 사용자 OK 후에만)
  python tools/make_pose.py pick 기본 2          후보 2번을 최종 포즈로 저장
  python tools/make_pose.py preview              전체 포즈 미리보기

새 포즈 추가: POSES 에 항목을 추가 (CLAUDE.md 7-2 pose 목록도 같이 수정)
"""
import argparse
import base64
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "reference" / "앞을 보는 귀여운 토끼 캐릭터.png"
GLASSES_REF = ROOT / "reference" / "안경 쓴 토끼 선생님.png"
POSE_DIR = ROOT / "assets" / "cupbunny"
OPAQUE_DIR = POSE_DIR / "_원본"          # 흰 배경 버전 (안경 포즈를 만들 때 기준으로 씀)
CAND_DIR = ROOT / "output" / "images" / "_포즈후보"
PREVIEW = ROOT / "output" / "images" / "_컵토끼_미리보기.png"
FONT = ROOT / "assets" / "fonts" / "Jua-Regular.ttf"

# 2026-10-14 OpenAI 공식 문서 확인: 편집 정확도가 중요한 작업용 모델
MODEL = "gpt-image-2.5-sunburst"
SIZE = "1024x1536"
# 1024x1536 1장 예상 비용(달러). 출력 단가(공식 계산표의 GPT Image 2 기준, 2.5와 토큰 단가 동일)
# + 기준 이미지 입력(고해상도 처리) 대략치. 정확한 금액은 OpenAI 사용량 페이지에서 확인.
COST_PER_IMAGE = {"low": 0.02, "medium": 0.06, "high": 0.19}

STYLE = (
    "Edit only the masked area of this illustration. Keep it the exact same character: "
    "a chubby cream-white bunny in flat minimal cartoon style with the same line weight, "
    "proportions, head, ears, body and black crop bra top. Colors must stay exactly: "
    "fur #FEFAF5, inner ears and cheek blush #F9CEC3, outline #3A3A3A. "
    "No pants, no shorts, no skirt: the lower body stays bare cream fur exactly like the original. "
    "Short chubby arms with round mitten hands and no fingers drawn in detail. "
    "Plain white background. No text, no letters, no extra objects unless asked."
)

# 영역 좌표는 원본(1024x1536) 기준 픽셀 (x1, y1, x2, y2). 이 사각형 안만 바뀐다.
ARM_L = (150, 790, 400, 1050)        # 화면 왼쪽 팔(허리에 손) 주변, 아래 꼬리는 제외
ARM_R = (560, 730, 860, 1170)        # 화면 오른쪽 팔(턱에 손) 주변
FACE = (330, 610, 700, 790)          # 눈·볼·입
EYES = (320, 600, 710, 760)          # 안경이 들어갈 눈 주변

POSES = {
    "고민": dict(base="reference", regions=None, prompt=None),  # 원본 그대로
    "기본": dict(base="reference", regions=[ARM_L, ARM_R], prompt=(
        "Change only the arms: both arms now hang relaxed down at the sides of the body, "
        "hands resting near the hips. Gentle small smile is fine but keep the face otherwise the same.")),
    # 2026-10-14 사용자 요청: 가리키기 대신 양손 허리 (원본 왼손이 이미 허리라 오른팔만 수정)
    "설명": dict(base="reference", regions=[ARM_R], prompt=(
        "Change only the arm on the viewer's right: it moves down from the chin and rests on the hip, "
        "mirroring the other arm, so both hands are on the hips in a confident explaining pose. "
        "The hand is a simple round mitten shape with no fingers, exactly like the other hand.")),
    # 2026-10-15 사용자 요청: 놀람 대신 실망. 톤 규칙상 눈물·우는 표정 금지
    # 최종본은 사용자가 넣은 reference/실망한 표정의 귀여운 토끼 캐릭터.png 를 그대로 사용 (original 명령)
    "실망": dict(base="reference", regions=[ARM_L, ARM_R, FACE], prompt=(
        "Change the arms and the face: a mildly disappointed, let-down look. Both arms hang down "
        "limply at the sides with round mitten hands, shoulders slightly slumped. Eyes are half-closed "
        "and droop downward at the outer corners, small downturned mouth. No tears, no crying, "
        "no sweat drops. Blush stays the same pink.")),
    "OK": dict(base="reference", regions=[ARM_L, (560, 560, 1024, 1170), FACE], prompt=(
        "Change the arms and the face: the arm on the viewer's right is raised giving a thumbs up, "
        "the other arm rests on the hip. Happy closed smiling eyes shaped like upside-down U (∩ ∩) "
        "and a small smile.")),
}
GLASSES_PROMPT = (
    "Change only the area around the eyes: add thin round black eyeglasses, the same style as the "
    "glasses in the second reference image. Keep the eyes, expression and everything else unchanged."
)


def all_pose_names():
    names = []
    for p in POSES:
        names += [p, p + "_안경"]
    return names


def spec(name):
    """포즈 이름 → (기준 이미지 경로, 영역, 프롬프트, 추가 참고 이미지)"""
    if name.endswith("_안경"):
        base_pose = name[: -len("_안경")]
        if base_pose not in POSES:
            sys.exit(f"없는 포즈: {base_pose}")
        base = OPAQUE_DIR / f"{base_pose}.png"
        if not base.exists():
            sys.exit(f"'{base_pose}' 포즈를 먼저 완성해야 '{name}'을 만들 수 있어요.")
        return base, [EYES], GLASSES_PROMPT, [GLASSES_REF]
    if name not in POSES:
        sys.exit(f"없는 포즈: {name}  (가능: {', '.join(all_pose_names())})")
    p = POSES[name]
    return REF, p["regions"], p["prompt"], []


def build_mask(size, regions):
    """흰 불투명 이미지에서 바꿀 영역만 투명(alpha 0)으로. 원본 1024x1536 기준 좌표를 크기에 맞춰 변환."""
    sx, sy = size[0] / 1024, size[1] / 1536
    mask = Image.new("RGBA", size, (255, 255, 255, 255))
    d = ImageDraw.Draw(mask)
    for x1, y1, x2, y2 in regions:
        d.rounded_rectangle((x1 * sx, y1 * sy, x2 * sx, y2 * sy), radius=40, fill=(0, 0, 0, 0))
    return mask


def remove_background(img):
    """가장자리에서 이어진 흰 배경만 투명 처리. 토끼 털(#FEFAF5)은 색으로 구분해서 지우지 않는다.

    배경 후보 = 거의 순백(가장 어두운 채널 ≥ 250, 채널 차이 ≤ 4). 털은 파랑 채널이 245 근처라 제외된다.
    가장자리와 이어진 영역 + 팔과 몸 사이처럼 갇힌 큰 흰 영역(400픽셀 이상)을 지우고,
    눈 하이라이트 같은 작은 흰 점은 남긴다.
    """
    rgb = img.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    cand = Image.new("L", (w + 2, h + 2), 255)  # 바깥 1픽셀 테두리 = 배경 후보로 이어 붙임
    cp = cand.load()
    for y in range(h):
        for x in range(w):
            pr, pg, pb = px[x, y]
            mn, mx = min(pr, pg, pb), max(pr, pg, pb)
            if not (mn >= 250 and mx - mn <= 4):
                cp[x + 1, y + 1] = 0
    BG, KEEP, TMP = 128, 60, 200
    ImageDraw.floodfill(cand, (0, 0), BG)
    # 갇힌 흰 영역 처리
    while True:
        only_white = cand.point(lambda v: 255 if v == 255 else 0)
        box = only_white.getbbox()
        if not box:
            break
        # bbox 첫 줄에서 255 픽셀 찾기
        seed = None
        for x in range(box[0], box[2]):
            if cp[x, box[1]] == 255:
                seed = (x, box[1])
                break
        ImageDraw.floodfill(cand, seed, TMP)
        count = cand.histogram()[TMP]
        cand = cand.point(lambda v, c=count: (BG if c >= 400 else KEEP) if v == TMP else v)
        cp = cand.load()
    alpha = cand.crop((1, 1, w + 1, h + 1)).point(lambda v: 0 if v == BG else 255)
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


def save_final(name, opaque_img):
    POSE_DIR.mkdir(parents=True, exist_ok=True)
    OPAQUE_DIR.mkdir(parents=True, exist_ok=True)
    opaque_img.convert("RGB").save(OPAQUE_DIR / f"{name}.png")
    remove_background(opaque_img).save(POSE_DIR / f"{name}.png")
    print(f"저장: assets/cupbunny/{name}.png (투명 배경)")


def compare_sheet(base_path, images, labels, out_path):
    """기준 그림과 후보들을 같은 높이로 나란히."""
    h, pad, label_h = 760, 30, 56
    tiles = [Image.open(base_path).convert("RGB")] + images
    tiles = [t.resize((round(t.width * h / t.height), h), Image.LANCZOS) for t in tiles]
    W = sum(t.width for t in tiles) + pad * (len(tiles) + 1)
    sheet = Image.new("RGB", (W, h + label_h + pad * 2), "#FFFFFF")
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(FONT), 34)
    x = pad
    for t, label in zip(tiles, ["기준"] + labels):
        sheet.paste(t, (x, pad))
        tw = d.textlength(label, font=font)
        d.text((x + (t.width - tw) / 2, pad + h + 10), label, font=font, fill="#3A3A3A")
        x += t.width + pad
    sheet.save(out_path)
    return out_path


def load_api_key():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("OPENAI_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                if key:
                    return key
    sys.exit("API 키가 없어요. KOOEN 폴더의 .env 파일에 OPENAI_API_KEY= 뒤에 키를 붙여넣고 저장해주세요.")


# ---------- 명령 ----------

def cmd_list(_):
    for n in all_pose_names():
        state = "완성" if (POSE_DIR / f"{n}.png").exists() else "-"
        print(f"{n:10s} {state}")


def cmd_original(a):
    """reference/ 이미지를 API 없이 그대로 포즈로 사용 (배경만 투명 처리)."""
    src = REF if a.file is None else ROOT / "reference" / a.file
    if not src.exists():
        sys.exit(f"reference 폴더에 파일이 없어요: {src.name}")
    save_final(a.pose, Image.open(src))


def cmd_mask(a):
    base, regions, _, _ = spec(a.pose)
    if not regions:
        sys.exit("고민 포즈는 원본 그대로라 마스크가 없어요.")
    img = Image.open(base).convert("RGBA")
    mask = build_mask(img.size, regions)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    sx, sy = img.size[0] / 1024, img.size[1] / 1536
    for x1, y1, x2, y2 in regions:
        od.rounded_rectangle((x1 * sx, y1 * sy, x2 * sx, y2 * sy), radius=40,
                             fill=(150, 120, 220, 90), outline=(120, 80, 200, 255), width=6)
    CAND_DIR.mkdir(parents=True, exist_ok=True)
    out = CAND_DIR / f"{a.pose}_마스크확인.png"
    Image.alpha_composite(img, overlay).save(out)
    print(f"바꿀 영역(보라색): {out.relative_to(ROOT)}")
    return mask


def cmd_estimate(a):
    per = COST_PER_IMAGE[a.quality]
    print(f"포즈 {a.pose} / 후보 {a.n}장 / 품질 {a.quality} / 모델 {MODEL}")
    print(f"예상 비용: 약 ${per * a.n:.2f} (1장 약 ${per:.2f}, 대략치)")


def cmd_make(a):
    if a.pose == "고민":
        sys.exit("고민 포즈는 원본 그대로예요: python tools/make_pose.py original")
    if not 1 <= a.n <= 3:
        sys.exit("후보는 한 번에 1~3장까지 만들 수 있어요.")
    cmd_estimate(a)
    if not a.yes:
        sys.exit("실제로 만들려면 --yes 를 붙여 실행하세요 (비용 발생).")
    from openai import OpenAI

    base, regions, prompt, extra = spec(a.pose)
    base_img = Image.open(base).convert("RGBA")
    if base_img.size != (1024, 1536):
        sys.exit(f"기준 이미지 크기가 1024x1536이 아니에요: {base_img.size}")
    CAND_DIR.mkdir(parents=True, exist_ok=True)
    base_png = CAND_DIR / "_기준.png"
    mask_png = CAND_DIR / "_마스크.png"
    base_img.save(base_png)
    build_mask(base_img.size, regions).save(mask_png)

    client = OpenAI(api_key=load_api_key())
    files = [open(base_png, "rb")] + [open(p, "rb") for p in extra]
    try:
        result = client.images.edit(
            model=MODEL,
            image=files if len(files) > 1 else files[0],
            mask=open(mask_png, "rb"),
            prompt=STYLE + " " + prompt,
            size=SIZE,
            quality=a.quality,
            n=a.n,
            output_format="png",
        )
    finally:
        for f in files:
            f.close()

    cands, labels = [], []
    for i, item in enumerate(result.data, 1):
        p = CAND_DIR / f"{a.pose}_{i}.png"
        p.write_bytes(base64.b64decode(item.b64_json))
        cands.append(Image.open(p).convert("RGB"))
        labels.append(f"후보 {i}")
    out = compare_sheet(base, cands, labels, CAND_DIR / f"{a.pose}_비교.png")
    print(f"후보 {len(cands)}장 저장, 비교 이미지: {out.relative_to(ROOT)}")


def cmd_pick(a):
    p = CAND_DIR / f"{a.pose}_{a.number}.png"
    if not p.exists():
        sys.exit(f"후보 파일이 없어요: {p.relative_to(ROOT)}")
    save_final(a.pose, Image.open(p))


def cmd_preview(_):
    names = [n for n in all_pose_names() if (POSE_DIR / f"{n}.png").exists()]
    if not names:
        sys.exit("완성된 포즈가 아직 없어요.")
    cw, ch, label_h = 300, 450, 56
    cols = 5
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new("RGB", (cw * cols, (ch + label_h) * rows), "#FFFFFF")
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(FONT), 32)
    for i, n in enumerate(names):
        img = Image.open(POSE_DIR / f"{n}.png")
        img.thumbnail((cw, ch), Image.LANCZOS)
        x, y = (i % cols) * cw, (i // cols) * (ch + label_h)
        sheet.paste(img, (x + (cw - img.width) // 2, y + (ch - img.height) // 2), img)
        tw = d.textlength(n, font=font)
        d.text((x + (cw - tw) / 2, y + ch + 8), n, font=font, fill="#3A3A3A")
    sheet.save(PREVIEW)
    print(f"미리보기: {PREVIEW.relative_to(ROOT)}")


def main():
    ap = argparse.ArgumentParser(description="컵토끼 포즈 만들기")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    o = sub.add_parser("original")
    o.add_argument("pose", nargs="?", default="고민")
    o.add_argument("file", nargs="?", default=None)
    sub.add_parser("preview")
    m = sub.add_parser("mask"); m.add_argument("pose")
    for name in ("estimate", "make"):
        s = sub.add_parser(name)
        s.add_argument("pose")
        s.add_argument("--n", type=int, default=2)
        s.add_argument("--quality", default="high", choices=list(COST_PER_IMAGE))
        if name == "make":
            s.add_argument("--yes", action="store_true")
    pk = sub.add_parser("pick"); pk.add_argument("pose"); pk.add_argument("number", type=int)
    a = ap.parse_args()
    {"list": cmd_list, "original": cmd_original, "mask": cmd_mask, "estimate": cmd_estimate,
     "make": cmd_make, "pick": cmd_pick, "preview": cmd_preview}[a.cmd](a)


if __name__ == "__main__":
    main()
