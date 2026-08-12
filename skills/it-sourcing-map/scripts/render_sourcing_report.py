#!/usr/bin/env python3
"""Validate neutral market-research JSON and render one offline HTML digest."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from string import Template
from typing import Any


ALLOWED_CLAIM_TYPES = {"fact", "vendor_claim", "inference", "reference", "estimate"}
ALLOWED_EVIDENCE_STATUSES = {"documented", "partial", "unverified"}
ALLOWED_PRICE_TYPES = {"public_price", "industry_estimate", "quote_required"}
ALLOWED_MARKET_KINDS = {"供给类型", "技术路线"}
ALLOWED_ENTERPRISE_REGIONS = {"mainland_china", "overseas", "unverified"}
REGION_ORDER = {"mainland_china": 0, "overseas": 1, "unverified": 2}
REGION_LABELS = {
    "mainland_china": "大陆企业",
    "overseas": "海外补充",
    "unverified": "主体待核验",
}
FORBIDDEN_DECISION_KEYS = {
    "decision",
    "shortlist",
    "short_list",
    "priority_vendors",
    "next_actions",
    "next_step",
    "recommendation",
    "recommendation_reason",
    "recommended_action",
    "why_contact",
    "fit",
    "fit_score",
    "rank",
    "ranking",
    "priority",
}
FORBIDDEN_DECISION_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"采购结论",
        r"推荐(?:供应商|厂商|名单|联系)",
        r"优先(?:推进|联系|采购|入围)",
        r"暂不建议",
        r"建议(?:联系|淘汰|入围|推进)",
        r"首轮候选",
        r"纳入首轮",
        r"下一步(?:建议|动作)",
        r"值得联系",
        r"最佳组合",
        r"进入\s*RFI",
        r"\bshort\s*list\b",
        r"\bshortlist\b",
    )
)
EVIDENCE_LABELS = {
    "documented": "有公开资料",
    "partial": "部分公开",
    "unverified": "公开资料不足",
}
PRICE_TYPE_LABELS = {
    "public_price": "公开价格",
    "industry_estimate": "行业估算",
    "quote_required": "需询价",
}
CLAIM_TYPE_LABELS = {
    "fact": "事实",
    "vendor_claim": "供应商声明",
    "inference": "分析归纳",
    "reference": "参考材料",
    "estimate": "估算",
}
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)


class ValidationError(ValueError):
    """Raised when market-research data violates the schema."""


def fail(path: str, message: str) -> None:
    raise ValidationError(f"{path}: {message}")


def validate_neutral_payload(value: Any, path: str = "root") -> None:
    """Reject decision-layer fields and procurement recommendations in v3 input."""
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key.casefold() in FORBIDDEN_DECISION_KEYS:
                fail(child_path, "中立调研数据不允许包含决策、排序或推进字段")
            validate_neutral_payload(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_neutral_payload(child, f"{path}[{index}]")
    elif isinstance(value, str):
        for pattern in FORBIDDEN_DECISION_PATTERNS:
            match = pattern.search(value)
            if match:
                fail(path, f"出现采购决策表述“{match.group(0)}”；请改写为事实、缺口或待核验项")


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


def optional_text(value: Any, fallback: str = "本次公开扫描未见") -> str:
    return str(value).strip() if value is not None and str(value).strip() else fallback


def join_clauses(values: list[str]) -> str:
    clauses = [value.strip().rstrip("。；; ") for value in values if value.strip()]
    return "；".join(clauses) + ("。" if clauses else "")


def neutralize_legacy_text(value: Any, fallback: str = "本次公开扫描未见") -> str:
    """Remove recommendation phrasing retained in pre-v3 research data."""
    text = optional_text(value, fallback)
    replacements = (
        ("把 SAST、SCA、IDE、CI/CD 门禁、漏洞管理和报表放在一个企业级平台中，最接近本次主采购对象。", "把 SAST、SCA、IDE、CI/CD 门禁、漏洞管理和报表放在同一企业级平台中。"),
        ("最接近本次主采购对象", "覆盖本次需求中的主平台模块"),
        ("GitLab 原生/开发者优先替代路线", "GitLab 原生与开发者工具路线"),
        ("GitLab 原生/开发者优先快速路线", "GitLab 原生与开发者工具组合"),
        ("GitLab 原生与开发者优先的替代技术路线", "GitLab 原生与开发者工具路线"),
        ("开发者优先 SaaS 价格下限参考", "开发者工具 SaaS 价格下限参考"),
        ("本次按中国大陆交付、私有化优先、源码原则上不出域的采购场景初筛", "本次研究边界按中国大陆交付、私有化部署、源码原则上不出域整理"),
        ("补强通用平台", "补充通用平台"),
        ("希望缩短集成周期、减少供应商数量、在 8 月底前完成选型。", "集成周期、供应商数量与选型时间是该路线的主要条件。"),
        ("原生代码与软件供应链均为高风险，且允许承担一定集成复杂度。", "同时覆盖原生代码与软件供应链，并增加多产品集成复杂度。"),
        ("需要真正闭环 60 项攻击面清单，而不是只对代码扫描工具打勾。", "覆盖范围包括源码、依赖、移动运行时、固件与实机攻击面。"),
        ("用于短期补位、低风险仓库或作为 POC 对照组。", "由 GitLab/CI 原生能力和开发者工具构成，覆盖范围取决于仓库类型与部署条件。"),
        ("选择对 C/C++/Android 更深的 SAST 引擎，同时独立采购 SCA/二进制成分分析，并用现有 GitLab 或安全开发平台统一门禁与结果。", "由面向 C/C++/Android 的深度 SAST、独立 SCA/二进制成分分析及现有 GitLab 或安全开发平台共同构成。"),
        ("选择对 C/C++/Android 更深的 SAST 引擎", "由面向 C/C++/Android 的深度 SAST 引擎"),
        ("并用现有 GitLab 或安全开发平台", "并通过现有 GitLab 或安全开发平台"),
        ("移动/固件专项另购服务", "移动/固件专项由独立产品或服务承担"),
        ("不能直接视为本项目完整主方案", "公开功能不足以证明完整覆盖本项目范围"),
        ("不满足严格离线要求", "公开资料未证明完全离线能力"),
        ("与严格私有化冲突", "其 SaaS-only 形态与严格私有化边界不同"),
        ("多语言、深度 SAST、GitLab/Jenkins/IDE、SCA 与统一治理强", "公开资料包含多语言、深度 SAST、GitLab/Jenkins/IDE、SCA 与统一治理"),
        ("C/C++/Java/Kotlin、SCA、Android Studio 与二进制成分分析强", "公开资料包含 C/C++/Java/Kotlin、SCA、Android Studio 与二进制成分分析"),
        ("SAST、语言、自定义查询、GitLab/Jenkins/IDE 强", "公开资料包含 SAST、语言、自定义查询及 GitLab/Jenkins/IDE 集成"),
        ("门禁、漏洞归一化、工单闭环和统一运营强", "公开资料包含门禁、漏洞归一化、工单闭环和统一运营"),
        ("SAST/SCA、二进制/源码、IDE/CI 与企业治理能力强", "公开资料包含 SAST/SCA、二进制/源码、IDE/CI 与企业治理"),
        ("GitLab MR/CI 门禁和统一流程强", "公开资料包含 GitLab MR/CI 门禁和统一流程"),
        ("MR、规则开发和开发者体验强", "公开资料包含 MR 扫描、规则开发与开发者反馈能力"),
        ("C/C++/Java 深度数据流适合内核和驱动补充", "公开资料涉及 C/C++/Java 深度数据流分析；内核和驱动场景仍需样本验证"),
        ("可用于 APK 快速基线与 POC 对照", "可提供 APK 快速基线扫描信息"),
        ("若作为补充，核验", "需核验"),
        ("仅在 SaaS 获准时核验", "需核验 SaaS 数据边界以及"),
        ("建议部署在隔离 POC 环境验证资源消耗和构建阻断", "资源消耗和构建阻断仍需在隔离 POC 环境验证"),
        ("可作为首轮端到端 POC", "已有端到端接入资料，实际能力仍需 POC 核验"),
        ("建议部署在隔离 POC 环境验证", "资源消耗和构建阻断仍需在隔离 POC 环境验证"),
        ("敏感项目优先核验", "敏感项目需核验"),
        ("采购范围需拆包或允许组合方案", "单一产品与组合方案的覆盖边界不同"),
        ("不接受只报云平台打包总价", "云平台打包总价无法说明各模块成本"),
        ("需要求", "仍需"),
        ("匹配度高", "公开资料覆盖较多"),
        ("高匹配", "公开资料覆盖较多"),
        ("方向匹配", "公开资料涉及该方向"),
        ("部分匹配", "公开资料覆盖部分条目"),
        ("适配度高", "公开资料覆盖较多"),
        ("最佳组合：", "组合式："),
        ("最适合", "常见于"),
        ("适合", "常见于"),
        ("值得", "可供观察"),
        ("匹配；", "有公开资料覆盖；"),
        ("匹配，", "有公开资料覆盖，"),
        ("匹配。", "有公开资料覆盖。"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def text_list(value: Any, path: str, required: bool = False) -> list[str]:
    values = as_list(value, path)
    normalized = [nonempty_text(item, f"{path}[{index}]") for index, item in enumerate(values)]
    if required and not normalized:
        fail(path, "至少需要一项")
    return normalized


def validate_date(value: Any, path: str, allow_undisclosed: bool = False) -> str:
    text = nonempty_text(value, path)
    if allow_undisclosed and text == "日期未公开":
        return text
    if not DATE_PATTERN.fullmatch(text):
        suffix = " 或‘日期未公开’" if allow_undisclosed else ""
        fail(path, f"只允许 YYYY-MM-DD{suffix}")
    try:
        dt.date.fromisoformat(text)
    except ValueError:
        fail(path, "不是有效日期")
    return text


def validate_sources(value: Any) -> tuple[list[dict[str, str]], set[str]]:
    normalized: list[dict[str, str]] = []
    identifiers: set[str] = set()
    for index, raw in enumerate(as_list(value, "sources")):
        path = f"sources[{index}]"
        item = as_object(raw, path)
        identifier = nonempty_text(item.get("id"), f"{path}.id")
        if identifier in identifiers:
            fail(f"{path}.id", "source_id 不能重复")
        identifiers.add(identifier)
        claim_type = nonempty_text(item.get("claim_type"), f"{path}.claim_type")
        if claim_type not in ALLOWED_CLAIM_TYPES:
            fail(f"{path}.claim_type", "来源类型不合法")
        url = optional_text(item.get("url"), "")
        locator = optional_text(item.get("source_locator"), "")
        if not url and not locator:
            fail(path, "必须提供 url 或 source_locator")
        if url and not URL_PATTERN.match(url):
            fail(f"{path}.url", "只允许 http:// 或 https:// 链接；本地材料请改用 source_locator")
        normalized.append(
            {
                "id": identifier,
                "subject": nonempty_text(item.get("subject"), f"{path}.subject"),
                "title": nonempty_text(item.get("title"), f"{path}.title"),
                "date": validate_date(item.get("date"), f"{path}.date", True),
                "claim_type": claim_type,
                "url": url,
                "source_locator": locator,
            }
        )
    return normalized, identifiers


def source_ids(value: Any, path: str, known_ids: set[str], required: bool = False) -> list[str]:
    values = as_list(value, path)
    if required and not values:
        fail(path, "至少需要一个有效 source_id")
    normalized: list[str] = []
    for index, raw in enumerate(values):
        identifier = nonempty_text(raw, f"{path}[{index}]")
        if identifier not in known_ids:
            fail(f"{path}[{index}]", f"引用不存在的 source_id：{identifier}")
        if identifier not in normalized:
            normalized.append(identifier)
    return normalized


def validate_all_references(value: Any, path: str, known_ids: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key == "source_ids":
                source_ids(child, child_path, known_ids)
            elif key == "source_id":
                identifier = nonempty_text(child, child_path)
                if identifier not in known_ids:
                    fail(child_path, f"引用不存在的 source_id：{identifier}")
            else:
                validate_all_references(child, child_path, known_ids)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_all_references(child, f"{path}[{index}]", known_ids)


def normalize_scope(data: dict[str, Any]) -> dict[str, Any]:
    item = as_object(data.get("scope"), "scope")
    is_v3 = data.get("schema_version") == "3.0"
    requirements_key = "requirements" if is_v3 else "p0_requirements"
    constraints_key = "constraints" if is_v3 else "procurement_constraints"
    questions_key = "open_questions" if is_v3 else "pending_items"
    constraints = text_list(item.get(constraints_key, []), f"scope.{constraints_key}")
    scan_scope = text_list(item.get("scan_scope", []), "scope.scan_scope", True)
    if not is_v3:
        constraints = [neutralize_legacy_text(value) for value in constraints]
        scan_scope = [neutralize_legacy_text(value) for value in scan_scope]
    geography = nonempty_text(item.get("geography"), "scope.geography")
    if not is_v3:
        geography = neutralize_legacy_text(geography)
    return {
        "buying_object": nonempty_text(item.get("buying_object"), "scope.buying_object"),
        "use_cases": text_list(item.get("use_cases", []), "scope.use_cases", True),
        "requirements": text_list(
            item.get(requirements_key, []), f"scope.{requirements_key}", True
        ),
        "geography": geography,
        "scan_scope": scan_scope,
        "constraints": constraints,
        "open_questions": text_list(item.get(questions_key, []), f"scope.{questions_key}"),
        "region_coverage_exception": optional_text(
            item.get("region_coverage_exception"), ""
        )
        if is_v3
        else "",
    }


def normalize_market_structure(data: dict[str, Any], known_ids: set[str]) -> list[dict[str, Any]]:
    if data.get("schema_version") == "3.0":
        normalized: list[dict[str, Any]] = []
        seen_names: set[str] = set()
        route_started = False
        supply_count = 0
        for index, raw in enumerate(as_list(data.get("market_structure", []), "market_structure")):
            path = f"market_structure[{index}]"
            item = as_object(raw, path)
            kind = nonempty_text(item.get("kind"), f"{path}.kind")
            if kind not in ALLOWED_MARKET_KINDS:
                fail(f"{path}.kind", "只允许“供给类型”或“技术路线”")
            if kind == "技术路线":
                route_started = True
            else:
                supply_count += 1
                if route_started:
                    fail(path, "供给类型必须全部列在技术路线之前")
            name = nonempty_text(item.get("name"), f"{path}.name")
            name_key = name.casefold()
            if name_key in seen_names:
                fail(f"{path}.name", "市场结构名称不能重复")
            seen_names.add(name_key)
            normalized.append(
                {
                    "kind": kind,
                    "name": name,
                    "solves": nonempty_text(item.get("solves"), f"{path}.solves"),
                    "product_forms": text_list(
                        item.get("product_forms", []), f"{path}.product_forms", True
                    ),
                    "boundary": nonempty_text(item.get("boundary"), f"{path}.boundary"),
                    "tradeoffs": nonempty_text(item.get("tradeoffs"), f"{path}.tradeoffs"),
                    "source_ids": source_ids(
                        item.get("source_ids", []), f"{path}.source_ids", known_ids, True
                    ),
                }
            )
        if supply_count == 0:
            fail("market_structure", "至少需要一个可承载供应商的“供给类型”")
        return normalized

    normalized = []
    for index, raw in enumerate(as_list(data.get("market_landscape", []), "market_landscape")):
        path = f"market_landscape[{index}]"
        item = as_object(raw, path)
        normalized.append(
            {
                "kind": "供给类型",
                "name": neutralize_legacy_text(item.get("segment")),
                "solves": neutralize_legacy_text(item.get("what_it_solves")),
                "product_forms": text_list(
                    item.get("product_forms", []), f"{path}.product_forms", True
                ),
                "boundary": neutralize_legacy_text(item.get("best_for")),
                "tradeoffs": neutralize_legacy_text(item.get("tradeoffs")),
                "source_ids": source_ids(
                    item.get("source_ids", []), f"{path}.source_ids", known_ids, True
                ),
            }
        )
    for index, raw in enumerate(as_list(data.get("technology_routes", []), "technology_routes")):
        path = f"technology_routes[{index}]"
        item = as_object(raw, path)
        normalized.append(
            {
                "kind": "技术路线",
                "name": neutralize_legacy_text(item.get("name")),
                "solves": neutralize_legacy_text(item.get("how_it_works")),
                "product_forms": ["技术路线"],
                "boundary": neutralize_legacy_text(item.get("best_for")),
                "tradeoffs": join_clauses(
                    [
                        neutralize_legacy_text(item.get("limitations")),
                        neutralize_legacy_text(item.get("cost_profile")),
                    ]
                ),
                "source_ids": source_ids(
                    item.get("source_ids", []), f"{path}.source_ids", known_ids, True
                ),
            }
        )
    return normalized


def legacy_enterprise_region(category: str) -> tuple[str, str]:
    """Conservatively recover explicit region labels from legacy category text."""
    if "国内" in category or "大陆" in category:
        return "mainland_china", f"旧版调研分类“{category}”明确标注为国内/大陆；正式准入仍需核验能力、签约与履约主体"
    if "国际" in category or "海外" in category:
        return "overseas", f"旧版调研分类“{category}”明确标注为国际/海外；中国区签约与履约主体仍需核验"
    return "unverified", "旧版数据未单列企业地域；需核验产品能力主体、注册地、签约主体与履约主体"


def normalize_vendors(data: dict[str, Any], known_ids: set[str]) -> list[dict[str, Any]]:
    if data.get("schema_version") == "3.0":
        raw_vendors = as_list(data.get("vendors", []), "vendors")
        if not raw_vendors:
            fail("vendors", "至少需要一家已识别厂商或方案")
        normalized: list[dict[str, Any]] = []
        seen: set[str] = set()
        for index, raw in enumerate(raw_vendors):
            path = f"vendors[{index}]"
            item = as_object(raw, path)
            vendor = nonempty_text(item.get("vendor"), f"{path}.vendor")
            key = vendor.casefold()
            if key in seen:
                fail(f"{path}.vendor", "同一供应商不得重复")
            seen.add(key)
            evidence_status = nonempty_text(
                item.get("evidence_status"), f"{path}.evidence_status"
            )
            if evidence_status not in ALLOWED_EVIDENCE_STATUSES:
                fail(f"{path}.evidence_status", "证据状态不合法")
            enterprise_region = nonempty_text(
                item.get("enterprise_region"), f"{path}.enterprise_region"
            )
            if enterprise_region not in ALLOWED_ENTERPRISE_REGIONS:
                fail(
                    f"{path}.enterprise_region",
                    "只允许 mainland_china、overseas 或 unverified",
                )
            citations = source_ids(
                item.get("source_ids", []),
                f"{path}.source_ids",
                known_ids,
                required=evidence_status != "unverified",
            )
            region_citations = source_ids(
                item.get("region_source_ids", []),
                f"{path}.region_source_ids",
                known_ids,
                required=enterprise_region != "unverified",
            )
            gaps = text_list(item.get("information_gaps", []), f"{path}.information_gaps", True)
            if enterprise_region == "unverified" and not any(
                keyword in gap for gap in gaps for keyword in ("主体", "注册", "总部", "地域")
            ):
                fail(
                    f"{path}.information_gaps",
                    "主体地域待核验时，必须列出能力主体、注册地、签约主体或履约主体缺口",
                )
            normalized.append(
                {
                    "category": nonempty_text(item.get("category"), f"{path}.category"),
                    "vendor": vendor,
                    "solution": nonempty_text(item.get("solution"), f"{path}.solution"),
                    "product_form": nonempty_text(item.get("product_form"), f"{path}.product_form"),
                    "public_coverage": nonempty_text(
                        item.get("public_coverage"), f"{path}.public_coverage"
                    ),
                    "capabilities": text_list(item.get("capabilities", []), f"{path}.capabilities"),
                    "deployment_integration": optional_text(item.get("deployment_integration")),
                    "commercial_model": optional_text(item.get("commercial_model")),
                    "information_gaps": gaps,
                    "evidence_status": evidence_status,
                    "enterprise_region": enterprise_region,
                    "region_basis": nonempty_text(
                        item.get("region_basis"), f"{path}.region_basis"
                    ),
                    "region_source_ids": region_citations,
                    "business_entry": optional_text(
                        item.get("business_entry"), "本次公开扫描未见商务入口"
                    ),
                    "source_ids": citations,
                }
            )
        return normalized

    detail_by_vendor = {
        optional_text(item.get("name"), "").casefold(): item
        for item in as_list(data.get("priority_vendors", []), "priority_vendors")
        if isinstance(item, dict) and optional_text(item.get("name"), "")
    }
    raw_vendors = as_list(data.get("long_list", []), "long_list")
    if not raw_vendors:
        fail("long_list", "至少需要一家已识别厂商或方案")
    normalized = []
    seen = set()
    for index, raw in enumerate(raw_vendors):
        path = f"long_list[{index}]"
        item = as_object(raw, path)
        vendor = nonempty_text(item.get("vendor"), f"{path}.vendor")
        raw_category = nonempty_text(item.get("category"), f"{path}.category")
        enterprise_region, region_basis = legacy_enterprise_region(raw_category)
        key = vendor.casefold()
        if key in seen:
            fail(f"{path}.vendor", "同一供应商不得重复")
        seen.add(key)
        detail = detail_by_vendor.get(key, {})
        citations = source_ids(item.get("source_ids", []), f"{path}.source_ids", known_ids)
        old_status = optional_text(item.get("status"), "")
        evidence_status = (
            "unverified"
            if not citations
            else "partial"
            if old_status == "pending_verification"
            else "documented"
        )
        gaps: list[str] = []
        validation = optional_text(item.get("validation_needed"), "")
        if validation and validation.casefold() not in {"无", "无需", "不适用", "n/a", "na", "none", "-"}:
            gaps.append(validation)
        for gap in detail.get("gaps_risks", []) if isinstance(detail, dict) else []:
            if isinstance(gap, str) and gap.strip() and gap.strip() not in gaps:
                gaps.append(gap.strip())
        if not gaps:
            gaps = ["本次公开扫描未见完整的需求逐项覆盖说明。"]
        detail_sources = detail.get("source_ids", []) if isinstance(detail, dict) else []
        for identifier in detail_sources:
            if identifier in known_ids and identifier not in citations:
                citations.append(identifier)
        normalized.append(
            {
                "category": raw_category,
                "vendor": vendor,
                "solution": nonempty_text(item.get("solution"), f"{path}.solution"),
                "product_form": nonempty_text(item.get("product_form"), f"{path}.product_form"),
                "public_coverage": neutralize_legacy_text(item.get("requirement_match")),
                "capabilities": [
                    value.strip()
                    for value in detail.get("core_capabilities", [])
                    if isinstance(value, str) and value.strip()
                ],
                "deployment_integration": neutralize_legacy_text(detail.get("deployment_integration")),
                "commercial_model": neutralize_legacy_text(detail.get("commercial_model")),
                "information_gaps": gaps,
                "evidence_status": evidence_status,
                "enterprise_region": enterprise_region,
                "region_basis": region_basis,
                "region_source_ids": citations[:1],
                "business_entry": nonempty_text(
                    item.get("business_entry"), f"{path}.business_entry"
                ),
                "source_ids": citations,
            }
        )
    return normalized


def normalize_commercial(data: dict[str, Any], known_ids: set[str]) -> list[dict[str, Any]]:
    is_v3 = data.get("schema_version") == "3.0"
    raw_items = (
        as_list(data.get("commercial_signals", []), "commercial_signals")
        if is_v3
        else as_list(
            as_object(data.get("commercial_benchmark"), "commercial_benchmark").get(
                "pricing_models", []
            ),
            "commercial_benchmark.pricing_models",
        )
    )
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_items):
        path = f"commercial_signals[{index}]" if is_v3 else f"commercial_benchmark.pricing_models[{index}]"
        item = as_object(raw, path)
        price_type = nonempty_text(item.get("price_type"), f"{path}.price_type")
        if price_type not in ALLOWED_PRICE_TYPES:
            fail(f"{path}.price_type", "价格类型不合法")
        signal = nonempty_text(item.get("price_signal"), f"{path}.price_signal")
        if price_type == "industry_estimate" and "估算" not in signal:
            fail(f"{path}.price_signal", "行业估算必须明确标注‘估算’")
        if price_type == "quote_required" and not ("询价" in signal or "quote" in signal.casefold()):
            fail(f"{path}.price_signal", "询价项必须明确写‘需询价’")
        if is_v3 and price_type == "public_price":
            has_amount = bool(re.search(r"\d", signal)) or "免费" in signal
            has_currency = bool(
                re.search(r"[¥￥$€£]|\b(?:USD|CNY|RMB|EUR|GBP)\b|人民币|美元|欧元|英镑", signal, re.IGNORECASE)
            )
            has_unit = bool(
                re.search(
                    r"/|每|\bper\b|月|年|次|席位|用户|开发者|请求|节点|项目|仓库|应用|GB|TB",
                    signal,
                    re.IGNORECASE,
                )
            )
            if not (has_amount and has_currency and has_unit):
                fail(
                    f"{path}.price_signal",
                    "公开价格必须同时写明金额、币种和计费单位；否则改标为行业估算或需询价",
                )
        if is_v3:
            cost_context = nonempty_text(item.get("cost_context"), f"{path}.cost_context")
            limitations = nonempty_text(item.get("limitations"), f"{path}.limitations")
            subject = nonempty_text(item.get("subject"), f"{path}.subject")
        else:
            subject = neutralize_legacy_text(item.get("route_or_segment"))
            cost_context = join_clauses(
                [
                    f"一次性：{optional_text(item.get('one_time_costs'))}",
                    f"持续性：{optional_text(item.get('recurring_costs'))}",
                    f"TCO：{optional_text(item.get('tco_notes'))}",
                ]
            )
            limitations = "该价格信号用于说明计费方式或公开价位，不代表本项目企业报价。"
        normalized.append(
            {
                "subject": subject,
                "billing_model": nonempty_text(item.get("billing_model"), f"{path}.billing_model"),
                "price_type": price_type,
                "price_signal": signal,
                "cost_context": cost_context,
                "limitations": limitations,
                "source_ids": source_ids(
                    item.get("source_ids", []), f"{path}.source_ids", known_ids, True
                ),
            }
        )
    return normalized


def normalize_risks(data: dict[str, Any], known_ids: set[str]) -> list[dict[str, Any]]:
    is_v3 = data.get("schema_version") == "3.0"
    raw_items = as_list(
        data.get("risk_signals", []) if is_v3 else data.get("key_risks", []),
        "risk_signals" if is_v3 else "key_risks",
    )
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_items):
        path = f"risk_signals[{index}]" if is_v3 else f"key_risks[{index}]"
        item = as_object(raw, path)
        normalized.append(
            {
                "topic": nonempty_text(
                    item.get("topic") if is_v3 else item.get("risk"),
                    f"{path}.{'topic' if is_v3 else 'risk'}",
                ),
                "observed_signal": nonempty_text(
                    item.get("observed_signal") if is_v3 else item.get("impact"),
                    f"{path}.{'observed_signal' if is_v3 else 'impact'}",
                ),
                "relevance": nonempty_text(item.get("relevance"), f"{path}.relevance")
                if is_v3
                else "该事项与需求中的能力、部署、数据或验收边界相关。",
                "information_needed": nonempty_text(
                    item.get("information_needed") if is_v3 else item.get("validation"),
                    f"{path}.{'information_needed' if is_v3 else 'validation'}",
                ),
                "source_ids": source_ids(
                    item.get("source_ids", []), f"{path}.source_ids", known_ids, True
                ),
            }
        )
    return normalized


def normalize_trends(data: dict[str, Any], known_ids: set[str]) -> list[dict[str, Any]]:
    is_v3 = data.get("schema_version") == "3.0"
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(as_list(data.get("trends", []), "trends")):
        path = f"trends[{index}]"
        item = as_object(raw, path)
        normalized.append(
            {
                "trend": nonempty_text(item.get("trend"), f"{path}.trend"),
                "horizon": nonempty_text(item.get("horizon"), f"{path}.horizon"),
                "observed_change": nonempty_text(
                    item.get("observed_change") if is_v3 else item.get("procurement_impact"),
                    f"{path}.{'observed_change' if is_v3 else 'procurement_impact'}",
                ),
                "possible_relevance": nonempty_text(
                    item.get("possible_relevance"), f"{path}.possible_relevance"
                )
                if is_v3
                else "可能影响产品边界、部署方式、成本结构或信息可移植性；具体影响由用户结合项目判断。",
                "source_ids": source_ids(
                    item.get("source_ids", []), f"{path}.source_ids", known_ids, True
                ),
            }
        )
    return normalized


def validate_and_normalize(raw: Any) -> dict[str, Any]:
    data = as_object(raw, "root")
    schema_version = optional_text(data.get("schema_version"), "legacy")
    if schema_version not in {"legacy", "1.0", "2.0", "3.0"}:
        fail("schema_version", "只支持旧版、1.0、2.0 或 3.0")
    if schema_version == "3.0":
        validate_neutral_payload(data)
    sources, known_ids = validate_sources(data.get("sources", []))
    validate_all_references(
        {key: value for key, value in data.items() if key != "sources"}, "root", known_ids
    )
    scope = normalize_scope(data)
    market_structure = normalize_market_structure(data, known_ids)
    vendors = normalize_vendors(data, known_ids)
    commercial_signals = normalize_commercial(data, known_ids)
    risk_signals = normalize_risks(data, known_ids)
    trends = normalize_trends(data, known_ids)
    if schema_version == "3.0":
        supply_groups = {
            item["name"] for item in market_structure if item["kind"] == "供给类型"
        }
        unknown_groups = sorted(
            {item["category"] for item in vendors if item["category"] not in supply_groups}
        )
        if unknown_groups:
            fail(
                "vendors.category",
                "必须与 market_structure 中的供给类型名称一致：" + "、".join(unknown_groups),
            )
        if not commercial_signals:
            fail(
                "commercial_signals",
                "至少需要一条公开价格、行业估算或“需询价”信号；没有公开价不等于没有商业信息",
            )
        if not risk_signals:
            fail("risk_signals", "至少需要一条有来源的风险或信息缺口")
        mainland_count = sum(
            item["enterprise_region"] == "mainland_china" for item in vendors
        )
        overseas_count = sum(item["enterprise_region"] == "overseas" for item in vendors)
        if mainland_count * 2 <= len(vendors) and not scope["region_coverage_exception"]:
            fail(
                "vendors.enterprise_region",
                "大陆企业必须占候选池严格多数；若市场客观供给不足，必须在 scope.region_coverage_exception 记录证据化例外",
            )
        if mainland_count <= overseas_count and not scope["region_coverage_exception"]:
            fail(
                "vendors.enterprise_region",
                "大陆企业数量必须多于海外企业；不得用主体待核验项目稀释该强约束",
            )
        source_by_id = {item["id"]: item for item in sources}
        for index, signal in enumerate(commercial_signals):
            if signal["price_type"] != "public_price":
                continue
            if any(source_by_id[source_id]["date"] == "日期未公开" for source_id in signal["source_ids"]):
                fail(
                    f"commercial_signals[{index}].source_ids",
                    "公开价格必须引用带明确日期的来源，避免把过期价格当作当前口径",
                )
    return {
        "schema_version": schema_version,
        "title": optional_text(data.get("title"), "市场调研信息整合"),
        "category": nonempty_text(data.get("category"), "category"),
        "research_date": validate_date(data.get("research_date"), "research_date"),
        "scope": scope,
        "market_structure": market_structure,
        "vendors": vendors,
        "commercial_signals": commercial_signals,
        "risk_signals": risk_signals,
        "trends": trends,
        "sources": sources,
    }


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def truncate_text(value: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    if len(text) <= limit:
        return text
    return text[: max(1, limit - 1)].rstrip("，。；、,. ;") + "…"


def list_markup(items: list[str], empty: str = "本次公开扫描未见") -> str:
    if not items:
        return f'<span class="muted">{esc(empty)}</span>'
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def link_markup(value: str, label: str | None = None) -> str:
    if re.match(r"^https?://", value, re.IGNORECASE):
        return f'<a href="{esc(value)}" target="_blank" rel="noopener noreferrer">{esc(label or value)}</a>'
    return esc(value)


def source_badges(ids: list[str]) -> str:
    if not ids:
        return '<span class="source-chip pending">待补证据</span>'
    return " ".join(
        f'<a class="source-chip" href="#source-{esc(identifier)}">{esc(identifier)}</a>'
        for identifier in ids
    )


def smart_business_markup(value: str) -> str:
    match = re.search(r"https?://[^\s；;，,]+", value, re.IGNORECASE)
    if not match:
        return esc(value)
    url = match.group(0)
    before = value[: match.start()].strip(" ；;，,")
    after = value[match.end() :].strip(" ；;，,")
    parts = [esc(before)] if before else []
    parts.append(link_markup(url, "商务入口"))
    if after:
        parts.append(esc(after))
    return " · ".join(parts)


def slug(value: str) -> str:
    compact = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    if compact:
        return compact
    return "c-" + hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]


def layer_color(index: int) -> str:
    """Generate stable, distinct category colors without implying rank."""
    hue = (28 + (index - 1) * 137.508) % 360
    return f"hsl({hue:.1f} 56% 46%)"


def legacy_group_for(category: str, supply_names: list[str]) -> str:
    """Map legacy fine-grained labels onto the report's coarse market layers."""

    def find_name(*needles: str) -> str:
        for name in supply_names:
            if any(needle.casefold() in name.casefold() for needle in needles):
                return name
        return ""

    if "深度 SAST" in category:
        target = find_name("嵌入式", "深度 SAST")
    elif "移动" in category:
        target = find_name("移动应用", "运行时")
    elif "固件" in category or "SCA/二进制" in category:
        target = find_name("固件", "二进制供应链")
    elif "平台编排" in category:
        target = find_name("编排", "运营平台")
    elif "开发者" in category or category.startswith("SCA 专项") or category.startswith("SCA+服务"):
        target = find_name("GitLab", "开发者优先")
    else:
        target = find_name("一体化", "私有 AppSec")
    return target or category.split("｜", 1)[0]


