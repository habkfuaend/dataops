#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ========================================================
# 平台统一入口 - 请勿修改此文件
# 工作流运行时由 tool-runner 容器自动调用
# 用户只需实现 process.py 中的 run() 函数
# ========================================================

import json
import sys

from process import run


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        input_data = {}
    input_files = input_data.get("input_files", [])
    params = input_data.get("params", {})
    result = run(input_files, params)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
