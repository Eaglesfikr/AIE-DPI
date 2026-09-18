# data/ — 数据目录

| 子目录 | 内容 | 说明 |
|---|---|---|
| `raw/` | 原始 PCAP（按批次 `batch_YYYYMMDD/`） | 不纳入版本管理 |
| `processed/` | 会话 JSON / 特征 CSV 中间结果 | 不纳入版本管理 |
| `labeled/` | 自建标注数据集（交付件） | manifest.csv + 分类 pcap |

组织与标注格式见 [docs/数据标注约定.md](../docs/%E6%95%B0%E6%8D%AE%E6%A0%87%E6%B3%A8%E7%BA%A6%E5%AE%9A.md)。
