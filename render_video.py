#!/usr/bin/env python3
"""
自动处理视频渲染流程：
1. 找到 public 目录中最新的 mp4 文件
2. 使用 node sub.mjs 进行转录
3. 更新 Root.tsx 中的 staticFile
4. 使用 npx remotion render 渲染视频
5. 将输出文件重命名为原始文件名
"""

import os
import subprocess
import re
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
PUBLIC_DIR = PROJECT_ROOT / "public"
ROOT_TSX = PROJECT_ROOT / "src" / "Root.tsx"
OUT_DIR = PROJECT_ROOT / "out"


def find_newest_mp4():
    """找到 public 目录中最新的 mp4 文件"""
    mp4_files = list(PUBLIC_DIR.glob("*.mp4"))
    
    if not mp4_files:
        raise FileNotFoundError("在 public 目录中未找到任何 mp4 文件")
    
    # 按修改时间排序，获取最新的
    newest_file = max(mp4_files, key=lambda f: f.stat().st_mtime)
    print(f"找到最新的视频文件: {newest_file.name}")
    return newest_file


def transcribe_video(video_path):
    """使用 node sub.mjs 对视频进行转录"""
    print(f"开始转录视频: {video_path.name}")
    
    # 构建相对于项目根目录的路径
    relative_path = video_path.relative_to(PROJECT_ROOT)
    
    result = subprocess.run(
        ["node", "sub.mjs", str(relative_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"转录失败: {result.stderr}")
    
    print("转录完成")
    
    # 检查 JSON 文件是否已生成
    json_path = video_path.with_suffix(".json")
    if not json_path.exists():
        raise FileNotFoundError(f"转录 JSON 文件未生成: {json_path}")


def update_root_tsx(video_filename):
    """更新 Root.tsx 中的 staticFile"""
    print(f"更新 Root.tsx 中的 staticFile 为: {video_filename}")
    
    content = ROOT_TSX.read_text(encoding="utf-8")
    
    # 使用正则表达式匹配 staticFile 中的文件名
    pattern = r'staticFile\("([^"]+)"\)'
    
    def replace_filename(match):
        return f'staticFile("{video_filename}")'
    
    new_content = re.sub(pattern, replace_filename, content)
    
    if new_content == content:
        raise ValueError(f"未找到 staticFile 调用，无法更新")
    
    ROOT_TSX.write_text(new_content, encoding="utf-8")
    print("Root.tsx 已更新")


def render_video():
    """使用 npx remotion render 渲染视频"""
    print("开始渲染视频...")
    
    # Remotion 渲染命令
    # 格式: npx remotion render <entry-file> <composition-id> <output-file>
    output_file = OUT_DIR / "CaptionedVideo.mp4"
    
    result = subprocess.run(
        [
            "npx", "remotion", "render",
            "src/index.ts",
            "CaptionedVideo",
            str(output_file)
        ],
        cwd=PROJECT_ROOT,
        capture_output=False  # 显示输出以便查看进度
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"视频渲染失败，退出码: {result.returncode}")
    
    print(f"视频渲染完成: {output_file}")
    return output_file


def rename_output(output_file, original_filename):
    """将输出文件重命名为原始文件名"""
    # 直接使用原始文件名
    new_path = OUT_DIR / original_filename
    
    if output_file.exists():
        # 如果目标文件已存在，先删除
        if new_path.exists():
            new_path.unlink()
        output_file.rename(new_path)
        print(f"输出文件已重命名为: {original_filename}")
        return new_path
    else:
        raise FileNotFoundError(f"输出文件不存在: {output_file}")


def main():
    """主函数"""
    try:
        print("=" * 60)
        print("开始自动视频渲染流程")
        print("=" * 60)
        
        # 1. 找到最新的 mp4 文件
        video_file = find_newest_mp4()
        original_filename = video_file.name
        
        # 2. 转录视频
        transcribe_video(video_file)
        
        # 3. 更新 Root.tsx
        update_root_tsx(original_filename)
        
        # 4. 渲染视频
        output_file = render_video()
        
        # 5. 重命名输出文件
        final_file = rename_output(output_file, original_filename)
        
        print("=" * 60)
        print("流程完成！")
        print(f"最终输出文件: {final_file}")
        print("=" * 60)
        
    except Exception as e:
        print(f"错误: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

