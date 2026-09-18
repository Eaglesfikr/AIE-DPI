# rules/ — 规则文件输出目录

规则文件是「特征挖掘工具」与「DPI 引擎」的接口契约。

- 由 `src/feature_miner.rule_gen` 生成，YAML 格式，可解释、可人工修正。
- DPI 引擎（engine/dpi_engine）直接加载。
- 每场景一个文件（阶段 1 起）：`social.yaml`、`im_behavior.yaml` 等。
- 本目录文件默认不纳入版本管理（可再生成），仅保留本说明。