def grouped_vendors(data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    supply_segments = [
        item for item in data["market_structure"] if item["kind"] == "供给类型"
    ]
    routes = [item for item in data["market_structure"] if item["kind"] == "技术路线"]
    supply_names = [item["name"] for item in supply_segments]
    buckets: dict[str, list[dict[str, Any]]] = {name: [] for name in supply_names}

    for vendor in data["vendors"]:
        group = (
            vendor["category"]
            if data["schema_version"] == "3.0"
            else legacy_group_for(vendor["category"], supply_names)
        )
        buckets.setdefault(group, []).append(vendor)

    for bucket in buckets.values():
        bucket.sort(key=lambda item: REGION_ORDER[item["enterprise_region"]])

    segment_by_name = {item["name"]: item for item in supply_segments}
    groups: list[dict[str, Any]] = []
    ordered_names = supply_names + [name for name in buckets if name not in supply_names]
    for index, name in enumerate(ordered_names, start=1):
        segment = segment_by_name.get(name)
        groups.append(
            {
                "index": index,
                "id": f"market-group-{index}",
                "name": name,
                "solves": segment["solves"] if segment else "该分组汇总同类产品与服务信息。",
                "product_forms": segment["product_forms"] if segment else [],
                "boundary": segment["boundary"] if segment else "具体边界以厂商公开资料为准。",
                "tradeoffs": segment["tradeoffs"] if segment else "本次公开扫描未见统一口径。",
                "source_ids": segment["source_ids"] if segment else [],
                "vendors": buckets.get(name, []),
                "mainland_count": sum(
                    item["enterprise_region"] == "mainland_china"
                    for item in buckets.get(name, [])
                ),
                "overseas_count": sum(
                    item["enterprise_region"] == "overseas"
                    for item in buckets.get(name, [])
                ),
                "unverified_count": sum(
                    item["enterprise_region"] == "unverified"
                    for item in buckets.get(name, [])
                ),
            }
        )
    return groups, routes


def render_html(data: dict[str, Any]) -> str:
    template_path = Path(__file__).with_name("sourcing_dashboard_template.html")
    if not template_path.exists():
        raise OSError(f"缺少 HTML 模板：{template_path}")

    scope = data["scope"]
    vendors = data["vendors"]
    groups, routes = grouped_vendors(data)
    public_prices = sum(
        1 for item in data["commercial_signals"] if item["price_type"] == "public_price"
    )

    nav_links = ['<a class="nav-link" href="#market-map">市场分层</a>']
    nav_links.extend(
        f'<a class="nav-link" href="#{esc(group["id"])}">M{group["index"]} {esc(truncate_text(group["name"], 10))}</a>'
        for group in groups
    )
    nav_links.append('<a class="nav-link" href="#price">价格</a>')
    if scope["constraints"]:
        nav_links.append('<a class="nav-link" href="#constraints">约束</a>')
    if data["trends"]:
        nav_links.append('<a class="nav-link" href="#trends">趋势</a>')
    nav_links.extend(
        [
            '<a class="nav-link" href="#risks">风险</a>',
            '<a class="nav-link" href="#longlist">Long List</a>',
        ]
    )

    def player_line(group: dict[str, Any], region: str, limit: int) -> str:
        players = [
            item["vendor"]
            for item in group["vendors"]
            if item["enterprise_region"] == region
        ]
        if not players:
            return ""
        visible = players[:limit]
        remaining = len(players) - len(visible)
        names = " / ".join(visible) + (f" / +{remaining}" if remaining else "")
        return (
            f'<span class="player-line {esc(region)}"><b>{esc(REGION_LABELS[region])}</b>'
            f'<span>{esc(names)}</span></span>'
        )

    max_group_vendors = max((len(group["vendors"]) for group in groups), default=1)
    market_map_rows = "".join(
        '<a class="market-layer" data-vendor-count="{count}" '
        'style="--layer-color:{color};--layer-width:{width}%" href="#{identifier}">'
        '<span class="layer-code">M{index}</span>'
        '<span class="layer-copy"><strong>{name}</strong><small>{solves}</small>'
        '<span class="layer-players">{mainland}{overseas}{unverified}</span></span>'
        '<span class="layer-meta"><b>{count} 家</b><small>{forms}</small></span>'
        "</a>".format(
            color=layer_color(group["index"]),
            width=round(68 + 30 * len(group["vendors"]) / max_group_vendors, 1),
            identifier=esc(group["id"]),
            index=group["index"],
            name=esc(group["name"]),
            solves=esc(truncate_text(group["solves"], 72)),
            mainland=player_line(group, "mainland_china", 5),
            overseas=player_line(group, "overseas", 3),
            unverified=player_line(group, "unverified", 2),
            count=len(group["vendors"]),
            forms=esc(" / ".join(group["product_forms"][:2]) or "形态待补充"),
        )
        for group in groups
    ) or '<p class="empty-state">当前资料不足以形成可核验的市场分层。</p>'

    route_rows = "".join(
        '<tr><td><span class="route-code">R{index}</span><strong>{name}</strong></td>'
        '<td>{solves}</td><td>{boundary}</td><td>{tradeoffs}{sources}</td></tr>'.format(
            index=index,
            name=esc(item["name"]),
            solves=esc(item["solves"]),
            boundary=esc(item["boundary"]),
            tradeoffs=esc(item["tradeoffs"]),
            sources=source_badges(item["source_ids"]),
        )
        for index, item in enumerate(routes, start=1)
    ) or '<tr><td colspan="4" class="empty-cell">当前资料未单列技术路线。</td></tr>'

    route_meta_chip = (
        f'<span class="meta-chip">技术路线 <strong>{len(routes)} 条</strong></span>'
        if routes
        else ""
    )
    route_block = (
        '<details class="route-block"><summary><strong>技术路线横向说明</strong>'
        f'<span>{len(routes)} 条路线 · 展开查看构成、适用条件与已知取舍</span></summary>'
        '<div class="table-wrap"><table class="route-table"><thead><tr>'
        '<th>路线</th><th>构成方式</th><th>涉及条件</th><th>已知取舍</th>'
        f'</tr></thead><tbody>{route_rows}</tbody></table></div></details>'
        if routes
        else ""
    )

    def vendor_card(item: dict[str, Any], group_index: int) -> str:
        visible_capabilities = item["capabilities"][:1]
        tags = [item["product_form"], *visible_capabilities]
        tag_markup = "".join(
            f'<span class="tag">{esc(truncate_text(tag, 24))}</span>' for tag in tags if tag
        )
        hidden_capability_count = max(0, len(item["capabilities"]) - len(visible_capabilities))
        if hidden_capability_count:
            tag_markup += f'<span class="tag">+{hidden_capability_count} 项</span>'
        all_sources = list(dict.fromkeys([*item["source_ids"], *item["region_source_ids"]]))
        return (
            '<article class="vendor-card" id="vendor-{vendor_slug}" data-market-group="{group_index}" '
            'data-enterprise-region="{region}" data-vendor-name="{vendor_attr}">'
            '<div class="vendor-top"><div><h3>{vendor}</h3><p class="product">{solution}</p></div>'
            '<div class="status-stack"><span class="region-status {region}">{region_label}</span>'
            '<span class="evidence-status {evidence}">{evidence_label}</span></div></div>'
            '<p class="coverage">{coverage}</p><div class="tags">{tags}</div>'
            '<div class="vendor-snapshot"><p><span>部署 / 数据</span>{deployment}</p>'
            '<p><span>价格状态</span>{commercial}</p></div>'
            '<p class="key-gap"><span>关键待核验</span>{gap}</p>'
            '<details class="vendor-more"><summary>完整能力、边界与来源</summary>'
            '<div class="vendor-detail-grid">'
            '<div class="wide"><b>公开覆盖</b><p>{coverage_full}</p></div>'
            '<div><b>能力要点</b>{capabilities}</div>'
            '<div><b>产品形态</b><p>{product_form}</p></div>'
            '<div><b>部署 / 接入</b><p>{deployment_full}</p></div>'
            '<div><b>商业信息</b><p>{commercial_full}</p></div>'
            '<div class="wide"><b>企业地域依据</b><p>{region_basis}</p>{region_sources}</div>'
            '<div class="wide"><b>全部信息缺口</b>{gaps}</div>'
            '<div class="wide"><b>商务入口原文</b><p>{business_full}</p></div>'
            '</div></details>'
            '<div class="vendor-foot"><span>{business}</span><span>{sources}</span></div>'
            "</article>"
        ).format(
            vendor_slug=esc(slug(item["vendor"])),
            group_index=group_index,
            region=esc(item["enterprise_region"]),
            region_label=esc(REGION_LABELS[item["enterprise_region"]]),
            vendor_attr=esc(item["vendor"]),
            vendor=esc(item["vendor"]),
            solution=esc(truncate_text(item["solution"], 86)),
            evidence=esc(item["evidence_status"]),
            evidence_label=esc(EVIDENCE_LABELS[item["evidence_status"]]),
            coverage=esc(truncate_text(item["public_coverage"], 92)),
            coverage_full=esc(item["public_coverage"]),
            tags=tag_markup,
            deployment=esc(truncate_text(item["deployment_integration"], 56)),
            deployment_full=esc(item["deployment_integration"]),
            commercial=esc(truncate_text(item["commercial_model"], 56)),
            commercial_full=esc(item["commercial_model"]),
            gap=esc(truncate_text(item["information_gaps"][0], 72)),
            capabilities=list_markup(item["capabilities"], "本次公开扫描未见能力明细"),
            product_form=esc(item["product_form"]),
            region_basis=esc(item["region_basis"]),
            region_sources=source_badges(item["region_source_ids"]),
            gaps=list_markup(item["information_gaps"]),
            business=smart_business_markup(item["business_entry"]),
            business_full=esc(item["business_entry"]),
            sources=source_badges(all_sources),
        )

    large_mode = len(vendors) >= 19 or len(groups) >= 6
    collapsible_groups = len(vendors) > 6

    def vendor_group(group: dict[str, Any]) -> str:
        vendor_count = len(group["vendors"])
        grid_size = "count-1" if vendor_count == 1 else "count-2" if vendor_count == 2 else "count-3plus"
        header = (
            '<div class="section-header"><span class="tier-badge" style="--layer-color:{color}">M{index}</span>'
            '<h2>{name}</h2><p>大陆 {mainland} · 海外 {overseas} · 待核验 {unverified}<br>{forms}</p></div>'
        ).format(
            color=layer_color(group["index"]),
            index=group["index"],
            name=esc(group["name"]),
            mainland=group["mainland_count"],
            overseas=group["overseas_count"],
            unverified=group["unverified_count"],
            forms=esc(" / ".join(group["product_forms"][:4]) or "产品形态待补充"),
        )
        cards = "".join(vendor_card(item, group["index"]) for item in group["vendors"])
        cards = cards or '<p class="empty-state">本次扫描未在该层识别到可核验厂商。</p>'
        if collapsible_groups:
            open_attr = "" if large_mode else " open"
            return (
                f'<details id="{esc(group["id"])}" class="vendor-section observed-section"{open_attr}>'
                f'<summary>{header}</summary><div class="vendor-grid {grid_size}">{cards}</div></details>'
            )
        return (
            f'<section id="{esc(group["id"])}" class="vendor-section observed-section">'
            f'{header}<div class="vendor-grid {grid_size}">{cards}</div></section>'
        )

    vendor_sections = "".join(vendor_group(group) for group in groups)
    group_controls = (
        '<div class="group-controls" aria-label="市场层展开控制">'
        '<button type="button" data-group-action="open">展开全部市场层</button>'
        '<button type="button" data-group-action="close">收起全部市场层</button></div>'
        if collapsible_groups
        else ""
    )

    commercial_rows = "".join(
        '<tr><td><span class="price-type {price_type}">{label}</span><strong>{subject}</strong></td>'
        '<td>{billing}</td><td class="price-signal">{signal}</td><td>{cost}</td>'
        '<td>{limitations}{sources}</td></tr>'.format(
            price_type=esc(item["price_type"]),
            label=esc(PRICE_TYPE_LABELS[item["price_type"]]),
            subject=esc(item["subject"]),
            signal=esc(item["price_signal"]),
            billing=esc(item["billing_model"]),
            cost=esc(item["cost_context"]),
            limitations=esc(item["limitations"]),
            sources=source_badges(item["source_ids"]),
        )
        for item in data["commercial_signals"]
    ) or '<tr><td colspan="5" class="empty-cell">本次未获得可核验的价格或计费信号。</td></tr>'

    constraint_cards = "".join(
        '<article class="constraint-card"><span>{index:02d}</span><p>{text}</p></article>'.format(
            index=index, text=esc(item)
        )
        for index, item in enumerate(scope["constraints"], start=1)
    ) or '<p class="empty-state">当前材料未列出影响市场边界的采购约束。</p>'

    risk_rows = "".join(
        '<article class="risk-item"><div class="risk-marker">{index:02d}</div><div><h3>{topic}</h3>'
        '<p><b>观察信号</b><br>{signal}</p><dl><div><dt>与本需求的关系</dt><dd>{relevance}</dd></div>'
        '<div><dt>仍需获得的信息</dt><dd>{needed}</dd></div></dl>{sources}</div></article>'.format(
            index=index,
            topic=esc(item["topic"]),
            signal=esc(item["observed_signal"]),
            relevance=esc(item["relevance"]),
            needed=esc(item["information_needed"]),
            sources=source_badges(item["source_ids"]),
        )
        for index, item in enumerate(data["risk_signals"], start=1)
    ) or '<p class="empty-state">本次未整理到有来源支撑的风险信号。</p>'

    trend_rows = "".join(
        '<article class="trend-card"><span>{horizon}</span><h3>{trend}</h3><p><b>观察变化</b><br>{change}</p>'
        '<div><b>可能相关</b><p>{relevance}</p></div>{sources}</article>'.format(
            horizon=esc(item["horizon"]),
            trend=esc(item["trend"]),
            change=esc(item["observed_change"]),
            relevance=esc(item["possible_relevance"]),
            sources=source_badges(item["source_ids"]),
        )
        for item in data["trends"]
    ) or '<p class="empty-state">本次未整理到有充分证据的相关趋势。</p>'

    constraint_section = (
        '<section id="constraints" class="section observed-section">'
        '<div class="section-title"><div><span>BOUNDARIES</span>'
        '<h2>采购约束与合规边界</h2></div>'
        f'<p>{len(scope["constraints"])} 项来自需求材料、地域、部署或数据边界，'
        '会影响可纳入的供给范围。</p></div>'
        f'<div class="constraint-grid">{constraint_cards}</div></section>'
        if scope["constraints"]
        else ""
    )
    trend_section = (
        '<section id="trends" class="section observed-section">'
        '<div class="section-title"><div><span>MARKET SIGNALS</span>'
        '<h2>技术与市场趋势</h2></div>'
        f'<p>{len(data["trends"])} 项与本品类未来 1–3 年产品边界、部署方式或成本结构相关的观察信号。'
        '</p></div>'
        f'<div class="trend-grid">{trend_rows}</div></section>'
        if data["trends"]
        else ""
    )

    longlist_items = sorted(
        ((group, item) for group in groups for item in group["vendors"]),
        key=lambda pair: (
            REGION_ORDER[pair[1]["enterprise_region"]],
            pair[0]["index"],
        ),
    )
    longlist_rows = "".join(
        '<tr class="longlist-row" data-market-group="{index}" data-enterprise-region="{region}" '
        'data-vendor-name="{vendor_attr}"><td><span class="table-tier">M{index}</span>{category}</td>'
        '<td><strong>{vendor}</strong></td><td><span class="region-status {region}">{region_label}</span></td>'
        '<td>{solution}</td><td>{form}</td><td><span class="evidence-status {evidence}">{evidence_label}</span></td>'
        '<td>{business}</td></tr>'.format(
            index=group["index"],
            category=esc(group["name"]),
            vendor=f'<a href="#vendor-{esc(slug(item["vendor"]))}">{esc(item["vendor"])}</a>',
            vendor_attr=esc(item["vendor"]),
            region=esc(item["enterprise_region"]),
            region_label=esc(REGION_LABELS[item["enterprise_region"]]),
            solution=esc(item["solution"]),
            form=esc(item["product_form"]),
            evidence=esc(item["evidence_status"]),
            evidence_label=esc(EVIDENCE_LABELS[item["evidence_status"]]),
            business=smart_business_markup(item["business_entry"]),
        )
        for group, item in longlist_items
    )

    source_rows = "".join(
        '<li id="source-{identifier}"><span>{identifier}</span><div><strong>{subject}</strong>'
        '<p>{title}</p><small>{date} · {claim}{locator}</small></div></li>'.format(
            identifier=esc(item["id"]),
            subject=esc(item["subject"]),
            title=link_markup(item["url"], item["title"]) if item["url"] else esc(item["title"]),
            date=esc(item["date"]),
            claim=esc(CLAIM_TYPE_LABELS[item["claim_type"]]),
            locator=f" · {esc(item['source_locator'])}" if item["source_locator"] else "",
        )
        for item in data["sources"]
    )

    mainland_count = sum(item["enterprise_region"] == "mainland_china" for item in vendors)
    overseas_count = sum(item["enterprise_region"] == "overseas" for item in vendors)
    unverified_region_count = sum(item["enterprise_region"] == "unverified" for item in vendors)
    region_meta_chips = (
        f'<span class="meta-chip">大陆企业 <strong>{mainland_count} 家</strong></span>'
        f'<span class="meta-chip">海外补充 <strong>{overseas_count} 家</strong></span>'
        + (
            f'<span class="meta-chip">主体待核验 <strong>{unverified_region_count} 家</strong></span>'
            if unverified_region_count
            else ""
        )
    )
    region_exception_note = (
        '<p class="region-exception"><b>地域覆盖例外</b>'
        f'{esc(scope["region_coverage_exception"])}</p>'
        if scope["region_coverage_exception"]
        else ""
    )

    display_title = data["title"]
    for prefix in ("市场情报与寻源报告｜", "采购寻源决策｜"):
        if display_title.startswith(prefix):
            display_title = "市场调研信息整合｜" + display_title[len(prefix) :]
            break

    longlist_open_attr = " open" if large_mode else ""
    longlist_summary = (
        f"{len(vendors)} 家 · 大陆企业全表置顶 · 大样本默认展开"
        if large_mode
        else f"{len(vendors)} 家 · 大陆企业全表置顶 · 默认折叠"
    )

    values = {
        "title": esc(display_title),
        "category": esc(data["category"]),
        "research_date": esc(data["research_date"]),
        "buying_object": esc(truncate_text(scope["buying_object"], 88)),
        "buying_object_full": esc(scope["buying_object"]),
        "geography": esc(truncate_text(scope["geography"], 34)),
        "geography_full": esc(scope["geography"]),
        "requirement_count": len(scope["requirements"]),
        "market_count": len(groups),
        "route_count": len(routes),
        "vendor_count": len(vendors),
        "mainland_count": mainland_count,
        "overseas_count": overseas_count,
        "unverified_region_count": unverified_region_count,
        "region_meta_chips": region_meta_chips,
        "public_price_count": public_prices,
        "source_count": len(data["sources"]),
        "constraint_count": len(scope["constraints"]),
        "trend_count": len(data["trends"]),
        "risk_count": len(data["risk_signals"]),
        "use_cases_html": list_markup(scope["use_cases"]),
        "requirements_html": list_markup(scope["requirements"]),
        "scan_scope_html": list_markup(scope["scan_scope"]),
        "constraints_html": list_markup(scope["constraints"]),
        "questions_html": list_markup(scope["open_questions"], "当前材料未列出待确认项"),
        "nav_links": "".join(nav_links),
        "market_map_rows": market_map_rows,
        "region_exception_note": region_exception_note,
        "route_rows": route_rows,
        "route_meta_chip": route_meta_chip,
        "route_block": route_block,
        "group_controls": group_controls,
        "vendor_sections": vendor_sections,
        "commercial_rows": commercial_rows,
        "constraint_cards": constraint_cards,
        "constraint_section": constraint_section,
        "risk_rows": risk_rows,
        "trend_rows": trend_rows,
        "trend_section": trend_section,
        "longlist_rows": longlist_rows,
        "longlist_open_attr": longlist_open_attr,
        "longlist_summary": esc(longlist_summary),
        "source_rows": source_rows,
    }
    rendered = Template(template_path.read_text(encoding="utf-8")).safe_substitute(values)
    unresolved = sorted(set(re.findall(r"\$[A-Za-z_][A-Za-z0-9_]*", rendered)))
    if unresolved:
        fail("html", "模板存在未替换变量：" + "、".join(unresolved))
    for pattern in FORBIDDEN_DECISION_PATTERNS:
        match = pattern.search(rendered)
        if match:
            fail("html", f"渲染结果仍含采购决策表述“{match.group(0)}”")
    return rendered


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验市场调研 JSON 并生成中立信息整合 HTML。")
    parser.add_argument("input", type=Path, help="UTF-8 JSON 数据文件")
    parser.add_argument("--output", "-o", type=Path, required=True, help="输出 HTML 路径")
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
