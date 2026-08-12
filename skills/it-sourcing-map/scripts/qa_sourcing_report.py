#!/usr/bin/env python3
"""Run structural, neutrality, and information-completeness checks on a report."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from render_sourcing_report import (
    FORBIDDEN_DECISION_PATTERNS,
    REGION_ORDER,
    ValidationError,
    grouped_vendors,
    validate_and_normalize,
)


class ReportParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.nav_targets: list[str] = []
        self.class_counts: dict[str, int] = {}
        self.vendor_group_open: list[bool] = []
        self.longlist_open: bool | None = None
        self.vendor_card_regions: list[tuple[int, str, str]] = []
        self.longlist_regions: list[tuple[int, str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        identifier = values.get("id")
        if identifier:
            self.ids.append(identifier)
        classes = set(values.get("class", "").split())
        for class_name in classes:
            self.class_counts[class_name] = self.class_counts.get(class_name, 0) + 1
        if tag == "a" and "nav-link" in classes:
            href = values.get("href", "")
            if href.startswith("#"):
                self.nav_targets.append(href[1:])
        if tag == "details" and "vendor-section" in classes:
            self.vendor_group_open.append("open" in values)
        if tag == "details" and "longlist-disclosure" in classes:
            self.longlist_open = "open" in values
        if tag == "article" and "vendor-card" in classes:
            self.vendor_card_regions.append(
                (
                    int(values.get("data-market-group", "0")),
                    values.get("data-enterprise-region", ""),
                    values.get("data-vendor-name", ""),
                )
            )
        if tag == "tr" and "longlist-row" in classes:
            self.longlist_regions.append(
                (
                    int(values.get("data-market-group", "0")),
                    values.get("data-enterprise-region", ""),
                    values.get("data-vendor-name", ""),
                )
            )


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def ordered_positions(raw_html: str, identifiers: list[str]) -> list[int]:
    return [raw_html.find(f'id="{identifier}"') for identifier in identifiers]


def assert_text_preserved(raw_html: str, data: dict[str, Any], failures: list[str]) -> None:
    for vendor in data["vendors"]:
        values = [
            vendor["vendor"],
            vendor["solution"],
            vendor["product_form"],
            vendor["public_coverage"],
            vendor["deployment_integration"],
            vendor["commercial_model"],
            vendor["business_entry"],
            vendor["enterprise_region"],
            vendor["region_basis"],
            *vendor["capabilities"],
            *vendor["information_gaps"],
            *vendor["source_ids"],
            *vendor["region_source_ids"],
        ]
        for value in values:
            require(
                html.escape(str(value), quote=True) in raw_html,
                f"厂商 {vendor['vendor']} 的信息未完整进入 HTML：{value}",
                failures,
            )


def run_checks(html_path: Path, data_path: Path | None) -> tuple[list[str], dict[str, Any]]:
    raw_html = html_path.read_text(encoding="utf-8")
    parser = ReportParser()
    parser.feed(raw_html)
    failures: list[str] = []

    require("\ufffd" not in raw_html, "HTML 含 Unicode 替换字符，疑似编码损坏", failures)
    require(
        not re.search(r"\$[A-Za-z_][A-Za-z0-9_]*", raw_html),
        "HTML 含未替换模板变量",
        failures,
    )
    for pattern in FORBIDDEN_DECISION_PATTERNS:
        match = pattern.search(raw_html)
        require(not match, f"HTML 含采购决策表述：{match.group(0) if match else ''}", failures)

    duplicate_ids = sorted({identifier for identifier in parser.ids if parser.ids.count(identifier) > 1})
    require(not duplicate_ids, "HTML id 重复：" + "、".join(duplicate_ids), failures)
    missing_targets = [target for target in parser.nav_targets if target not in parser.ids]
    require(not missing_targets, "导航目标不存在：" + "、".join(missing_targets), failures)

    metrics: dict[str, Any] = {
        "market_layers": parser.class_counts.get("market-layer", 0),
        "vendor_cards": parser.class_counts.get("vendor-card", 0),
        "longlist_rows": parser.class_counts.get("table-tier", 0),
        "route_blocks": parser.class_counts.get("route-block", 0),
        "vendor_groups_collapsible": len(parser.vendor_group_open),
        "html_bytes": html_path.stat().st_size,
    }

    if data_path is None:
        return failures, metrics

    normalized = validate_and_normalize(json.loads(data_path.read_text(encoding="utf-8")))
    grouped, _ = grouped_vendors(normalized)
    supply_groups = [
        item for item in normalized["market_structure"] if item["kind"] == "供给类型"
    ]
    routes = [item for item in normalized["market_structure"] if item["kind"] == "技术路线"]
    vendor_count = len(normalized["vendors"])
    group_count = len(supply_groups)
    large_mode = vendor_count >= 19 or group_count >= 6
    collapsible = vendor_count > 6

    require(metrics["market_layers"] == group_count, "市场层数量与数据不一致", failures)
    require(metrics["vendor_cards"] == vendor_count, "厂商卡数量与数据不一致", failures)
    require(metrics["longlist_rows"] == vendor_count, "Long List 行数与数据不一致", failures)
    require(metrics["route_blocks"] == (1 if routes else 0), "技术路线空态处理不正确", failures)
    require(
        ("trends" in parser.ids) == bool(normalized["trends"]),
        "趋势为空时应省略章节和导航，非空时必须展示",
        failures,
    )
    require(
        ("constraints" in parser.ids) == bool(normalized["scope"]["constraints"]),
        "约束为空时应省略章节和导航，非空时必须展示",
        failures,
    )
    require(len(parser.vendor_group_open) == (group_count if collapsible else 0), "市场层折叠策略不正确", failures)
    if collapsible:
        expected_group_open = not large_mode
        require(
            all(state == expected_group_open for state in parser.vendor_group_open),
            "市场层默认展开状态与样本规模不匹配",
            failures,
        )
    require(parser.longlist_open == large_mode, "Long List 默认展开状态与样本规模不匹配", failures)

    mainland_count = sum(
        item["enterprise_region"] == "mainland_china" for item in normalized["vendors"]
    )
    overseas_count = sum(
        item["enterprise_region"] == "overseas" for item in normalized["vendors"]
    )
    if (
        normalized["schema_version"] == "3.0"
        and not normalized["scope"]["region_coverage_exception"]
    ):
        require(mainland_count * 2 > vendor_count, "大陆企业未占候选池严格多数", failures)
        require(mainland_count > overseas_count, "大陆企业数量未多于海外企业", failures)

    def check_region_order(
        rows: list[tuple[int, str, str]], label: str
    ) -> None:
        for group_index in range(1, group_count + 1):
            regions = [region for index, region, _ in rows if index == group_index]
            ranks = [REGION_ORDER.get(region, 99) for region in regions]
            require(ranks == sorted(ranks), f"{label} 的 M{group_index} 未按大陆、海外、待核验排序", failures)

    check_region_order(parser.vendor_card_regions, "厂商卡")
    longlist_rank_pairs = [
        (REGION_ORDER.get(region, 99), group_index)
        for group_index, region, _ in parser.longlist_regions
    ]
    require(
        longlist_rank_pairs == sorted(longlist_rank_pairs),
        "Long List 未按全表大陆、海外、待核验优先，再按市场层排序",
        failures,
    )
    require(
        sorted(item[2] for item in parser.vendor_card_regions)
        == sorted(item[2] for item in parser.longlist_regions),
        "厂商卡与 Long List 的供应商集合不一致",
        failures,
    )

    map_end = raw_html.find('id="market-group-1"')
    map_fragment = raw_html[:map_end] if map_end >= 0 else raw_html
    for group in grouped:
        for region, limit in (("mainland_china", 5), ("overseas", 3), ("unverified", 2)):
            names = [
                item["vendor"]
                for item in group["vendors"]
                if item["enterprise_region"] == region
            ][:limit]
            for name in names:
                require(html.escape(name, quote=True) in map_fragment, f"市场图未直列玩家：{name}", failures)

    expected_order = ["market-map", *[f"market-group-{index}" for index in range(1, group_count + 1)], "price"]
    if normalized["scope"]["constraints"]:
        expected_order.append("constraints")
    if normalized["trends"]:
        expected_order.append("trends")
    expected_order.extend(["risks", "longlist"])
    positions = ordered_positions(raw_html, expected_order)
    require(all(position >= 0 for position in positions), "核心章节缺失", failures)
    require(positions == sorted(positions), "核心章节顺序不符合信息逻辑", failures)

    colors = re.findall(r'class="market-layer"[^>]*--layer-color:([^;]+);', raw_html)
    require(len(set(colors)) == group_count, "市场层颜色未保持分类唯一", failures)
    density_rows = [
        (int(count), float(width))
        for count, width in re.findall(
            r'class="market-layer" data-vendor-count="(\d+)"[^>]*--layer-width:([\d.]+)%',
            raw_html,
        )
    ]
    require(len(density_rows) == group_count, "市场图未输出可解释的厂商数量宽度", failures)
    for left_count, left_width in density_rows:
        for right_count, right_width in density_rows:
            if left_count > right_count:
                require(left_width > right_width, "市场图宽度未随已识别厂商数量增加", failures)
    assert_text_preserved(raw_html, normalized, failures)
    return failures, metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="验收中立市场调研 HTML。")
    parser.add_argument("html", type=Path, help="待验收 HTML")
    parser.add_argument("--data", type=Path, help="可选：生成该 HTML 的 JSON 数据")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        failures, metrics = run_checks(args.html, args.data)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"验收无法执行：{exc}", file=sys.stderr)
        return 2
    if failures:
        print("验收失败：", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("验收通过：" + json.dumps(metrics, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
