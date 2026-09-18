#!/usr/bin/env bash
# 在 WSL venv 中运行单元测试
# 用法：bash scripts/run_tests.sh
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/python -m unittest discover -s tests -t . -v
echo "==> 测试通过 ✅"
