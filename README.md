# 音频比特率筛选工具

## 功能

接收音频文件，使用 FFprobe 读取第一条音频流的平均比特率，仅输出比特率位于指定范围内的文件。最低值和最高值均包含在筛选范围内。

筛选通过的文件会原样复制，不会重新编码，因此不会改变音质、编码格式或文件元数据。

## 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `min_bitrate_kbps` | 最低音频比特率，单位 kbps | `128` |
| `max_bitrate_kbps` | 最高音频比特率，单位 kbps | `320` |

## 比特率读取规则

1. 优先读取第一条音频流的 `bit_rate`。
2. 对缺少流比特率的 VBR 文件，回退到容器的平均 `bit_rate`。
3. 无法取得比特率或未检测到音频流时跳过文件，并在日志中说明原因。

当前支持常见的 AAC、AC3、AIFF、ALAC、AMR、APE、CAF、DTS、FLAC、M4A、MKA、MP2、MP3、OGG、Opus、WAV、WMA、WavPack 等扩展名。

> FLAC、WAV 等无损或未压缩音频的比特率主要由采样率、位深和声道数决定，不能直接代表听感音质。

## 文件结构

| 文件 | 说明 | 是否可编辑 |
|------|------|-----------|
| `main.py` | 平台统一入口，运行时自动调用 | 不可修改 |
| `process.py` | FFprobe 检测、筛选与文件输出逻辑 | 可修改 |
| `config.json` | 节点输入、输出和筛选参数配置 | 可修改 |
| `requirements.txt` | Python 依赖说明 | 按需修改 |

## 运行环境

- Python 3.11
- FFmpeg / FFprobe
- 输入目录：`/workspace/input/`（只读）
- 输出目录：`/workspace/output/`（写入）

安装 FFmpeg 后会同时获得 FFprobe。可用以下命令检查：

```bash
ffprobe -version
```

也可以通过环境变量指定可执行文件：

```bash
FFPROBE_PATH=/opt/ffmpeg/bin/ffprobe
```

## 调用示例

```json
{
  "input_files": [
    {
      "local_path": "/workspace/input/example.mp3",
      "path": "example.mp3"
    }
  ],
  "params": {
    "min_bitrate_kbps": 128,
    "max_bitrate_kbps": 320
  }
}
```

## 本地单元测试

首次测试或需要重建数据集时运行：

```powershell
python generate_test_data.py
```

运行全部单元测试：

```powershell
python -m unittest discover -s tests -v
```

测试数据位于 `tests/data/`，覆盖 CBR MP3、VBR MP3、PCM WAV、损坏音频和非音频文件。测试过程使用系统临时输出目录，不会污染算子的正式输出目录。
