"""카드 이미지를 이어 붙여 릴스 영상(1080x1920 MP4)을 만든다. API 사용 안 함.

실행 (KOOEN 폴더에서):
  python tools/make_reels.py        최신 주간기획의 릴스 전부
  python tools/make_reels.py 월     월요일 릴스만

입력: 최신 주간기획의 릴스 섹션(후킹 문구·캡션·해시태그) + make_cards로 만든 카드 이미지
출력: output/reels/[주차]/[요일]_[시리즈].mp4, 같은 이름의 커버 .jpg, 캡션 .txt
음악: 기본은 음악 없음
"""
import re
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_cards as mc  # noqa: E402

ROOT = mc.ROOT
REEL_DIR = ROOT / "output" / "reels"

W, H = 1080, 1920
FPS = 30
FADE = 0.2          # 컷 전환 페이드(초)
ZOOM = 0.0          # 컷마다 확대 효과 (2026-10-15 사용자 요청으로 끔. 켜려면 0.03)
CARD_W = 1000
CARD_Y = 500
BG = "#F7F7F8"


def parse_reels(text):
    """릴스 섹션 → [{day, series, topic, hook, caption, hashtags}]"""
    part = text.split("## 2. 릴스", 1)[1].split("\n## 3.", 1)[0]
    reels = []
    for sec in re.split(r"\n### ", part)[1:]:
        head = sec.splitlines()[0]
        bits = [b.strip() for b in head.split("·")]
        day = bits[0].split()[0]
        hook = re.search(r"후킹:\s*\*\*(.+?)\*\*", sec)
        # 인스타는 굵은 글씨(**)를 지원하지 않으므로 표시 제거
        caption = [l.strip()[2:].replace("**", "") for l in sec.split("⑤ 캡션:", 1)[1].split("- ⑥", 1)[0].splitlines()
                   if l.strip().startswith(">")] if "⑤ 캡션:" in sec else []
        tags = re.search(r"⑥ 해시태그:\s*(.+)", sec)
        reels.append(dict(day=day, series=bits[1] if len(bits) > 1 else "",
                          topic=bits[2] if len(bits) > 2 else "",
                          hook=hook.group(1) if hook else "",
                          caption=caption, hashtags=tags.group(1).strip() if tags else ""))
    return reels


def base_frame(hook):
    """배경 + 위쪽 후킹 문구 + 아래 작은 KOOEN."""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    size, lines, _ = mc.fit_lines([hook], 84, 54, W - 120, 300, 1.25)
    total = len(lines) * size * 1.25
    y = (CARD_Y - total) / 2 + 20
    for line in lines:
        x = (W - mc.text_width(line, size)) / 2
        mc.draw_text(d, (x, y), line, size, mc.INK)
        y += size * 1.25
    label = "KOOEN"
    mc.draw_text(d, ((W - mc.text_width(label, 40)) / 2, CARD_Y + CARD_W + 110), label, 40, mc.GRAY)
    return img


def card_frame(base, card_img, zoom):
    """카드 자리(1000x1000)에 살짝 확대한 카드를 가운데 기준으로 잘라 넣는다."""
    s = round(CARD_W * zoom)
    big = card_img.resize((s, s), Image.BICUBIC)
    off = (s - CARD_W) // 2
    crop = big.crop((off, off, off + CARD_W, off + CARD_W))
    frame = base.copy()
    frame.paste(crop, ((W - CARD_W) // 2, CARD_Y))
    return frame


def render(reel, cards, card_dir, out_mp4):
    imgs = []
    for c in cards:
        p = card_dir / f"{c['id']}.png"
        if not p.exists():
            sys.exit(f"카드 이미지가 없어요: {p.relative_to(ROOT)} → 먼저 /make-cards 를 실행해주세요.")
        imgs.append(Image.open(p).convert("RGB"))
    durations = [c["seconds"] or 2 for c in cards]
    base = base_frame(reel["hook"])

    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
           "-movflags", "+faststart", str(out_mp4)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    prev_last = None
    total_frames = 0
    for img, dur in zip(imgs, durations):
        n = round(dur * FPS)
        fade_n = round(FADE * FPS)
        last = None
        for i in range(n):
            frame = card_frame(base, img, 1 + ZOOM * i / max(n - 1, 1))
            if prev_last is not None and i < fade_n:
                frame = Image.blend(prev_last, frame, (i + 1) / (fade_n + 1))
            proc.stdin.write(frame.tobytes())
            last = frame
        prev_last = last
        total_frames += n
    proc.stdin.close()
    if proc.wait() != 0:
        sys.exit("영상 만들기에 실패했어요 (ffmpeg 오류).")

    # 커버: 후킹 문구 + 첫 카드
    card_frame(base, imgs[0], 1.0).save(out_mp4.with_suffix(".jpg"), quality=92)
    return total_frames / FPS


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    plan = mc.latest_plan()
    text = plan.read_text(encoding="utf-8")
    week = mc.week_of(plan)
    all_cards = mc.parse_cards(text)
    reels = [r for r in parse_reels(text) if not arg or r["day"] == arg]
    if not reels:
        sys.exit(f"'{arg}' 릴스가 주간기획에 없어요.")
    out_dir = REEL_DIR / week
    out_dir.mkdir(parents=True, exist_ok=True)
    card_dir = mc.IMG_DIR / week
    print(f"주간기획: {plan.name}")
    for r in reels:
        cards = [c for c in all_cards if re.fullmatch(rf"{r['day']}_\d+", c["id"])]
        name = f"{r['day']}_{r['series']}"
        mp4 = out_dir / f"{name}.mp4"
        secs = render(r, cards, card_dir, mp4)
        (out_dir / f"{name}_캡션.txt").write_text(
            "\n".join(r["caption"]) + "\n\n" + r["hashtags"] + "\n", encoding="utf-8")
        print(f"저장: {mp4.relative_to(ROOT)}  ({secs:.1f}초, 컷 {len(cards)}개) + 커버 .jpg + 캡션 .txt")


if __name__ == "__main__":
    main()
