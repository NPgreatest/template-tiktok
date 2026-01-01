#!/usr/bin/env python3

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent
PUBLIC_DIR = PROJECT_ROOT / "public"
ROOT_TSX = PROJECT_ROOT / "src" / "Root.tsx"
OUT_DIR = PROJECT_ROOT / "out"


def sanitize_filename(name: str) -> str:
    ALLOWED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._- ")
    name = name.replace("\u00a0", " ")
    safe = [(ch if ch in ALLOWED else "_") for ch in name]
    name = "".join(safe)
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r"_+", "_", name)
    return name or "video.mp4"


def ensure_legal_video_name(video_path: Path) -> Path:
    sanitized = sanitize_filename(video_path.name)
    if sanitized == video_path.name:
        return video_path

    new_path = video_path.with_name(sanitized)
    if new_path.exists():
        new_path.unlink()

    # JSON 同步重命名
    old_json = video_path.with_suffix(".json")
    new_json = new_path.with_suffix(".json")
    if old_json.exists():
        if new_json.exists():
            new_json.unlink()
        old_json.rename(new_json)

    video_path.rename(new_path)
    print(f"✓ 已重命名: {video_path.name} → {new_path.name}")
    return new_path


def find_single_mp4():
    mp4s = list(PUBLIC_DIR.glob("*.mp4"))
    if not mp4s:
        raise FileNotFoundError("❌ public 下没有视频")
    if len(mp4s) > 1:
        raise RuntimeError("❌ public 下有多个视频，请清理")
    return mp4s[0]


def mac_dialog(msg):
    cmd = f'''osascript -e 'display dialog "{msg}" buttons {{"继续"}} default button "继续" with icon note' '''
    os.system(cmd)


def transcribe(video_path):
    rel = video_path.relative_to(PROJECT_ROOT).as_posix()
    print(f"▶ 转录 {rel}")

    result = subprocess.run(["node", "sub.mjs", rel],
                            cwd=PROJECT_ROOT,
                            capture_output=True,
                            text=True)

    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("❌ 转录失败")


def update_root(filename, template):
    txt = ROOT_TSX.read_text()

    txt = re.sub(r'src:\s*staticFile\(\s*["\'`](.+?)["\'`]\s*\)',
                 f'src: staticFile("{filename}")', txt)

    txt = re.sub(r'template:\s*["\'`](.+?)["\'`]',
                 f'template: "{template}"', txt)

    ROOT_TSX.write_text(txt)
    print("✔ Root.tsx 已更新")


def render_video():
    OUT_DIR.mkdir(exist_ok=True)
    outfile = OUT_DIR / "CaptionedVideo.mp4"
    if outfile.exists():
        outfile.unlink()

    cmd = ["npx", "remotion", "render", "src/index.ts",
           "CaptionedVideo", str(outfile)]
    result = subprocess.run(cmd, cwd=PROJECT_ROOT,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(result.stderr.decode())
        raise RuntimeError("❌ 渲染失败")

    return outfile


def rename_output(output, name):
    final = OUT_DIR / name
    if final.exists():
        final.unlink()
    output.rename(final)
    print(f"✔ 最终输出: {final}")
    return final


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", default="tiktok")
    parser.add_argument("--skip-transcribe", action="store_true")
    args = parser.parse_args()

    print("🚀 启动渲染流水线")

    video = find_single_mp4()
    video = ensure_legal_video_name(video)
    final_name = video.name

    json_path = video.with_suffix(".json")

    if not json_path.exists() and not args.skip_transcribe:
        transcribe(video)

    subprocess.run(["open", str(PUBLIC_DIR)])
    mac_dialog("人工检查。\n完成后点击继续开始渲染。")

    update_root(final_name, args.template)
    output = render_video()
    rename_output(output, final_name)


if __name__ == "__main__":
    main()
