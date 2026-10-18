"""KOOEN 사연툰 manifest를 카드 이미지와 무음 릴스로 만든다.

실행:
  .venv/bin/python tools/build_storytoon.py output/storytoon/.../manifest.json
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
W, H = 941, 1672
VIDEO_W, VIDEO_H = 1080, 1920
FPS = 30
FADE = 0.18
INK = "#171717"
CORAL = "#E97870"
LAVENDER = "#EFE7FF"
GRAY = "#8A8A8A"
FONT_PATH = ROOT / "assets" / "fonts" / "Jua-Regular.ttf"


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size)


def centered(draw: ImageDraw.ImageDraw, text: str, y: int, size: int, fill: str) -> int:
    f = font(size)
    box = draw.textbbox((0, 0), text, font=f)
    width = box[2] - box[0]
    draw.text(((W - width) / 2, y), text, font=f, fill=fill)
    return box[3] - box[1]


def badge(draw: ImageDraw.ImageDraw, text: str) -> None:
    f = font(34)
    box = draw.textbbox((0, 0), text, font=f)
    width = box[2] - box[0]
    x0 = (W - width) / 2 - 28
    y0 = 62
    draw.rounded_rectangle((x0, y0, x0 + width + 56, y0 + 60), radius=30, fill="#FBE1DF")
    draw.text(((W - width) / 2, y0 + 9), text, font=f, fill="#B95555")


def render_card(base: Path, card: dict, out: Path) -> Image.Image:
    img = Image.open(base).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    if card.get("badge"):
        badge(draw, card["badge"])

    y = int(card.get("title_y", 145))
    size = int(card.get("font_size", 72))
    gap = int(card.get("line_gap", 10))
    accent = set(card.get("accent_lines", []))
    for index, line in enumerate(card["lines"]):
        height = centered(draw, line, y, size, CORAL if index in accent else INK)
        y += height + gap

    prompt = card.get("bottom_prompt")
    if prompt:
        f = font(int(card.get("prompt_size", 34)))
        box = draw.textbbox((0, 0), prompt, font=f)
        width = box[2] - box[0]
        x0 = (W - width) / 2 - 30
        y0 = int(card.get("prompt_y", 1510))
        draw.rounded_rectangle((x0, y0, x0 + width + 60, y0 + 58), radius=29, fill=LAVENDER)
        draw.text(((W - width) / 2, y0 + 9), prompt, font=f, fill=INK)

    footer = "@kooen.official"
    f = font(25)
    box = draw.textbbox((0, 0), footer, font=f)
    draw.text(((W - (box[2] - box[0])) / 2, H - 48), footer, font=f, fill=GRAY)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, quality=95)
    return img


def build_video(images: list[Image.Image], durations: list[float], output: Path) -> float:
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{VIDEO_W}x{VIDEO_H}",
        "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "18", "-preset", "medium", "-movflags", "+faststart", str(output),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    previous = None
    total = 0
    for image, duration in zip(images, durations):
        frame = image.resize((VIDEO_W, VIDEO_H), Image.Resampling.LANCZOS)
        frames = round(duration * FPS)
        fade_frames = round(FADE * FPS)
        for index in range(frames):
            current = frame
            if previous is not None and index < fade_frames:
                current = Image.blend(previous, frame, (index + 1) / (fade_frames + 1))
            proc.stdin.write(current.tobytes())
        previous = frame
        total += frames
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("릴스 렌더링에 실패했습니다.")
    images[0].resize((VIDEO_W, VIDEO_H), Image.Resampling.LANCZOS).save(
        output.with_name(output.stem + "_커버.jpg"), quality=94
    )
    return total / FPS


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("manifest.json 경로가 필요합니다.")
    manifest_path = Path(sys.argv[1]).resolve()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    base_dir = manifest_path.parent
    rendered = []
    durations = []
    for card in data["cards"]:
        rendered.append(render_card(base_dir / card["source"], card, base_dir / card["output"]))
        durations.append(float(card["duration"]))
    seconds = build_video(rendered, durations, base_dir / data["video"])
    print(f"카드 {len(rendered)}장, 릴스 {seconds:.1f}초 생성 완료")


if __name__ == "__main__":
    main()
