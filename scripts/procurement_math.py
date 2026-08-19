#!/usr/bin/env python3
"""Deterministic weighted-score and TCO calculations for procurement artifacts.

Usage:
    python scripts/procurement_math.py score --input assets/supplier-evaluation.csv --pretty
    python scripts/procurement_math.py tco --input assets/cost-scenarios.csv --pretty
    python scripts/procurement_math.py tco-advanced --input assets/examples/tco-advanced-example.csv --pretty
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterable, Iterator, TextIO


PASS_VALUES = {"pass", "passed", "yes", "true", "1", "通过", "满足", "是"}
FAIL_VALUES = {"fail", "failed", "no", "false", "0", "不通过", "不满足", "否", "暂停"}
VERIFIED_VALUES = {"verified", "confirmed", "pass", "已验证", "已确认", "通过", "材料事实"}


def normalized(value: object) -> str:
    return str(value or "").strip().lower()


def parse_number(value: str, field: str, row_number: int) -> float:
    text = str(value or "").strip().replace(",", "")
    if not text:
        raise ValueError(f"row {row_number}: {field} is required")
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(f"row {row_number}: invalid {field}={value!r}") from exc


def parse_rate(value: str, field: str, row_number: int, *, weight: bool = False) -> float:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return 0.0
    if text.endswith("%"):
        return parse_number(text[:-1], field, row_number) / 100.0
    number = parse_number(text, field, row_number)
    if weight and number > 1:
        return number / 100.0
    return number


def parse_optional_number(value: str, field: str, row_number: int, default: float) -> float:
    text = str(value or "").strip()
    if not text:
        return default
    return parse_number(text, field, row_number)


def parse_bool(value: str) -> bool:
    return normalized(value) in {"true", "yes", "1", "是", "y"}


@contextmanager
def input_stream(path: str) -> Iterator[TextIO]:
    if path == "-":
        yield sys.stdin
        return
    handle = Path(path).open("r", encoding="utf-8-sig", newline="")
    try:
        yield handle
    finally:
        handle.close()


def read_rows(path: str) -> list[dict[str, str]]:
    with input_stream(path) as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("input CSV has no header")
        rows = list(reader)
    if not rows:
        raise ValueError("input CSV has no data rows")
    return rows


def require_columns(rows: list[dict[str, str]], required: Iterable[str]) -> None:
    available = set(rows[0].keys())
    missing = [name for name in required if name not in available]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")


def calculate_scores(rows: list[dict[str, str]]) -> dict[str, object]:
    require_columns(
        rows,
        ["vendor_id", "criterion_id", "mandatory_gate", "gate_result", "weight", "score", "evidence_status"],
    )

    criterion_weights: Dict[str, float] = {}
    seen: set[tuple[str, str]] = set()
    stats: dict[str, dict[str, object]] = defaultdict(
        lambda: {
            "weighted_points": 0.0,
            "scored_weight": 0.0,
            "verified_weight": 0.0,
            "gate_failures": [],
            "gate_unknowns": [],
            "missing_scores": [],
        }
    )

    for row_number, row in enumerate(rows, start=2):
        vendor = str(row.get("vendor_id") or "").strip()
        criterion = str(row.get("criterion_id") or "").strip()
        if not vendor or not criterion:
            raise ValueError(f"row {row_number}: vendor_id and criterion_id are required")
        pair = (vendor, criterion)
        if pair in seen:
            raise ValueError(f"row {row_number}: duplicate vendor/criterion pair {pair}")
        seen.add(pair)

        weight = parse_rate(row.get("weight", ""), "weight", row_number, weight=True)
        if weight < 0:
            raise ValueError(f"row {row_number}: weight cannot be negative")
        previous = criterion_weights.get(criterion)
        if previous is not None and abs(previous - weight) > 1e-9:
            raise ValueError(f"row {row_number}: inconsistent weight for criterion {criterion}")
        criterion_weights[criterion] = weight

        vendor_stats = stats[vendor]
        if parse_bool(row.get("mandatory_gate", "")):
            gate = normalized(row.get("gate_result"))
            if gate in FAIL_VALUES:
                vendor_stats["gate_failures"].append(criterion)
            elif gate not in PASS_VALUES:
                vendor_stats["gate_unknowns"].append(criterion)

        score_text = str(row.get("score") or "").strip()
        if not score_text:
            vendor_stats["missing_scores"].append(criterion)
            continue
        score = parse_number(score_text, "score", row_number)
        if not 0 <= score <= 5:
            raise ValueError(f"row {row_number}: score must be between 0 and 5")

        vendor_stats["weighted_points"] += score * weight
        vendor_stats["scored_weight"] += weight
        if normalized(row.get("evidence_status")) in VERIFIED_VALUES:
            vendor_stats["verified_weight"] += weight

    total_weight = sum(criterion_weights.values())
    if total_weight <= 0:
        raise ValueError("total criterion weight must be greater than zero")

    output = []
    for vendor, values in stats.items():
        scored_weight = float(values["scored_weight"])
        normalized_score = float(values["weighted_points"]) / scored_weight if scored_weight else None
        if values["gate_failures"]:
            gate_status = "fail"
        elif values["gate_unknowns"]:
            gate_status = "unknown"
        else:
            gate_status = "pass"
        output.append(
            {
                "vendor_id": vendor,
                "gate_status": gate_status,
                "gate_failures": values["gate_failures"],
                "gate_unknowns": values["gate_unknowns"],
                "weighted_score_5": round(normalized_score, 6) if normalized_score is not None else None,
                "weighted_score_100": round(normalized_score * 20, 4) if normalized_score is not None else None,
                "score_coverage": round(scored_weight / total_weight, 6),
                "verified_evidence_coverage": round(float(values["verified_weight"]) / total_weight, 6),
                "missing_scores": values["missing_scores"],
            }
        )

    gate_rank = {"pass": 0, "unknown": 1, "fail": 2}
    output.sort(
        key=lambda item: (
            gate_rank[item["gate_status"]],
            -(item["weighted_score_5"] if item["weighted_score_5"] is not None else -1),
            item["vendor_id"],
        )
    )
    return {
        "calculation": "weighted vendor score",
        "scale": "0-5",
        "total_unique_criterion_weight": round(total_weight, 6),
        "vendors": output,
        "warning": "A numeric result is not a recommendation. Review gates, evidence coverage, assumptions, and sensitivity.",
    }


def calculate_tco(rows: list[dict[str, str]]) -> dict[str, object]:
    require_columns(
        rows,
        [
            "vendor_id",
            "scenario",
            "item_id",
            "item",
            "quantity",
            "unit_price",
            "periods",
            "escalation_rate",
            "currency",
            "evidence_status",
        ],
    )

    groups: dict[tuple[str, str], dict[str, object]] = defaultdict(
        lambda: {"currency": None, "total": 0.0, "items": [], "unverified_items": []}
    )
    seen: set[tuple[str, str, str]] = set()

    for row_number, row in enumerate(rows, start=2):
        vendor = str(row.get("vendor_id") or "").strip()
        scenario = str(row.get("scenario") or "").strip()
        item_id = str(row.get("item_id") or "").strip()
        item = str(row.get("item") or "").strip()
        currency = str(row.get("currency") or "").strip().upper()
        if not all([vendor, scenario, item_id, item, currency]):
            raise ValueError(f"row {row_number}: vendor_id, scenario, item_id, item, and currency are required")
        key = (vendor, scenario, item_id)
        if key in seen:
            raise ValueError(f"row {row_number}: duplicate vendor/scenario/item_id {key}")
        seen.add(key)

        quantity = parse_number(row.get("quantity", ""), "quantity", row_number)
        unit_price = parse_number(row.get("unit_price", ""), "unit_price", row_number)
        periods_value = parse_number(row.get("periods", ""), "periods", row_number)
        periods = int(periods_value)
        if periods_value != periods or periods < 1:
            raise ValueError(f"row {row_number}: periods must be a positive integer")
        escalation = parse_rate(row.get("escalation_rate", ""), "escalation_rate", row_number)
        if escalation <= -1:
            raise ValueError(f"row {row_number}: escalation_rate must be greater than -100%")

        annual_base = quantity * unit_price
        item_total = sum(annual_base * ((1 + escalation) ** period) for period in range(periods))
        group = groups[(vendor, scenario)]
        if group["currency"] is None:
            group["currency"] = currency
        elif group["currency"] != currency:
            raise ValueError(
                f"row {row_number}: mixed currencies in {vendor}/{scenario}; convert with a documented FX rate first"
            )
        group["total"] += item_total
        group["items"].append(
            {
                "item_id": item_id,
                "item": item,
                "quantity": quantity,
                "unit_price": unit_price,
                "periods": periods,
                "escalation_rate": escalation,
                "total": round(item_total, 6),
                "evidence_status": row.get("evidence_status", ""),
            }
        )
        if normalized(row.get("evidence_status")) not in VERIFIED_VALUES:
            group["unverified_items"].append(item_id)

    output = []
    for (vendor, scenario), values in sorted(groups.items()):
        output.append(
            {
                "vendor_id": vendor,
                "scenario": scenario,
                "currency": values["currency"],
                "tco": round(float(values["total"]), 6),
                "unverified_items": values["unverified_items"],
                "items": values["items"],
            }
        )
    return {
        "calculation": "scenario TCO",
        "groups": output,
        "warning": "The script does not convert currency, infer tax, or validate commercial scope. Review inputs and assumptions.",
    }


def calculate_tco_advanced(rows: list[dict[str, str]]) -> dict[str, object]:
    require_columns(
        rows,
        [
            "vendor_id",
            "scenario",
            "item_id",
            "item",
            "quantity",
            "unit_price",
            "periods",
            "escalation_rate",
            "currency",
            "evidence_status",
            "discount_rate",
            "exit_cost",
            "commitment_amount",
            "expected_utilization",
            "migration_cost",
        ],
    )

    groups: dict[tuple[str, str], dict[str, object]] = defaultdict(
        lambda: {"currency": None, "npv_total": 0.0, "nominal_total": 0.0, "items": [], "unverified_items": []}
    )
    seen: set[tuple[str, str, str]] = set()

    for row_number, row in enumerate(rows, start=2):
        vendor = str(row.get("vendor_id") or "").strip()
        scenario = str(row.get("scenario") or "").strip()
        item_id = str(row.get("item_id") or "").strip()
        item = str(row.get("item") or "").strip()
        currency = str(row.get("currency") or "").strip().upper()
        if not all([vendor, scenario, item_id, item, currency]):
            raise ValueError(f"row {row_number}: vendor_id, scenario, item_id, item, and currency are required")
        key = (vendor, scenario, item_id)
        if key in seen:
            raise ValueError(f"row {row_number}: duplicate vendor/scenario/item_id {key}")
        seen.add(key)

        quantity = parse_number(row.get("quantity", ""), "quantity", row_number)
        unit_price = parse_number(row.get("unit_price", ""), "unit_price", row_number)
        periods_value = parse_number(row.get("periods", ""), "periods", row_number)
        periods = int(periods_value)
        if periods_value != periods or periods < 1:
            raise ValueError(f"row {row_number}: periods must be a positive integer")
        escalation = parse_rate(row.get("escalation_rate", ""), "escalation_rate", row_number)
        if escalation <= -1:
            raise ValueError(f"row {row_number}: escalation_rate must be greater than -100%")

        discount_rate = parse_rate(row.get("discount_rate", ""), "discount_rate", row_number)
        if not 0 <= discount_rate < 1:
            raise ValueError(f"row {row_number}: discount_rate must be in [0, 1)")
        exit_cost = parse_optional_number(row.get("exit_cost", ""), "exit_cost", row_number, 0.0)
        commitment_amount = parse_optional_number(row.get("commitment_amount", ""), "commitment_amount", row_number, 0.0)
        migration_cost = parse_optional_number(row.get("migration_cost", ""), "migration_cost", row_number, 0.0)
        if min(exit_cost, commitment_amount, migration_cost) < 0:
            raise ValueError(f"row {row_number}: exit_cost, commitment_amount, and migration_cost cannot be negative")
        utilization_text = str(row.get("expected_utilization") or "").strip()
        expected_utilization = (
            parse_rate(utilization_text, "expected_utilization", row_number, weight=True) if utilization_text else 1.0
        )
        if not 0 < expected_utilization <= 1:
            raise ValueError(f"row {row_number}: expected_utilization must be in (0, 1]")

        annual_base = quantity * unit_price
        commitment_waste = commitment_amount * (1 - expected_utilization)
        item_npv = 0.0
        item_nominal = 0.0
        for period in range(1, periods + 1):
            period_cost = annual_base * ((1 + escalation) ** (period - 1)) + commitment_waste
            if period == 1:
                period_cost += migration_cost
            if period == periods:
                period_cost += exit_cost
            item_nominal += period_cost
            item_npv += period_cost / ((1 + discount_rate) ** period)

        group = groups[(vendor, scenario)]
        if group["currency"] is None:
            group["currency"] = currency
        elif group["currency"] != currency:
            raise ValueError(
                f"row {row_number}: mixed currencies in {vendor}/{scenario}; convert with a documented FX rate first"
            )
        group["npv_total"] += item_npv
        group["nominal_total"] += item_nominal
        group["items"].append(
            {
                "item_id": item_id,
                "item": item,
                "quantity": quantity,
                "unit_price": unit_price,
                "periods": periods,
                "escalation_rate": escalation,
                "discount_rate": discount_rate,
                "exit_cost": exit_cost,
                "commitment_amount": commitment_amount,
                "expected_utilization": expected_utilization,
                "migration_cost": migration_cost,
                "npv": round(item_npv, 6),
                "nominal_total": round(item_nominal, 6),
                "evidence_status": row.get("evidence_status", ""),
            }
        )
        if normalized(row.get("evidence_status")) not in VERIFIED_VALUES:
            group["unverified_items"].append(item_id)

    output = []
    for (vendor, scenario), values in sorted(groups.items()):
        output.append(
            {
                "vendor_id": vendor,
                "scenario": scenario,
                "currency": values["currency"],
                "npv_total": round(float(values["npv_total"]), 6),
                "nominal_total": round(float(values["nominal_total"]), 6),
                "unverified_items": values["unverified_items"],
                "items": values["items"],
            }
        )
    return {
        "calculation": "scenario TCO with NPV, commitment waste, migration and exit costs",
        "groups": output,
        "warning": "NPV is an arithmetic result and does not replace commercial judgment. Escalation does not apply to the first period (base cost uses (1+escalation)^(t-1)); with discount_rate=0 the NPV equals the undiscounted total. The script does not convert currency, infer tax, or validate commercial scope.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("score", "calculate weighted vendor scores from supplier-evaluation.csv"),
        ("tco", "calculate scenario TCO from cost-scenarios.csv"),
        ("tco-advanced", "calculate scenario NPV TCO with commitment waste, migration and exit costs"),
    ):
        child = subparsers.add_parser(command, help=help_text)
        child.add_argument("--input", required=True, help="input CSV path, or - for stdin")
        child.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        rows = read_rows(args.input)
        if args.command == "score":
            result = calculate_scores(rows)
        elif args.command == "tco-advanced":
            result = calculate_tco_advanced(rows)
        else:
            result = calculate_tco(rows)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
