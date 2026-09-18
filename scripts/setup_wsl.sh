#!/usr/bin/env bash
# 一键环境搭建（WSL Ubuntu）：创建 venv + 安装依赖 + 初始化 git（可选）
#
# 用法（在项目根目录执行）：
#   bash scripts/setup_wsl.sh
# 跳过 git 初始化：
#   bash scripts/setup_wsl.sh --no-git
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> 使用 $(python3 --version) / $(git --version)"
echo "==> 创建 venv (.venv)"
python3 -m venv .venv
echo "==> 升级 pip 并安装依赖"
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

if [[ "${1:-}" != "--no-git" ]]; then
  if [ ! -d .git ]; then
    echo "==> git init"
    git init -b main
    if ! git config user.name >/dev/null 2>&1; then
      git config user.name "$USER"
      git config user.email "$USER@local"
    fi
    echo "==> 首次提交"
    git add -A
    git commit -m "chore: 阶段0 基建（目录结构/架构文档/骨架代码）" || true
  else
    echo "==> 已存在 .git，跳过 git init"
  fi
fi

echo "==> ✅ 环境就绪。激活 venv： source .venv/bin/activate"
