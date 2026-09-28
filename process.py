"""平台内置工具 - 根据平均音频比特率筛选音频文件。"""

import json
import math
import os
import shutil
import subprocess


OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/workspace/output")
FFPROBE_PATH = os.environ.get("FFPROBE_PATH", "ffprobe")
FFPROBE_TIMEOUT_SECONDS = 30
SUPPORTED_EXTENSIONS = {
    ".aac",
    ".ac3",
    ".aif",
    ".aiff",
    ".alac",
    ".amr",
    ".ape",
    ".au",
    ".caf",
    ".dts",
    ".eac3",
    ".flac",
    ".m4a",
    ".mka",
    ".mp2",
    ".mp3",
    ".oga",
    ".ogg",
    ".opus",
    ".ra",
    ".tta",
    ".wav",
    ".wma",
    ".wv",
}


class ProbeError(Exception):
    """FFprobe 无法读取输入文件。"""


def collect_input_files(input_files):
    """优先使用平台传入的文件列表，否则扫描默认输入目录。"""
    if not isinstance(input_files, list):
        raise ValueError("input_files 必须是数组")
    if input_files:
        files = []
        for index, item in enumerate(input_files):
            if not isinstance(item, dict):
                raise ValueError(f"input_files[{index}] 必须是对象")
            local_path = item.get("local_path")
            relative_path = item.get("path", "")
            if not isinstance(local_path, str) or not local_path.strip():
                raise ValueError(
                    f"input_files[{index}].local_path 必须是非空字符串"
                )
            if not isinstance(relative_path, str):
                raise ValueError(f"input_files[{index}].path 必须是字符串")
            files.append((local_path, relative_path))
        return files

    files = []
    input_dir = os.environ.get("INPUT_DIR", "/workspace/input")
    if not os.path.isdir(input_dir):
        return files
    for root, _, names in os.walk(input_dir):
        for name in names:
            local_path = os.path.join(root, name)
            files.append((local_path, os.path.relpath(local_path, input_dir)))
    return files


def get_output_path(relative_path):
    """生成安全的输出路径，并确保文件不会写出 OUTPUT_DIR。"""
    relative_path = relative_path or "output.audio"
    if os.path.isabs(relative_path):
        relative_path = os.path.basename(relative_path)

    output_root = os.path.realpath(os.path.abspath(OUTPUT_DIR))
    destination = os.path.realpath(
        os.path.abspath(os.path.join(output_root, relative_path))
    )
    try:
        is_inside_output = os.path.commonpath([output_root, destination]) == output_root
    except ValueError:
        is_inside_output = False
    if not is_inside_output:
        raise ValueError("输出路径超出输出目录")
    return destination


def make_unique_relative_path(relative_path, used_paths):
    directory, filename = os.path.split(relative_path)
    stem, extension = os.path.splitext(filename)
    candidate = relative_path
    number = 2
    while os.path.normcase(os.path.normpath(candidate)).casefold() in used_paths:
        candidate = os.path.join(directory, f"{stem}_{number}{extension}")
        number += 1
    used_paths.add(os.path.normcase(os.path.normpath(candidate)).casefold())
    return candidate


def parse_bitrate_parameter(params, name, default):
    """读取正数比特率参数，拒绝布尔值、空值和非有限数字。"""
    value = params.get(name, default)
    if isinstance(value, bool):
        raise ValueError(f"{name} 必须是数字")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} 必须是数字") from exc
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{name} 必须是大于或等于 0 的有限数字")
    return number


def positive_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number <= 0:
        return None
    return number


