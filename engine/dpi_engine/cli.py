"""引擎 CLI（阶段 1 已实现，对应 TODO 2.1）。

当前输入为 joyfuljay 产出的特征 CSV（每行一个流/会话）。流程：
	加载规则 → 逐行转特征字典 → 分层匹配 → DetectionResult → 输出 CSV + 统计。

用法：
	.venv/bin/python -m engine.dpi_engine.cli \
		--rules rules/social.yaml \
		--input data/processed/features_<app>.csv \
		[--out data/processed/detections.csv]
	可选 --true-label-col <列名>（如 app）打印每类命中率，便于人工核查规则效果。

输入格式：
	--format auto|csv（默认 auto，按扩展名 .csv 识别为特征矩阵）
	pcap 输入留待特征管线接入，当前统一走"预提取特征 CSV"。
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from .loader import RuleLoader
from .matcher import RuleMatcher

# 非特征（标识/血缘）列，不参与匹配
_NON_FEATURE = {"pcap", "app", "src_ip", "dst_ip", "start_time", "end_time",
				"time_first", "time_last", "flow_stat", "hdr_desc", "__label__"}


def _row_features(row: pd.Series) -> dict:
	"""把一行转成特征字典；只保留非 NaN、非血缘的数值/字符串特征。"""
	f = {}
	for col, val in row.items():
		if col in _NON_FEATURE:
			continue
		if pd.isna(val):
			continue
		f[col] = val
	return f


def run(rules_path: str, input_csv: str, out_path: str | None,
		true_label_col: str | None) -> None:
	compiled = RuleLoader().load(rules_path)
	matcher = RuleMatcher(compiled)
	n_rules = sum(len(r) for r in compiled["by_cost"].values())
	print(f"== 已加载规则文件: {rules_path}  (schema {compiled['schema_version']}，"
		  f"目标 {compiled['target']}，共 {n_rules} 条规则，"
		  f"分层 { {k: len(v) for k, v in compiled['by_cost'].items()} })")

	df = pd.read_csv(input_csv)
	print(f"== 输入特征: {df.shape[0]} 流 × {df.shape[1]} 列")

	rows = []
	stat_apps: Counter = Counter()
	for idx, row in df.iterrows():
		features = _row_features(row)
		res = matcher.classify(features)
		session_id = f"flow_{idx}"
		rows.append({
			"session_id": session_id,
			"app": res["app"],
			"confidence": res["confidence"],
			"matched_rule_id": res["matched_rule_id"] or "",
			"cost": res["cost"] or "",
			"true_label": str(row.get("app", "")) if "app" in df.columns else "",
		})
		stat_apps[res["app"]] += 1

	out = pd.DataFrame(rows)
	print("== 识别结果分布:", dict(stat_apps))
	hit = (out["matched_rule_id"] != "").mean()
	print(f"== 规则命中率: {hit * 100:.1f}%")

	if true_label_col and true_label_col in df.columns:
		out["true_label"] = df[true_label_col].astype(str)
		# 按真实标签 × 判定交叉表（人工核查规则是否贴合）
		cross = out.groupby(["true_label", "app"]).size().unstack(fill_value=0)
		print("== 真实标签 × 识别 交叉表（行=真实，列=识别）:")
		print(cross.to_string())

	if out_path:
		p = Path(out_path)
		p.parent.mkdir(parents=True, exist_ok=True)
		out.to_csv(p, index=False)
		print(f"== 已写入 {p}")


def main() -> None:
	ap = argparse.ArgumentParser(description="高效 DPI 规则识别引擎 CLI")
	ap.add_argument("--rules", required=True, help="规则文件 (rules/*.yaml)")
	ap.add_argument("--input", required=True, help="输入特征 CSV（每行一个流）")
	ap.add_argument("--format", default="auto", choices=["auto", "csv"],
					help="输入格式（auto 按扩展名识别；当前支持特征 CSV）")
	ap.add_argument("--out", default=None, help="识别结果 CSV 输出路径")
	ap.add_argument("--true-label-col", default=None, help="真实标签列名（打印交叉表）")
	args = ap.parse_args()

	if args.format == "auto":
		fmt = "csv" if args.input.lower().endswith(".csv") else args.format
	else:
		fmt = args.format
	if fmt != "csv":
		print(f"暂不支持 {fmt} 输入，当前仅支持特征 CSV", file=sys.stderr)
		sys.exit(1)

	run(args.rules, args.input, args.out, args.true_label_col)


if __name__ == "__main__":
	main()
