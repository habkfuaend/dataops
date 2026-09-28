#!/usr/bin/env python3
"""使用 FFmpeg 生成音频比特率筛选算子的本地测试数据集。"""

import json
import os
from pathlib import Path
import shutil
import subprocess


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "tests" / "data"


def find_ffmpeg():
    """支持环境变量、PATH，以及 winget 的常见安装目录。"""
    configured = os.environ.get("FFMPEG_PATH")
    if configured:
        return configured

    executable = shutil.which("ffmpeg")
    if executable:
        return executable

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        package_root = (
            Path(local_app_data)
            / "Microsoft"
            / "WinGet"
            / "Packages"
            / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
        )
        candidates = sorted(
            package_root.glob("ffmpeg-*-full_build/bin/ffmpeg.exe"),
            reverse=True,
        )
        if candidates:
            return str(candidates[0])

    raise RuntimeError(
        "未找到 ffmpeg。请重启终端，或设置 FFMPEG_PATH 为 ffmpeg 可执行文件路径。"
    )


def generate_audio(ffmpeg, filename, encoding_arguments, frequency):
    destination = DATA_DIR / filename
    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency={frequency}:sample_rate=44100:duration=2",
        "-vn",
        *encoding_arguments,
        str(destination),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or f"退出码 {result.returncode}"
        raise RuntimeError(f"生成 {filename} 失败：{detail}")


def main():
    ffmpeg = find_ffmpeg()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    fixtures = [
        ("tone_96k.mp3", ["-c:a", "libmp3lame", "-b:a", "96k"], 330),
        ("tone_128k.mp3", ["-c:a", "libmp3lame", "-b:a", "128k"], 440),
        ("tone_192k.mp3", ["-c:a", "libmp3lame", "-b:a", "192k"], 550),
        ("tone_320k.mp3", ["-c:a", "libmp3lame", "-b:a", "320k"], 660),
        ("tone_vbr.mp3", ["-c:a", "libmp3lame", "-q:a", "4"], 770),
        ("tone_pcm.wav", ["-c:a", "pcm_s16le", "-ac", "2"], 880),
    ]
    for filename, arguments, frequency in fixtures:
        generate_audio(ffmpeg, filename, arguments, frequency)

    (DATA_DIR / "corrupt.mp3").write_bytes(
        b"This is intentionally not a valid MP3 file.\n"
    )
    (DATA_DIR / "notes.txt").write_text(
        "该文件用于验证不支持的扩展名会被跳过。\n",
        encoding="utf-8",
    )

    manifest = {
        "description": "音频比特率筛选算子本地单元测试数据集",
        "generated_by": "generate_test_data.py",
        "files": [
            {"path": "tone_96k.mp3", "type": "CBR MP3", "expected_kbps": 96},
            {"path": "tone_128k.mp3", "type": "CBR MP3", "expected_kbps": 128},
            {"path": "tone_192k.mp3", "type": "CBR MP3", "expected_kbps": 192},
            {"path": "tone_320k.mp3", "type": "CBR MP3", "expected_kbps": 320},
            {
                "path": "tone_vbr.mp3",
                "type": "VBR MP3",
                "expected": "可读取正数平均比特率",
            },
            {
                "path": "tone_pcm.wav",
                "type": "PCM WAV",
                "expected_kbps": 1411.2,
            },
            {
                "path": "corrupt.mp3",
                "type": "损坏文件",
                "expected": "检测失败",
            },
            {
                "path": "notes.txt",
                "type": "非音频文件",
                "expected": "跳过",
            },
        ],
    }
    (DATA_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"已生成 {len(manifest['files'])} 个测试文件：{DATA_DIR}")


if __name__ == "__main__":
    main()
