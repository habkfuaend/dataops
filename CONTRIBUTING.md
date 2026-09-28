# 贡献指南

## 开发环境

- Python 3.11 或更高版本
- 仅在生成真实音频测试数据或执行端到端验证时需要 FFmpeg / FFprobe

## 提交前检查

```powershell
python -m compileall -q main.py process.py generate_test_data.py tests
python -m unittest discover -s tests -p "test_*.py" -v
```

所有新功能和缺陷修复都应包含对应测试。不要提交 `tests/data/`、
`qa-output/`、虚拟环境或 Python 缓存。

## Pull Request 要求

1. 描述改动目的、验证方法和潜在风险。
2. 关联对应 Issue 和 Milestone。
3. 确保 Quality CI 全部通过。
4. 涉及用户行为变化时同步更新 README。

