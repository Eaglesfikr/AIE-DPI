# AIE-DPI — 赛题4：智能化辅助分析·应用及精细化行为特征挖掘识别

> 题目背景见 [赛题.md](赛题.md)，执行计划见 [TODO.md](TODO.md)。

## 项目定位

构建两套**独立又配套**的模块，解决 TLS 1.3 / QUIC / 私有加密协议下的大规模应用识别与精细化行为区分：

| 模块 | 定位 | 职责 |
|---|---|---|
| **智能化加密流量特征挖掘工具**（`src/feature_miner/`） | 离线·研究 | 解析会话 → 提取基础/高级特征 → 智能总结可用识别方案 → 产出**规则文件** |
| **高效 DPI 规则识别引擎**（`engine/dpi_engine/`） | 在线·识别 | 加载挖掘工具产出的规则文件 → 高效分层匹配 → 输出**识别结果** |

两个模块独立工作，识别维度上互相配合（规则文件是两者的接口契约）。

## 识别场景（按实现顺序）

1. **场景一（先做）**：社交应用分类（微信 / WhatsApp / Telegram 等）
2. **场景二**：IM 精细行为（语音 vs 视频通话、发文字消息聊天）
3. **场景三**：社交应用发文字贴行为（Facebook / X / Instagram）
4. **场景四**：匿名工具流量检测（Tor / Psiphon / Session）

## 目录结构

```
AIE-DPI/
├── src/feature_miner/     # 智能化特征挖掘工具
│   ├── parser/            # 加密流量解析与会话重组
│   ├── features/          # 基础/高级特征维度提取
│   ├── analyzer/          # 特征智能分析与识别方案总结
│   └── rule_gen/          # 规则文件生成器
├── engine/dpi_engine/     # 高效 DPI 规则识别引擎
├── data/
│   ├── raw/               # 原始 PCAP
│   ├── processed/         # 会话重组/特征中间结果
│   └── labeled/           # 自建标注数据集（交付件）
├── rules/                 # 规则文件输出（引擎输入）
├── docs/                  # 架构设计、数据标注约定等
├── scripts/               # 抓包/建库/pipeline 脚本
├── tests/                 # 单元测试
├── requirements.txt       # 依赖清单
└── TODO.md                # 执行计划
```

## 环境要求

- Python 3.10+（本机尚未安装，见 README 下方「环境准备」）
- git（可选，用于版本管理）
- 依赖：`pip install -r requirements.txt`

## 环境准备（尚未完成）

当前机器没有可用的 Python 解释器和 git。安装参考：

```powershell
# 方式一：winget 安装
winget install Python.Python.3.12
winget install Git.Git

# 方式二：微软商店
# 搜索 "Python 3.12" 安装

# 安装后验证
python --version && pip --version
git --version
```

## 快速开始（阶段 1 后具备）

```bash
# 1. 抓包并存放到 data/raw/（参考 scripts/ 中的脚本）
# 2. 会话重组 + 特征提取
python -m src.feature_miner.pipeline --input data/raw --output data/processed
# 3. 智能分析与规则生成（输出到 rules/）
python -m src.feature_miner.analyze --label data/labeled/social.csv --out rules/social.yaml
# 4. DPI 引擎加载规则并识别
python -m engine.dpi_engine.cli --rules rules/social.yaml --input data/raw/sample.pcap
```

## 指标基准（验收）

特征有效率 ≥ 80%（人工修正后 ≥ 90%）；识别召回率 ≥ 98%、准确率 ≥ 95%、精确率 ≥ 95%、假阳率 ≤ 5%；Android / iOS / PC 跨平台。

## 交付件

源代码（两模块）· 工具/引擎技术说明书 · 测试报告 · 部署与使用手册 · 自建标注数据集。
