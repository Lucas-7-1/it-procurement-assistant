#!/usr/bin/env python3
"""Validate research-backed supplier-map JSON and render one offline HTML file."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path
from typing import Any


ALLOWED_CLAIM_TYPES = {"fact", "vendor_claim", "inference", "reference"}
ALLOWED_STATUSES = {"shortlist", "watch", "exclude"}
STATUS_LABELS = {"shortlist": "入围", "watch": "观察", "exclude": "排除"}
HEAT_LABELS = {"high": "高", "medium": "中", "low": "低", "pending": "待验证"}
FIVE_LOOKS = (
    ("industry", "看行业"),
    ("market", "看市场"),
    ("customer", "看客户"),
    ("competition", "看竞争"),
    ("self", "看自己"),
)
THREE_DECISIONS = (
    ("control_point", "定控制点"),
    ("goal", "定目标"),
    ("strategy", "定策略"),
)
REQUIRED_INDUSTRY_HIGHLIGHTS = ("国家政策", "技术趋势")
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
FORBIDDEN_PENDING_FIELDS = {
    "x",
    "y",
    "coordinate_rationale",
    "coordinate_source_ids",
    "source_id",
    "source_ids",
}


class ValidationError(ValueError):
    """Raised when the evidence map does not meet the required schema."""


def fail(path: str, message: str) -> None:
    raise ValidationError(f"{path}: {message}")


def as_object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(path, "必须是对象")
    return value


def as_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        fail(path, "必须是数组")
    return value


def nonempty_text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(path, "必须是非空文本")
    return value.strip()


def validate_date(value: Any, path: str, allow_undisclosed: bool = False) -> str:
    text = nonempty_text(value, path)
    if allow_undisclosed and text == "日期未公开":
        return text
    if not DATE_PATTERN.fullmatch(text):
        fail(path, "只允许 YYYY-MM-DD" + (" 或“日期未公开”" if allow_undisclosed else ""))
    try:
        dt.date.fromisoformat(text)
    except ValueError:
        fail(path, "不是有效日期")
    return text


def source_ids(value: Any, path: str, known_ids: set[str], required: bool = False) -> list[str]:
    values = as_list(value, path)
    if required and not values:
        fail(path, "至少需要一个有效 source_id")
    normalized: list[str] = []
    for index, item in enumerate(values):
        identifier = nonempty_text(item, f"{path}[{index}]")
        if identifier not in known_ids:
            fail(f"{path}[{index}]", f"引用不存在的 source_id：{identifier}")
        if identifier not in normalized:
            normalized.append(identifier)
    return normalized


def validate_sources(value: Any) -> tuple[list[dict[str, Any]], set[str]]:
    sources = as_list(value, "sources")
    ids: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(sources):
        item = as_object(raw, f"sources[{index}]")
        identifier = nonempty_text(item.get("id"), f"sources[{index}].id")
        if identifier in ids:
            fail(f"sources[{index}].id", "source_id 不能重复")
        ids.add(identifier)
        claim_type = nonempty_text(item.get("claim_type"), f"sources[{index}].claim_type")
        if claim_type not in ALLOWED_CLAIM_TYPES:
            fail(
                f"sources[{index}].claim_type",
                "只允许 fact/vendor_claim/inference/reference",
            )
        url = item.get("url")
        locator = item.get("source_locator")
        if not (isinstance(url, str) and url.strip()) and not (
            isinstance(locator, str) and locator.strip()
        ):
            fail(f"sources[{index}]", "必须提供非空 url 或 source_locator")
        normalized.append(
            {
                "id": identifier,
                "subject": nonempty_text(item.get("subject"), f"sources[{index}].subject"),
                "title": nonempty_text(item.get("title"), f"sources[{index}].title"),
                "date": validate_date(item.get("date"), f"sources[{index}].date", True),
                "claim_type": claim_type,
                "url": url.strip() if isinstance(url, str) else "",
                "source_locator": locator.strip() if isinstance(locator, str) else "",
            }
        )
    return normalized, ids


def validate_generic_references(value: Any, path: str, known_ids: set[str]) -> None:
    """Reject dangling source IDs everywhere outside the source catalog."""
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in {"source_ids", "coordinate_source_ids"}:
                source_ids(child, child_path, known_ids)
            elif key == "source_id":
                identifier = nonempty_text(child, child_path)
                if identifier not in known_ids:
                    fail(child_path, f"引用不存在的 source_id：{identifier}")
            else:
                validate_generic_references(child, child_path, known_ids)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_generic_references(child, f"{path}[{index}]", known_ids)


def validate_vendor(raw: Any, index: int, known_ids: set[str]) -> dict[str, Any]:
    path = f"vendors[{index}]"
    item = as_object(raw, path)
    status = nonempty_text(item.get("status"), f"{path}.status")
    if status not in ALLOWED_STATUSES:
        fail(f"{path}.status", "只允许 shortlist/watch/exclude")

    try:
        x = float(item.get("x"))
        y = float(item.get("y"))
    except (TypeError, ValueError):
        fail(path, "x 和 y 必须是 0–100 的数字")
    if not 0 <= x <= 100 or not 0 <= y <= 100:
        fail(path, "x 和 y 必须在 0–100 之间")

    citations = source_ids(item.get("source_ids"), f"{path}.source_ids", known_ids, True)
    coordinate_citations = source_ids(
        item.get("coordinate_source_ids"),
        f"{path}.coordinate_source_ids",
        known_ids,
        True,
    )
    return {
        "name": nonempty_text(item.get("name"), f"{path}.name"),
        "segment": nonempty_text(item.get("segment"), f"{path}.segment"),
        "status": status,
        "x": x,
        "y": y,
        "summary": str(item.get("summary", "待补充")).strip() or "待补充",
        "technology_path": str(item.get("technology_path", "待确认")).strip() or "待确认",
        "fit_note": str(item.get("fit_note", "待确认")).strip() or "待确认",
        "compliance_note": str(item.get("compliance_note", "待确认")).strip() or "待确认",
        "source_ids": citations,
        "coordinate_rationale": nonempty_text(
            item.get("coordinate_rationale"), f"{path}.coordinate_rationale"
        ),
        "coordinate_source_ids": coordinate_citations,
    }


def validate_pending_vendor(raw: Any, index: int) -> dict[str, str]:
    path = f"pending_verification_vendors[{index}]"
    item = as_object(raw, path)
    present = FORBIDDEN_PENDING_FIELDS.intersection(item)
    if present:
        fail(path, "待验证候选不得带来源或坐标字段：" + ", ".join(sorted(present)))
    return {
        "name": nonempty_text(item.get("name"), f"{path}.name"),
        "reason": nonempty_text(item.get("reason"), f"{path}.reason"),
        "next_validation": nonempty_text(item.get("next_validation"), f"{path}.next_validation"),
    }


def normalize_text_list(value: Any, path: str) -> list[str]:
    if value is None:
        return []
    return [str(item).strip() for item in as_list(value, path) if str(item).strip()]


def normalize_evidence_items(value: Any, path: str, known_ids: set[str]) -> list[dict[str, Any]]:
    if value is None:
        return []
    items = as_list(value, path)
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(items):
        item = as_object(raw, f"{path}[{index}]")
        citations = source_ids(item.get("source_ids", []), f"{path}[{index}].source_ids", known_ids)
        normalized.append(
            {
                "name": nonempty_text(item.get("name"), f"{path}[{index}].name"),
                "summary": nonempty_text(item.get("summary"), f"{path}[{index}].summary"),
                "source_ids": citations,
                "heat": str(item.get("heat", "pending")).strip() or "pending",
            }
        )
    return normalized


def normalize_five_looks(value: Any, known_ids: set[str]) -> dict[str, dict[str, Any]]:
    raw = as_object(value if value is not None else {}, "five_looks")
    normalized: dict[str, dict[str, Any]] = {}
    for key, _ in FIVE_LOOKS:
        item = raw.get(key, {})
        item = as_object(item, f"five_looks.{key}")
        normalized[key] = {
            "summary": str(item.get("summary", "待验证")).strip() or "待验证",
            "source_ids": source_ids(item.get("source_ids", []), f"five_looks.{key}.source_ids", known_ids),
            "highlights": normalize_evidence_items(
                item.get("highlights", []), f"five_looks.{key}.highlights", known_ids
            ),
        }
    return normalized


def normalize_three_decisions(value: Any, known_ids: set[str]) -> dict[str, dict[str, Any]]:
    if value is None:
        fail("three_decisions", "必须提供三定（control_point/goal/strategy）")
    raw = as_object(value, "three_decisions")
    normalized: dict[str, dict[str, Any]] = {}
    for key, _ in THREE_DECISIONS:
        entry = as_object(raw.get(key, {}), f"three_decisions.{key}")
        summary = str(entry.get("summary", "")).strip()
        if not summary:
            fail(f"three_decisions.{key}.summary", "必须是非空文本")
        normalized[key] = {
            "summary": summary,
            "source_ids": source_ids(
                entry.get("source_ids", []), f"three_decisions.{key}.source_ids", known_ids
            ),
        }
    return normalized


def normalize_boundary(value: Any) -> dict[str, Any]:
    item = as_object(value if value is not None else {}, "demand_boundary")
    return {
        "business_goal": str(item.get("business_goal", "待确认")).strip() or "待确认",
        "in_scope": normalize_text_list(item.get("in_scope", []), "demand_boundary.in_scope"),
        "out_of_scope": normalize_text_list(item.get("out_of_scope", []), "demand_boundary.out_of_scope"),
        "timeline": str(item.get("timeline", "待确认")).strip() or "待确认",
        "budget": str(item.get("budget", "待确认")).strip() or "待确认",
        "system_data_compliance_constraints": normalize_text_list(
            item.get("system_data_compliance_constraints", []),
            "demand_boundary.system_data_compliance_constraints",
        ),
        "success_criteria": normalize_text_list(
            item.get("success_criteria", []), "demand_boundary.success_criteria"),
    }


def validate_and_normalize(raw: Any) -> dict[str, Any]:
    data = as_object(raw, "root")
    demand_oneliner = nonempty_text(data.get("demand_oneliner"), "demand_oneliner")
    sources, known_ids = validate_sources(data.get("sources", []))
    vendors = [validate_vendor(item, index, known_ids) for index, item in enumerate(as_list(data.get("vendors", []), "vendors"))]
    if vendors and not sources:
        fail("sources", "vendors 非空时，sources 不得为空")
    pending = [
        validate_pending_vendor(item, index)
        for index, item in enumerate(as_list(data.get("pending_verification_vendors", []), "pending_verification_vendors"))
    ]
    validate_generic_references(
        {key: value for key, value in data.items() if key != "sources"},
        "root",
        known_ids,
    )

    five_looks = normalize_five_looks(data.get("five_looks"), known_ids)
    industry_highlight_names = {item["name"] for item in five_looks["industry"]["highlights"]}
    for required in REQUIRED_INDUSTRY_HIGHLIGHTS:
        if required not in industry_highlight_names:
            fail("five_looks.industry.highlights", f"看行业必须包含子项：{required}")
    three_decisions = normalize_three_decisions(data.get("three_decisions"), known_ids)

    axes = as_object(data.get("map_axes", {}), "map_axes")
    return {
        "title": str(data.get("title", "供应商地图")).strip() or "供应商地图",
        "category": str(data.get("category", "待确认品类")).strip() or "待确认品类",
        "research_date": validate_date(data.get("research_date"), "research_date"),
        "demand_oneliner": demand_oneliner,
        "assumptions": normalize_text_list(data.get("assumptions", []), "assumptions"),
        "demand_boundary": normalize_boundary(data.get("demand_boundary")),
        "map_axes": {
            "x_label": str(axes.get("x_label", "横轴：需求适配度（分析定位）")).strip()
            or "横轴：需求适配度（分析定位）",
            "y_label": str(axes.get("y_label", "纵轴：交付 / 部署可控性（分析定位）")).strip()
            or "纵轴：交付 / 部署可控性（分析定位）",
        },
        "five_looks": five_looks,
        "three_decisions": three_decisions,
        "technical_paths": normalize_evidence_items(data.get("technical_paths"), "technical_paths", known_ids),
        "peer_paths": normalize_evidence_items(data.get("peer_paths"), "peer_paths", known_ids),
        "compliance_risks": normalize_evidence_items(data.get("compliance_risks"), "compliance_risks", known_ids),
        "vendors": vendors,
        "pending_verification_vendors": pending,
        "sources": sources,
        "pending_items": normalize_text_list(data.get("pending_items", []), "pending_items"),
    }


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def source_badges(ids: list[str]) -> str:
    if not ids:
        return '<span class="muted">待验证</span>'
    return " ".join(f'<span class="source-chip">{esc(identifier)}</span>' for identifier in ids)


def list_markup(items: list[str]) -> str:
    if not items:
        return '<span class="muted">待确认</span>'
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def source_markup(source: dict[str, Any]) -> str:
    label = f"{source['id']}｜{source['subject']}｜{source['title']}｜{source['date']}｜{source['claim_type']}"
    url = source.get("url", "")
    if url and re.match(r"^https?://", url, re.IGNORECASE):
        return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'
    locator = source.get("source_locator", "")
    return f"{esc(label)}" + (f"<br><span class=\"muted\">{esc(locator or url)}</span>" if locator or url else "")


def render_card(title: str, summary: str, ids: list[str], highlights: list[dict[str, Any]] | None = None) -> str:
    highlights_markup = ""
    if highlights:
        rows = "".join(
            "<li>"
            f"<strong>{esc(item['name'])}</strong>：{esc(item['summary'])}"
            f'<div class="evidence">{source_badges(item["source_ids"])}</div>'
            "</li>"
            for item in highlights
        )
        highlights_markup = f'<ul class="highlights">{rows}</ul>'
    return (
        '<article class="card">'
        f"<h3>{esc(title)}</h3><p>{esc(summary)}</p>"
        f"{highlights_markup}"
        f'<div class="evidence">{source_badges(ids)}</div></article>'
    )


def evidence_list_markup(items: list[dict[str, Any]], risk: bool = False) -> str:
    if not items:
        return '<p class="muted">暂无经公开证据确认的内容。</p>'
    rows: list[str] = []
    for item in items:
        heat = f'<span class="heat {esc(item["heat"])}">{esc(HEAT_LABELS.get(item["heat"], item["heat"]))}</span> ' if risk else ""
        rows.append(
            "<li>"
            f"<strong>{heat}{esc(item['name'])}</strong><br>{esc(item['summary'])}<br>"
            f'<span class="evidence">{source_badges(item["source_ids"])}</span>'
            "</li>"
        )
    return '<ul class="evidence-list">' + "".join(rows) + "</ul>"


def render_evidence_section(title: str, items: list[dict[str, Any]], risk: bool = False) -> str:
    return f'<section class="panel"><h2>{esc(title)}</h2>{evidence_list_markup(items, risk)}</section>'


def render_vendor_summary(vendors: list[dict[str, Any]]) -> str:
    groups = [
        ("shortlist", "推荐入围", "建议进入统一询价与POC"),
        ("watch", "观察", "暂不推进，保留跟踪"),
        ("exclude", "排除", "当前不建议"),
    ]
    blocks: list[str] = []
    for status, label, note in groups:
        selected = [vendor for vendor in vendors if vendor["status"] == status]
        if not selected:
            continue
        rows = "".join(
            "<li>"
            f"<strong>{esc(vendor['name'])}</strong>"
            f"<span class=\"muted\">｜{esc(vendor['segment'])}</span><br>"
            f"{esc(vendor['summary'])}"
            f"<br><span class=\"muted\">合规待验证：{esc(vendor['compliance_note'])}</span>"
            "</li>"
            for vendor in selected
        )
        blocks.append(
            f'<article class="card"><h3>{esc(label)}（{len(selected)}家）</h3>'
            f'<p class="muted">{esc(note)}</p><ul class="vendor-lines">{rows}</ul></article>'
        )
    if not blocks:
        blocks.append('<article class="card"><h3>候选</h3><p class="muted">暂无经公开证据验证的候选，见下方待验证候选区。</p></article>')
    return "".join(blocks)


def render_html(data: dict[str, Any]) -> str:
    boundary = data["demand_boundary"]
    look_cards = ""
    for key, label in FIVE_LOOKS:
        look = data["five_looks"][key]
        look_cards += render_card(label, look["summary"], look["source_ids"], look.get("highlights"))
    decision_cards = "".join(
        render_card(label, data["three_decisions"][key]["summary"], data["three_decisions"][key]["source_ids"])
        for key, label in THREE_DECISIONS
    )
    vendor_summary = render_vendor_summary(data["vendors"])
    top_risks = [item for item in data["compliance_risks"] if item.get("heat") == "high"][:3] or data["compliance_risks"][:3]
    risk_lines = "".join(
        f"<li><strong>{esc(item['name'])}</strong>：{esc(item['summary'])}</li>" for item in top_risks
    )
    summary_panel = (
        '<section class="panel summary-panel"><h2>采购结论（三定）</h2>'
        f'<div class="five-grid">{decision_cards}</div>'
        f'<h2 style="margin-top:16px">短名单</h2><div class="five-grid">{vendor_summary}</div>'
        f'<h2 style="margin-top:16px">关键风险</h2><ul class="evidence-list">{risk_lines}</ul>'
        "</section>"
    )
    source_rows = "".join(f"<li>{source_markup(source)}</li>" for source in data["sources"])
    pending_rows = "".join(
        "<li><strong>" + esc(item["name"]) + "</strong>：" + esc(item["reason"]) + "<br>下一步：" + esc(item["next_validation"]) + "</li>"
        for item in data["pending_verification_vendors"]
    )
    pending_items = list_markup(data["pending_items"])
    no_vendor_notice = (
        '<p id="no-vendor-notice" class="empty-notice">暂无经公开证据验证的玩家。下方仅列待验证候选，不绘制坐标。</p>'
        if not data["vendors"]
        else '<p id="no-vendor-notice" class="empty-notice" hidden>当前筛选下暂无经公开证据验证的玩家。</p>'
    )
    json_data = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    json_data = json_data.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(data['title'])}</title>
<style>
:root {{ color-scheme: light; --ink:#172033; --muted:#5d6b82; --line:#dce3ee; --paper:#f6f8fc; --blue:#2457d6; --green:#16886a; --orange:#db741b; --red:#b42318; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--paper); color:var(--ink); font-family:"Microsoft YaHei", "PingFang SC", Arial, sans-serif; line-height:1.55; }}
main {{ max-width:1240px; margin:0 auto; padding:28px 20px 48px; }}
header {{ border-left:5px solid var(--blue); padding:4px 0 5px 16px; margin-bottom:20px; }}
h1 {{ margin:0; font-size:28px; line-height:1.25; }} h2 {{ margin:0 0 12px; font-size:19px; }} h3 {{ margin:0 0 8px; font-size:16px; }} p {{ margin:0 0 8px; }}
.meta, .muted {{ color:var(--muted); }} .meta {{ margin-top:7px; }}
.oneliner {{ margin-top:12px; padding:10px 14px; background:#eef3ff; border-left:4px solid var(--blue); border-radius:0 8px 8px 0; font-size:15px; }}
.highlights {{ margin:8px 0 0; padding-left:18px; font-size:13px; }} .highlights li {{ margin:6px 0; }} .highlights .evidence {{ margin-top:2px; }}
.panel {{ background:#fff; border:1px solid var(--line); border-radius:12px; padding:18px; margin:16px 0; box-shadow:0 2px 7px rgba(29,43,74,.04); }}
.summary-panel {{ border-left:5px solid var(--green); }}
details.panel {{ padding:0; }} details.panel > summary {{ list-style:none; cursor:pointer; font-weight:600; font-size:16px; padding:14px 18px; }} details.panel > summary::-webkit-details-marker {{ display:none; }} details.panel > summary::before {{ content:"▸ "; color:var(--blue); }} details.panel[open] > summary::before {{ content:"▾ "; }} details.panel > summary:hover {{ color:var(--blue); }} details.panel .panel-body {{ padding:0 18px 16px; }}
.boundary {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:12px; }}
.boundary article, .card {{ border:1px solid var(--line); border-radius:10px; padding:13px; background:#fff; }}
.boundary h3 {{ color:var(--muted); font-size:13px; }} ul {{ margin:7px 0 0; padding-left:20px; }}
.five-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:12px; }}
.vendor-lines li {{ padding:7px 0; border-bottom:1px solid #edf0f5; }} .vendor-lines li:last-child {{ border-bottom:0; }}
.source-chip {{ display:inline-block; padding:2px 7px; margin:3px 4px 0 0; border-radius:999px; background:#eef3ff; color:#284a99; font-size:12px; }}
.evidence {{ margin-top:8px; font-size:12px; }}
.controls {{ display:flex; flex-wrap:wrap; align-items:end; gap:12px; margin:0 0 12px; }}
label {{ display:flex; flex-direction:column; gap:4px; font-size:13px; color:var(--muted); }} select, button {{ min-height:34px; border:1px solid #b8c4d8; border-radius:7px; background:#fff; padding:5px 9px; color:var(--ink); }} button {{ cursor:pointer; }}
.map-wrap {{ overflow-x:auto; border:1px solid var(--line); border-radius:10px; background:#fcfdff; padding:8px; }}
svg {{ display:block; width:100%; min-width:720px; height:auto; }} .axis {{ stroke:#7a889e; stroke-width:1.25; }} .grid {{ stroke:#e5eaf2; stroke-width:1; stroke-dasharray:3 5; }} .axis-label {{ fill:#53627a; font-size:13px; }} .tick {{ fill:#7a889e; font-size:11px; }}
.bubble {{ cursor:pointer; fill-opacity:.85; stroke:#fff; stroke-width:2; }} .bubble.shortlist {{ fill:var(--green); }} .bubble.watch {{ fill:var(--orange); }} .bubble.exclude {{ fill:var(--red); }} .bubble:hover {{ fill-opacity:1; stroke:#172033; }}
.legend {{ display:flex; flex-wrap:wrap; gap:12px; margin:10px 0 0; font-size:13px; }} .dot {{ display:inline-block; width:11px; height:11px; border-radius:50%; margin-right:4px; }} .dot.shortlist {{ background:var(--green); }} .dot.watch {{ background:var(--orange); }} .dot.exclude {{ background:var(--red); }}
.map-note, .empty-notice {{ color:var(--muted); font-size:13px; margin-top:10px; }} .detail {{ margin-top:12px; padding:14px; border-radius:9px; background:#f3f6fb; min-height:80px; }} .detail p {{ margin:5px 0; }}
.evidence-list {{ margin:0; padding-left:20px; }} .evidence-list li {{ padding:8px 0; border-bottom:1px solid #edf0f5; }} .evidence-list li:last-child {{ border-bottom:0; }} .heat {{ border-radius:5px; padding:1px 5px; font-size:12px; }} .heat.high {{ background:#ffe5e2; color:#9b1c13; }} .heat.medium {{ background:#fff1d7; color:#925809; }} .heat.low {{ background:#e4f7ef; color:#11634d; }} .heat.pending {{ background:#eef0f4; color:#566177; }}
a {{ color:#1d4ed8; }} footer {{ color:var(--muted); font-size:12px; margin-top:18px; }}
</style>
</head>
<body>
<main>
  <header><h1>{esc(data['title'])}</h1><p class="meta">品类：{esc(data['category'])}　|　研究日期：{esc(data['research_date'])}　|　仅供采购调研与核验使用</p><p class="oneliner">需求原话：{esc(data['demand_oneliner'])}</p></header>
  {summary_panel}
  <section class="panel"><h2>供应商分布图</h2>
    <div class="controls"><label>状态<select id="status-filter"><option value="all">全部</option><option value="shortlist">入围</option><option value="watch">观察</option><option value="exclude">排除</option></select></label><label>细分<select id="segment-filter"><option value="all">全部细分</option></select></label><button id="reset-filter" type="button">重置筛选</button></div>
    <div class="map-wrap"><svg id="supplier-map" viewBox="0 0 960 550" role="img" aria-label="供应商分析定位图"><g id="map-base"></g><g id="map-points"></g></svg></div>
    <div class="legend"><span><i class="dot shortlist"></i>入围</span><span><i class="dot watch"></i>观察</span><span><i class="dot exclude"></i>排除</span><span>气泡大小＝公开证据覆盖度（去重来源数），不是市场份额</span></div>
    {no_vendor_notice}
    <p class="map-note">坐标为分析定位：用于呈现相对判断，不代表市场排名、营收、市场份额或客观能力评分。点击气泡查看坐标依据与来源。</p>
    <div id="vendor-detail" class="detail">选择图上的玩家，查看需求匹配、合规待验证、坐标依据与来源。</div>
  </section>
  <details class="panel"><summary>五看摘要（行业 / 政策 / 趋势 / 市场 / 客户 / 竞争 / 自己）</summary><div class="panel-body"><div class="five-grid">{look_cards}</div></div></details>
  <details class="panel"><summary>需求边界、假设与待确认</summary><div class="panel-body"><div class="boundary">
    <article><h3>业务目标</h3><p>{esc(boundary['business_goal'])}</p></article>
    <article><h3>假设与待确认（用户未说明，由调研方推断）</h3>{list_markup(data['assumptions'])}</article>
    <article><h3>范围内</h3>{list_markup(boundary['in_scope'])}</article>
    <article><h3>范围外</h3>{list_markup(boundary['out_of_scope'])}</article>
    <article><h3>时间 / 预算</h3><p>时间：{esc(boundary['timeline'])}</p><p>预算：{esc(boundary['budget'])}</p></article>
    <article><h3>系统、数据与合规约束</h3>{list_markup(boundary['system_data_compliance_constraints'])}</article>
    <article><h3>成功标准</h3>{list_markup(boundary['success_criteria'])}</article>
  </div></div></details>
  <details class="panel"><summary>技术路径 · 同类需求路径 · 合规风险热区</summary><div class="panel-body">
    <h3>技术路径</h3>{evidence_list_markup(data['technical_paths'])}
    <h3 style="margin-top:16px">同类需求路径</h3>{evidence_list_markup(data['peer_paths'])}
    <h3 style="margin-top:16px">合规风险热区</h3>{evidence_list_markup(data['compliance_risks'], True)}
  </div></details>
  <details class="panel"><summary>待验证候选与待验证项</summary><div class="panel-body"><h3>待验证候选（不绘制坐标）</h3>{('<ul class="evidence-list">' + pending_rows + '</ul>') if pending_rows else '<p class="muted">暂无。</p>'}<h3 style="margin-top:16px">待验证项</h3>{pending_items}</div></details>
  <details class="panel"><summary>来源（{len(data['sources'])}条，可回链核验）</summary><div class="panel-body">{('<ul class="evidence-list">' + source_rows + '</ul>') if source_rows else '<p class="muted">暂无外部来源；本报告为待验证地图。</p>'}</div></details>
  <footer>生成方式：离线单文件 HTML。请在评估、POC 或供应商尽调前复核来源时点、厂商主张与适用边界。</footer>
</main>
<script>
const reportData = {json_data};
const svgNS = 'http://www.w3.org/2000/svg';
const base = document.getElementById('map-base');
const points = document.getElementById('map-points');
const detail = document.getElementById('vendor-detail');
const notice = document.getElementById('no-vendor-notice');
const statusFilter = document.getElementById('status-filter');
const segmentFilter = document.getElementById('segment-filter');
const chart = {{ left: 92, right: 910, top: 42, bottom: 458 }};
const sourceIndex = new Map(reportData.sources.map(source => [source.id, source]));

function node(name, attributes = {{}}) {{
  const element = document.createElementNS(svgNS, name);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, String(value)));
  return element;
}}
function textNode(text, attributes = {{}}) {{
  const element = node('text', attributes); element.textContent = text; return element;
}}
function mapX(value) {{ return chart.left + (value / 100) * (chart.right - chart.left); }}
function mapY(value) {{ return chart.bottom - (value / 100) * (chart.bottom - chart.top); }}
function drawBase() {{
  base.replaceChildren();
  for (let tick = 0; tick <= 100; tick += 20) {{
    const x = mapX(tick), y = mapY(tick);
    base.append(node('line', {{ x1:x, y1:chart.top, x2:x, y2:chart.bottom, class:'grid' }}));
    base.append(node('line', {{ x1:chart.left, y1:y, x2:chart.right, y2:y, class:'grid' }}));
    base.append(textNode(String(tick), {{ x:x, y:chart.bottom + 18, 'text-anchor':'middle', class:'tick' }}));
    base.append(textNode(String(tick), {{ x:chart.left - 12, y:y + 4, 'text-anchor':'end', class:'tick' }}));
  }}
  base.append(node('line', {{ x1:chart.left, y1:chart.bottom, x2:chart.right, y2:chart.bottom, class:'axis' }}));
  base.append(node('line', {{ x1:chart.left, y1:chart.top, x2:chart.left, y2:chart.bottom, class:'axis' }}));
  base.append(textNode(reportData.map_axes.x_label, {{ x:(chart.left + chart.right)/2, y:523, 'text-anchor':'middle', class:'axis-label' }}));
  const yLabel = textNode(reportData.map_axes.y_label, {{ x:22, y:(chart.top + chart.bottom)/2, 'text-anchor':'middle', class:'axis-label', transform:`rotate(-90 22 ${{(chart.top + chart.bottom)/2}})` }});
  base.append(yLabel);
}}
function evidenceText(ids) {{
  return ids.map(id => {{ const source = sourceIndex.get(id); return source ? `${{id}}｜${{source.subject}}｜${{source.title}}｜${{source.date}}` : id; }}).join('\n');
}}
function appendDetailLine(label, value) {{
  const paragraph = document.createElement('p');
  const strong = document.createElement('strong'); strong.textContent = label; paragraph.append(strong, document.createTextNode(value)); detail.append(paragraph);
}}
function showDetail(vendor) {{
  detail.replaceChildren();
  const heading = document.createElement('h3'); heading.textContent = `${{vendor.name}}｜${{vendor.segment}}｜${{({{shortlist:'入围',watch:'观察',exclude:'排除'}})[vendor.status]}}`; detail.append(heading);
  appendDetailLine('定位：', vendor.summary);
  appendDetailLine('技术路径：', vendor.technology_path);
  appendDetailLine('需求匹配：', vendor.fit_note);
  appendDetailLine('合规待验证：', vendor.compliance_note);
  appendDetailLine('坐标依据（分析定位）：', vendor.coordinate_rationale);
  appendDetailLine('坐标来源：', evidenceText(vendor.coordinate_source_ids));
  appendDetailLine('其他公开证据：', evidenceText(vendor.source_ids));
}}
function visibleVendors() {{
  return reportData.vendors.filter(vendor => (statusFilter.value === 'all' || vendor.status === statusFilter.value) && (segmentFilter.value === 'all' || vendor.segment === segmentFilter.value));
}}
function renderPoints() {{
  points.replaceChildren();
  const visible = visibleVendors();
  notice.hidden = visible.length > 0;
  visible.forEach(vendor => {{
    const coverage = new Set(vendor.source_ids).size;
    const bubble = node('circle', {{ cx:mapX(vendor.x), cy:mapY(vendor.y), r:Math.min(27, 9 + coverage * 4), class:`bubble ${{vendor.status}}`, tabindex:0, role:'button', 'aria-label':`${{vendor.name}}，${{vendor.segment}}` }});
    bubble.addEventListener('click', () => showDetail(vendor));
    bubble.addEventListener('keydown', event => {{ if (event.key === 'Enter' || event.key === ' ') {{ event.preventDefault(); showDetail(vendor); }} }});
    points.append(bubble);
    points.append(textNode(vendor.name, {{ x:mapX(vendor.x), y:mapY(vendor.y) + 4, 'text-anchor':'middle', fill:'#fff', 'font-size':'11', 'pointer-events':'none' }}));
  }});
}}
const segments = [...new Set(reportData.vendors.map(vendor => vendor.segment))].sort((a, b) => a.localeCompare(b, 'zh-CN'));
segments.forEach(segment => {{ const option = document.createElement('option'); option.value = segment; option.textContent = segment; segmentFilter.append(option); }});
statusFilter.addEventListener('change', renderPoints); segmentFilter.addEventListener('change', renderPoints);
document.getElementById('reset-filter').addEventListener('click', () => {{ statusFilter.value = 'all'; segmentFilter.value = 'all'; renderPoints(); }});
drawBase(); renderPoints();
</script>
</body>
</html>"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="校验供应商地图证据 JSON，并生成离线单文件 HTML。"
    )
    parser.add_argument("input", type=Path, help="符合 reference schema 的 UTF-8 JSON 文件")
    parser.add_argument("--output", "-o", type=Path, required=True, help="输出 HTML 文件路径")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        raw = json.loads(args.input.read_text(encoding="utf-8"))
        data = validate_and_normalize(raw)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(render_html(data), encoding="utf-8")
    except FileNotFoundError as exc:
        print(f"错误：找不到文件：{exc.filename}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"错误：JSON 无法解析：{exc}", file=sys.stderr)
        return 2
    except ValidationError as exc:
        print(f"校验失败：{exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"错误：无法写入输出文件：{exc}", file=sys.stderr)
        return 2
    print(f"已生成：{args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
