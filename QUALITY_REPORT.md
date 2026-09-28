# 综合质量验证报告

- 验证日期：2026-09-28
- 基线提交：`31173a816f2d822b90a1df2328d8d63ffe92791b`
- 验证环境：Windows、CPython 3.12.14 与 CPython 3.14.3

## 结果

| 检查项 | 结果 |
|---|---|
| Python 语法编译 | 通过 |
| 自动化单元测试 | 17/17 通过 |
| Python 3.12 回归 | 通过 |
| Python 3.14 回归 | 通过 |
| 参数与边界检查 | 通过 |
| 输出路径穿越防护 | 通过 |
| FFprobe 正常/回退/异常分支 | 通过 |
| 文件筛选、复制和重名处理 | 通过 |
| CI 配置 | 已建立（3.11/3.12/3.13） |
| 许可证与维护文档 | 已补齐 |
| GitHub Milestone | 规范与创建脚本已备妥，上传后需在线执行 |

## 重现命令

```powershell
python -m compileall -q main.py process.py generate_test_data.py tests
python -m unittest discover -s tests -p "test_*.py" -v
```

## GitHub 上线后检查

1. 确认 Quality Actions 三个 Python 版本全部通过。
2. 执行 `scripts/bootstrap_github_milestone.ps1` 创建真实 Milestone 和关联 Issue。
3. 在仓库 About 中设置描述与 Topics。
4. 端到端验证完成后创建 `v1.0.0` 标签或 Release。

