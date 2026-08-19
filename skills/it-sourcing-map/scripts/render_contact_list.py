#!/usr/bin/env python3
"""Render a source-backed supplier contact list as plain UTF-8 text."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def require_text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"缺少必填字段：{field}")
    return text


def source_url(source: dict[str, Any]) -> str:
    return require_text(
        source.get("source_locator") or source.get("url"),
        f"sources[{source.get('id', '?')}].source_locator",
    )


def render_contact_list(data: dict[str, Any]) -> str:
    vendors = data.get("vendors")
    sources = data.get("sources")
    if not isinstance(vendors, list) or not vendors:
        raise ValueError("vendors 必须是非空数组")
    if not isinstance(sources, list) or not sources:
        raise ValueError("sources 必须是非空数组")

    source_map: dict[str, dict[str, Any]] = {}
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"sources[{index}] 必须是对象")
        source_id = require_text(source.get("id"), f"sources[{index}].id")
        if source_id in source_map:
            raise ValueError(f"来源 ID 重复：{source_id}")
        source_url(source)
        source_map[source_id] = source

    region_rank = {"mainland_china": 0, "overseas": 1}
    ordered_vendors = sorted(
        enumerate(vendors),
        key=lambda item: (
            region_rank.get(str(item[1].get("enterprise_region") or "").strip(), 2)
            if isinstance(item[1], dict)
            else 2,
            item[0],
        ),
    )

    blocks: list[str] = []
    for index, vendor in ordered_vendors:
        if not isinstance(vendor, dict):
            raise ValueError(f"vendors[{index}] 必须是对象")
        name = require_text(vendor.get("vendor"), f"vendors[{index}].vendor")
        region = require_text(
            vendor.get("enterprise_region"), f"vendors[{index}].enterprise_region"
        )
        if region not in {"mainland_china", "overseas"}:
            raise ValueError(f"{name} 的 enterprise_region 不支持：{region}")

        contacts = vendor.get("contacts", [])
        note = str(vendor.get("contact_note") or "").strip()
        contact_source_ids = vendor.get("contact_source_ids", [])
        if not isinstance(contacts, list):
            raise ValueError(f"{name}.contacts 必须是数组")
        if not isinstance(contact_source_ids, list) or not contact_source_ids:
            raise ValueError(f"{name} 缺少 contact_source_ids")
        for source_id in contact_source_ids:
            if source_id not in source_map:
                raise ValueError(f"{name} 引用了不存在的来源：{source_id}")
        if not contacts and not note:
            raise ValueError(f"{name} 必须提供联系方式或未公开说明")

        lines = [name, f"地区：{'中国大陆' if region == 'mainland_china' else '海外'}"]
        seen: set[tuple[str, str]] = set()
        for contact_index, contact in enumerate(contacts):
            if not isinstance(contact, dict):
                raise ValueError(f"{name}.contacts[{contact_index}] 必须是对象")
            contact_type = require_text(
                contact.get("type"), f"{name}.contacts[{contact_index}].type"
            )
            expected_type = "phone" if region == "mainland_china" else "email"
            if contact_type != expected_type:
                raise ValueError(
                    f"{name} 地域为 {region}，联系方式类型必须是 {expected_type}"
                )
            value = require_text(
                contact.get("value"), f"{name}.contacts[{contact_index}].value"
            )
            if contact_type == "email" and not EMAIL_RE.fullmatch(value):
                raise ValueError(f"{name} 邮箱格式无效：{value}")
            dedupe_key = (contact_type, value.casefold())
            if dedupe_key in seen:
                raise ValueError(f"{name} 联系方式重复：{value}")
            seen.add(dedupe_key)

            label = require_text(
                contact.get("label"), f"{name}.contacts[{contact_index}].label"
            )
            scope = require_text(
                contact.get("scope"), f"{name}.contacts[{contact_index}].scope"
            )
            source_ids = contact.get("source_ids")
            if not isinstance(source_ids, list) or not source_ids:
                raise ValueError(f"{name} 的 {value} 缺少来源")
            urls: list[str] = []
            for source_id in source_ids:
                if source_id not in source_map:
                    raise ValueError(f"{name} 的 {value} 引用了不存在的来源：{source_id}")
                url = source_url(source_map[source_id])
                if url not in urls:
                    urls.append(url)

            lines.extend(
                [
                    f"{'电话' if contact_type == 'phone' else '邮箱'}：{value}",
                    f"用途：{label}",
                    f"适用范围：{scope}",
                ]
            )
            lines.extend(f"来源：{url}" for url in urls)

        if note:
            lines.append(f"说明：{note}")
            used_urls = {
                source_url(source_map[source_id])
                for contact in contacts
                for source_id in contact.get("source_ids", [])
            }
            note_urls: list[str] = []
            for source_id in contact_source_ids:
                url = source_url(source_map[source_id])
                if url not in used_urls and url not in note_urls:
                    note_urls.append(url)
            lines.extend(f"说明来源：{url}" for url in note_urls)

        blocks.append("\n".join(lines))

    return "\n\n".join(blocks) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="生成供应商联系方式纯文本清单")
    parser.add_argument("data", type=Path, help="市场调研 JSON 数据文件")
    parser.add_argument("--output", "-o", type=Path, required=True, help="输出 TXT 路径")
    parser.add_argument("--expected-vendors", type=int, help="预期供应商数量")
    args = parser.parse_args()

    with args.data.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    vendors = data.get("vendors")
    if args.expected_vendors is not None and len(vendors or []) != args.expected_vendors:
        raise ValueError(
            f"供应商数量不符：预期 {args.expected_vendors}，实际 {len(vendors or [])}"
        )

    text = render_contact_list(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8-sig", newline="\n")
    print(f"已生成：{args.output.resolve()}")
    print(f"供应商：{len(vendors)}")
    print(f"联系方式：{sum(len(vendor.get('contacts', [])) for vendor in vendors)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
