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

import os
import subprocess
import re
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
PUBLIC_DIR = PROJECT_ROOT / "public"
ROOT_TSX = PROJECT_ROOT / "src" / "Root.tsx"
OUT_DIR = PROJECT_ROOT / "out"


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

    relative_path = video_path.relative_to(PROJECT_ROOT)

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
    subprocess.run(["open", str(PUBLIC_DIR)])

    # macOS 原生弹窗：等你点“继续”后再继续执行
    os.system(r'''
    osascript <<EOF
    display dialog "请检查并修改 transcript.json\n\n修改完请点击「继续」开始渲染" buttons {"继续"} default button "继续"
    EOF
    ''')
    # ---------------------------------------------------------

    print("✔ 已确认继续渲染")


def update_root(video_filename):
    """精准更新 Root.tsx 中 staticFile 的路径"""
    print(f"▶ 更新 Root.tsx staticFile → {video_filename}")

    content = ROOT_TSX.read_text(encoding="utf-8")

    pattern = r'src:\s*staticFile\(\s*["\'`](.+?)["\'`]\s*\)'
    if not re.search(pattern, content):
        raise RuntimeError("❌ Root.tsx 中未找到 staticFile(...)")

    new_content = re.sub(
        pattern,
        f'src: staticFile("{video_filename}")',
        content
    )

    ROOT_TSX.write_text(new_content, encoding="utf-8")
    print("✔ Root.tsx 已更新")


def render_video():
    print("▶ 开始渲染视频...")

    output_file = OUT_DIR / "CaptionedVideo.mp4"

    if output_file.exists():
        output_file.unlink()

    result = subprocess.run(
        [
            "npx", "remotion", "render",
            "src/index.ts",
            "CaptionedVideo",
            str(output_file)
        ],
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
    try:
        print("=" * 60)
        print("🚀 开始自动渲染流程")
        print("=" * 60)

        video_file = find_single_mp4()
        original_filename = video_file.name

        transcribe(video_file)        # ← 已带人工审核
        update_root(original_filename)
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