def probe_audio_bitrate(local_path):
    """
    返回 (kbps, codec, source)。

    优先采用第一条音频流的 bit_rate；VBR 等场景缺少流码率时，
    回退到纯音频文件容器的 format.bit_rate。
    """
    command = [
        FFPROBE_PATH,
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=codec_name,bit_rate:format=bit_rate",
        "-of",
        "json",
        local_path,
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=FFPROBE_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ProbeError(
            f"未找到 FFprobe，请安装 FFmpeg 或设置 FFPROBE_PATH（当前值: {FFPROBE_PATH}）"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise ProbeError(f"FFprobe 处理超时（{FFPROBE_TIMEOUT_SECONDS} 秒）") from exc
    except OSError as exc:
        raise ProbeError(f"无法启动 FFprobe: {exc}") from exc

    if result.returncode != 0:
        detail = result.stderr.strip() or f"退出码 {result.returncode}"
        raise ProbeError(f"FFprobe 读取失败: {detail}")

    try:
        probe_data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ProbeError("FFprobe 返回了无效的 JSON 数据") from exc
    if not isinstance(probe_data, dict):
        raise ProbeError("FFprobe 返回了无效的数据结构")

    streams = probe_data.get("streams") or []
    if not isinstance(streams, list) or not streams:
        raise ProbeError("未检测到音频流")

    stream = streams[0]
    if not isinstance(stream, dict):
        raise ProbeError("FFprobe 返回了无效的音频流信息")
    codec = stream.get("codec_name") or "unknown"
    bitrate = positive_number(stream.get("bit_rate"))
    source = "音频流"
    if bitrate is None:
        format_info = probe_data.get("format") or {}
        if not isinstance(format_info, dict):
            raise ProbeError("FFprobe 返回了无效的容器信息")
        bitrate = positive_number(format_info.get("bit_rate"))
        source = "容器平均值"
    if bitrate is None:
        raise ProbeError("文件未提供可用的比特率信息")

    return bitrate / 1000.0, codec, source


def run(input_files, params):
    """
    输入：
        input_files: 文件列表，元素格式为 {'local_path': str, 'path': str}
        params: {'min_bitrate_kbps': number, 'max_bitrate_kbps': number}
    """
    logs = []
    output_files = []

    if not isinstance(params, dict):
        raise ValueError("params 必须是对象")
    min_bitrate = parse_bitrate_parameter(params, "min_bitrate_kbps", 128)
    max_bitrate = parse_bitrate_parameter(params, "max_bitrate_kbps", 320)

    if min_bitrate > max_bitrate:
        raise ValueError("最低比特率不能大于最高比特率")

    examined_count = 0
    completed_count = 0
    used_output_paths = set()
    for local_path, relative_path in collect_input_files(input_files):
        display_path = relative_path or os.path.basename(local_path)
        if not os.path.isfile(local_path):
            logs.append(f"跳过（文件不存在）: {display_path}")
            continue

        extension = os.path.splitext(local_path)[1].lower()
        if extension not in SUPPORTED_EXTENSIONS:
            logs.append(f"跳过（不支持的音频格式）: {display_path}")
            continue

        examined_count += 1
        try:
            bitrate, codec, bitrate_source = probe_audio_bitrate(local_path)
        except ProbeError as exc:
            logs.append(f"检测失败: {display_path} - {exc}")
            continue
        if not min_bitrate <= bitrate <= max_bitrate:
            logs.append(
                f"未通过: {display_path} - {bitrate:.2f} kbps，"
                f"要求 {min_bitrate:g}–{max_bitrate:g} kbps"
            )
            completed_count += 1
            continue

        output_relative_path = None
        try:
            output_relative_path = make_unique_relative_path(
                display_path, used_output_paths
            )
            destination = get_output_path(output_relative_path)
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.copy2(local_path, destination)
        except (OSError, ValueError) as exc:
            if output_relative_path is not None:
                used_output_paths.discard(
                    os.path.normcase(
                        os.path.normpath(output_relative_path)
                    ).casefold()
                )
            logs.append(f"输出失败: {display_path} - {exc}")
            continue

        output_files.append(
            {"path": output_relative_path, "local_path": destination}
        )
        completed_count += 1
        logs.append(
            f"已通过: {display_path} - {bitrate:.2f} kbps，"
            f"编码 {codec}，数据来源 {bitrate_source}"
        )

    if completed_count == 0:
        detail = "；".join(logs[:10]) if logs else "没有找到可检测的音频文件"
        if len(logs) > 10:
            detail += f"；另有 {len(logs) - 10} 条日志已省略"
        raise RuntimeError(f"没有音频文件检测成功：{detail}")

    return {
        "files": output_files,
        "message": (
            f"检测了 {examined_count} 个音频文件，"
            f"{len(output_files)} 个符合 {min_bitrate:g}–{max_bitrate:g} kbps"
        ),
        "logs": logs,
    }
