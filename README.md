# 音频比特率筛选工具

读取音频文件的平均比特率，仅输出位于指定范围内的文件。上下限均包含在
筛选范围内。通过筛选的文件会原样复制，不重新编码，因此不会改变音质、
编码格式或元数据。

## 功能与规则

1. 优先读取第一条音频流的 `bit_rate`。
2. 流未提供码率时，回退到容器的平均 `bit_rate`。
3. 无音频流、码率不可用、文件损坏或 FFprobe 执行失败时跳过文件并记录原因。
4. 输出路径限制在 `OUTPUT_DIR` 中；重名文件自动添加 `_2`、`_3` 等后缀。

支持 AAC、AC3、AIFF、ALAC、AMR、APE、CAF、DTS、FLAC、M4A、MKA、
MP2、MP3、OGG、Opus、WAV、WMA、WavPack 等常见扩展名。

> FLAC、WAV 等无损或未压缩音频的比特率主要由采样率、位深和声道数决定，
> 不能直接代表听感音质。

## 参数

| 参数 | 说明 | 默认值 |
|---|---|---:|
| `min_bitrate_kbps` | 最低音频比特率（kbps） | `128` |
| `max_bitrate_kbps` | 最高音频比特率（kbps） | `320` |

参数必须是大于或等于 0 的有限数字，且最低值不能大于最高值。

## 运行环境

- Python 3.11 或更高版本
- FFmpeg / FFprobe
- 默认输入目录：`/workspace/input/`（只读）
- 默认输出目录：`/workspace/output/`（写入）

项目没有 Python 第三方运行时依赖。安装 FFmpeg 后会同时获得 FFprobe：

```bash
ffprobe -version
```

也可以通过环境变量指定路径和目录：

```bash
FFPROBE_PATH=/opt/ffmpeg/bin/ffprobe
INPUT_DIR=/workspace/input
OUTPUT_DIR=/workspace/output
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

将 JSON 写入标准输入：

```bash
python main.py < input.json
```

成功时输出包含 `files`、`message` 和 `logs` 的 JSON 对象。

## 自动化测试

无需生成音频即可运行完整单元测试；测试通过 Mock 覆盖 FFprobe 的正常、回退
和异常分支，并覆盖参数校验、路径安全、边界值、文件复制与重名处理：

```powershell
python -m compileall -q main.py process.py generate_test_data.py tests
python -m unittest discover -s tests -p "test_*.py" -v
```

如需执行真实音频手工/端到端验证：

```powershell
python generate_test_data.py
```

该命令在 `tests/data/` 生成 CBR MP3、VBR MP3、PCM WAV、损坏音频和非音频
样本；此目录属于生成物，不提交到 Git。GitHub Actions 会在 Python
3.11、3.12 和 3.13 上自动执行编译及单元测试。

## 文件结构

| 文件或目录 | 说明 |
|---|---|
| `main.py` | 平台统一入口 |
| `process.py` | FFprobe 检测、筛选和文件输出逻辑 |
| `config.json` | 节点输入、输出和参数配置 |
| `tests/` | 可重复执行的自动化单元测试 |
| `.github/workflows/quality.yml` | 多版本 Python CI 门禁 |
| `docs/milestone-v1.0.md` | v1.0 线上 Milestone 创建及验收规范 |
| `scripts/bootstrap_github_milestone.ps1` | 创建线上 Milestone 和验收 Issue |
| `CONTRIBUTING.md` | 贡献和 PR 要求 |
| `SECURITY.md` | 安全问题报告策略 |
| `LICENSE` | MIT 许可证 |

## 发布与项目管理

首个发布目标和验收 Issue 清单位于
[`docs/milestone-v1.0.md`](docs/milestone-v1.0.md)。仓库上传 GitHub 后，应据此
创建真实 Milestone、建立并关联 Issue；只有文档而没有线上 Milestone 不视为
完成项目管理验收。

安装并登录 GitHub CLI 后，可在仓库根目录执行：

```powershell
.\scripts\bootstrap_github_milestone.ps1
```

## 已知限制

- 实际可解析格式取决于运行环境中的 FFmpeg 构建。
- 容器平均码率仅在音频流没有提供码率时使用。
- 工具按文件报告失败，不会尝试修复或重新编码损坏的音频。
