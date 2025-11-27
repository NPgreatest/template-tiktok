#!/usr/bin/env python3
"""
自动处理视频渲染流程：
1. 找到 public 目录中唯一的 mp4 文件
2. 使用 node sub.mjs 进行转录
3. 打开 transcript.json 供你人工校对
4. 弹出 macOS 原生对话框等待你确认
5. 更新 Root.tsx 中的 staticFile 路径
6. 使用 npx remotion render 渲染视频
7. 将输出文件重命名为原始文件名
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
PUBLIC_DIR = PROJECT_ROOT / "public"
ROOT_TSX = PROJECT_ROOT / "src" / "Root.tsx"
OUT_DIR = PROJECT_ROOT / "out"
ALLOWED_TEMPLATES = {"tiktok", "bottom_karaoke"}


def sanitize_filename(name: str) -> str:
    """Make a transcription-safe filename (for whisper on Windows)."""
    name = name.replace("\u00a0", " ")
    safe = []
    for ch in name:
        if re.match(r"[A-Za-z0-9._\\-\\s]", ch):
            safe.append(ch)
        else:
            safe.append("_")
    sanitized = re.sub(r"[\\s]+", " ", "".join(safe)).strip()
    sanitized = re.sub(r"_+", "_", sanitized)
    return sanitized or "video.mp4"


def ensure_legal_video_name(video_path: Path) -> Path:
    """Rename the video to a sanitized filename (no copies)."""
    sanitized_name = sanitize_filename(video_path.name)
    if sanitized_name == video_path.name:
        return video_path

    sanitized_path = video_path.with_name(sanitized_name)
    if sanitized_path.exists():
        sanitized_path.unlink()

    # 如果已有旧的字幕 JSON，重命名保持同步
    old_json = video_path.with_suffix(".json")
    new_json = sanitized_path.with_suffix(".json")
    if old_json.exists():
        if new_json.exists():
            new_json.unlink()
        old_json.rename(new_json)

    video_path.rename(sanitized_path)
    print(f"ℹ️  已重命名文件: {video_path.name} → {sanitized_path.name}")
    return sanitized_path


def find_single_mp4():
    """确保 public 中只有 1 个 mp4 文件，并返回它。"""
    mp4_files = list(PUBLIC_DIR.glob("*.mp4"))

    if not mp4_files:
        raise FileNotFoundError("❌ public 目录中没有 mp4 文件")

    if len(mp4_files) > 1:
        raise RuntimeError(f"❌ public 目录中有多个 mp4 文件（共 {len(mp4_files)} 个），请先清理")

    video = mp4_files[0]
    print(f"▶ 找到视频文件: {video.name}")
    return video


def transcribe(video_path):
    """使用 node sub.mjs 进行视频转录，并人工审核"""
    print(f"▶ 开始转录: {video_path.name}")

    # 使用 POSIX 风格路径避免 Windows 反斜杠导致的转义问题
    relative_path = video_path.relative_to(PROJECT_ROOT).as_posix()

    result = subprocess.run(
        ["node", "sub.mjs", str(relative_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("❌ 转录失败")

    # 检查 JSON 文件
    # 优先使用转录输入同名的 json
    json_path = video_path.with_suffix(".json")
    if not json_path.exists():
        # 在 public 下查找任意 .json 文件
        json_candidates = list(video_path.parent.glob(f"{video_path.stem}*.json"))
        if not json_candidates:
            raise FileNotFoundError("❌ 找不到生成的 transcript JSON")
        json_path = json_candidates[0]
    if not json_path.exists():
        raise FileNotFoundError(f"❌ 转录 JSON 未生成: {json_path}")

    print("✔ 转录完成")

    # ---------------------------------------------------------
    # ⭐⭐ 新增部分：打开 transcript.json 并等待人工审核 ⭐⭐
    # ---------------------------------------------------------

    print("✏️ 打开 transcript.json 供你人工修改...")
    opener = None
    if sys.platform.startswith("darwin"):
        opener = ["open", str(PUBLIC_DIR)]
    elif os.name == "nt":
        opener = ["explorer", str(PUBLIC_DIR)]
    else:
        opener = ["xdg-open", str(PUBLIC_DIR)]

    try:
        subprocess.run(opener, check=False)
    except FileNotFoundError:
        print("⚠️ 无法自动打开目录，请手动检查 public 下的字幕 JSON")

    if sys.platform.startswith("darwin"):
        os.system(
            r'''
        osascript <<EOF
        display dialog "请检查并修改 transcript.json\n\n修改完请点击「继续」开始渲染" buttons {"继续"} default button "继续"
        EOF
        '''
        )
    else:
        input("请检查并修改 transcript.json，完成后按回车继续渲染...")
    # ---------------------------------------------------------

    print("✔ 已确认继续渲染")

    # 无需清理副本，因为已直接重命名原文件


def update_root(video_filename, template):
    """精准更新 Root.tsx 中 staticFile 的路径和模板"""
    print(f"▶ 更新 Root.tsx staticFile → {video_filename}, template → {template}")

    content = ROOT_TSX.read_text(encoding="utf-8")

    pattern = re.compile(
        r"src:\s*staticFile\(\s*['\"`](.+?)['\"`]\s*,?\s*\)",
        re.DOTALL,
    )
    match = pattern.search(content)
    if not match:
        raise RuntimeError("❌ Root.tsx 中未找到 staticFile(...)，请确认 defaultProps.src 存在")

    new_content = pattern.sub(f'src: staticFile("{video_filename}")', content)

    template_pattern = re.compile(
        r'template:\s*["\'`](.+?)["\'`]\s*,?',
        re.DOTALL,
    )
    if not re.search(template_pattern, new_content):
        raise RuntimeError("❌ Root.tsx 中未找到 template: \"...\"")

    new_content = re.sub(
        template_pattern,
        f'template: "{template}"',
        new_content
    )

    ROOT_TSX.write_text(new_content, encoding="utf-8")
    print("✔ Root.tsx 已更新")


def render_video():
    print("▶ 开始渲染视频...")

    output_file = OUT_DIR / "CaptionedVideo.mp4"

    if output_file.exists():
        output_file.unlink()

    if not OUT_DIR.exists():
        OUT_DIR.mkdir(parents=True, exist_ok=True)

    npx_cmd = shutil.which("npx.cmd") if os.name == "nt" else shutil.which("npx")
    if not npx_cmd:
        raise FileNotFoundError("❌ 未找到 npx，请确认已安装 Node.js/npm 并在 PATH 中")

    cmd = [
        npx_cmd,
        "remotion",
        "render",
        "src/index.ts",
        "CaptionedVideo",
        str(output_file),
    ]

    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,      # 不显示 stdout
        stderr=subprocess.DEVNULL       # 不显示 stderr
    )

    if result.returncode != 0:
        raise RuntimeError("❌ 渲染失败")

    print(f"✔ 渲染完成: {output_file}")
    return output_file



def rename_output(output_file, original_filename):
    """将渲染结果重命名为原视频的文件名"""
    final_path = OUT_DIR / original_filename

    if final_path.exists():
        final_path.unlink()

    output_file.rename(final_path)
    print(f"✔ 视频已重命名为: {final_path}")
    return final_path


def main():
    parser = argparse.ArgumentParser(description="自动转录并渲染 Remotion 视频")
    parser.add_argument(
        "--template",
        default="tiktok",
        choices=sorted(ALLOWED_TEMPLATES),
        help="选择字幕模板",
    )
    parser.add_argument(
        "--skip-transcribe",
        action="store_true",
        help="跳过转录（要求 public 下已存在对应 JSON）",
    )
    args = parser.parse_args()
    template = args.template

    try:
        print("=" * 60)
        print("🚀 开始自动渲染流程")
        print("=" * 60)

        video_file = find_single_mp4()
        video_file = ensure_legal_video_name(video_file)
        original_filename = video_file.name

        subtitles_json = video_file.with_suffix(".json")
        should_skip = subtitles_json.exists() or args.skip_transcribe
        if should_skip and subtitles_json.exists():
            print("⏭ 检测到同名字幕 JSON，自动跳过转录")
        elif args.skip_transcribe:
            print("⏭ 跳过转录")
            if not subtitles_json.exists():
                raise FileNotFoundError("❌ 需要先生成字幕 JSON，未找到对应文件")
        else:
            transcribe(video_file)        # ← 已带人工审核

        update_root(original_filename, template)
        output = render_video()
        final = rename_output(output, original_filename)

        print("=" * 60)
        print(f"🎉 完成！输出文件：{final}")
        print("=" * 60)

    except Exception as e:
        print(e)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
