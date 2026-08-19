#!/usr/bin/env python3
"""Self-contained regression tests for the neutral sourcing renderer."""

from __future__ import annotations

import argparse
import copy
import html
import json
import tempfile
from pathlib import Path

from qa_sourcing_report import run_checks
from render_contact_list import render_contact_list
from render_sourcing_report import ValidationError, render_html, validate_and_normalize


def base_payload() -> dict:
    return {
        "schema_version": "3.0",
        "title": "结构回归样例｜测试品类",
        "category": "测试品类",
        "research_date": "2026-08-12",
        "scope": {
            "buying_object": "用于验证中立市场调研结构的测试对象",
            "use_cases": ["测试场景"],
            "requirements": ["测试需求"],
            "geography": "中国大陆",
            "scan_scope": ["公开产品页与文档"],
            "constraints": [],
            "open_questions": ["实际交付边界待核验"],
            "region_coverage_exception": "",
        },
        "market_structure": [
            {
                "kind": "供给类型",
                "name": "平台型供给",
                "solves": "覆盖通用流程",
                "product_forms": ["软件平台"],
                "boundary": "专项能力需单独核验",
                "tradeoffs": "模块边界与报价口径可能不同",
                "source_ids": ["S1"],
            }
        ],
        "vendors": [
            {
                "category": "平台型供给",
                "vendor": "示例厂商 <A>",
                "solution": "示例产品 & 服务",
                "product_form": "软件平台",
                "public_coverage": "公开资料覆盖测试能力。",
                "capabilities": ["能力一", "能力二", "能力三", "能力四", "能力五"],
                "deployment_integration": "支持 API 与本地部署。",
                "commercial_model": "企业许可需询价。",
                "information_gaps": ["缺口一", "缺口二"],
                "evidence_status": "documented",
                "enterprise_region": "mainland_china",
                "region_basis": "官方产品页主体信息显示为中国大陆企业，正式准入仍核验签约与履约主体。",
                "region_source_ids": ["S1"],
                "source_ids": ["S1"],
            }
        ],
        "commercial_signals": [
            {
                "subject": "企业许可",
                "billing_model": "按年订阅",
                "price_type": "quote_required",
                "price_signal": "需询价",
                "cost_context": "部署与服务另行确认",
                "limitations": "公开资料未披露企业报价",
                "source_ids": ["S2"],
            }
        ],
        "risk_signals": [
            {
                "topic": "能力边界",
                "observed_signal": "公开资料只覆盖部分功能。",
                "relevance": "可能影响需求覆盖口径。",
                "information_needed": "逐项能力证明与样本结果。",
                "source_ids": ["S1"],
            }
        ],
        "trends": [],
        "sources": [
            {
                "id": "S1",
                "subject": "示例厂商",
                "title": "产品页",
                "date": "2026-08-12",
                "claim_type": "vendor_claim",
                "url": "https://example.com/product?a=1&b=2",
                "source_locator": "",
            },
            {
                "id": "S2",
                "subject": "示例厂商",
                "title": "商务页",
                "date": "2026-08-12",
                "claim_type": "vendor_claim",
                "url": "https://example.com/contact",
                "source_locator": "",
            },
        ],
    }


def expect_invalid(payload: dict, label: str) -> None:
    try:
        validate_and_normalize(payload)
    except ValidationError:
        return
    raise AssertionError(f"负例未被拒绝：{label}")


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 Skill 渲染器自检。")
    parser.add_argument("--legacy-sample", type=Path, help="可选：额外回归一份旧版 JSON")
    args = parser.parse_args()

    payload = base_payload()
    normalized = validate_and_normalize(payload)
    rendered = render_html(normalized)
    assert "class=\"route-block\"" not in rendered
    assert 'id="trends"' not in rendered
    assert 'id="constraints"' not in rendered
    assert 'class="vendor-grid count-1"' in rendered
    assert "longlist-disclosure\" open" not in rendered
    assert html.escape("能力五", quote=True) in rendered
    assert html.escape("缺口二", quote=True) in rendered
    assert "本次公开扫描未见商务入口" in rendered
    assert "&lt;A&gt;" in rendered and "产品 &amp; 服务" in rendered
    assert "大陆企业" in rendered
    assert "官方产品页主体信息显示为中国大陆企业" in rendered
    assert rendered.find("示例厂商 &lt;A&gt;") < rendered.find('id="market-group-1"')

    contact_payload = {
        "vendors": [
            {
                "vendor": "海外联系厂商",
                "enterprise_region": "overseas",
                "contacts": [
                    {
                        "type": "email",
                        "value": "support@example.com",
                        "label": "技术支持",
                        "scope": "全球",
                        "source_ids": ["S2"],
                    }
                ],
                "contact_note": "",
                "contact_source_ids": ["S2"],
            },
            {
                "vendor": "大陆联系厂商",
                "enterprise_region": "mainland_china",
                "contacts": [
                    {
                        "type": "phone",
                        "value": "400-000-1234",
                        "label": "全国服务热线",
                        "scope": "中国大陆",
                        "source_ids": ["S2"],
                    }
                ],
                "contact_note": "",
                "contact_source_ids": ["S2"],
            },
        ],
        "sources": [
            {"id": "S2", "url": "https://example.com/contact"}
        ],
    }
    sorted_contact_text = render_contact_list(contact_payload)
    assert sorted_contact_text.find("大陆联系厂商") < sorted_contact_text.find("海外联系厂商")

    invalid = copy.deepcopy(payload)
    invalid["decision"] = "进入 RFI"
    expect_invalid(invalid, "决策字段")
    invalid = copy.deepcopy(payload)
    invalid["scope"]["open_questions"] = ["优先推进某厂商"]
    expect_invalid(invalid, "决策措辞")
    invalid = copy.deepcopy(payload)
    invalid["vendors"].append(copy.deepcopy(invalid["vendors"][0]))
    expect_invalid(invalid, "重复厂商")
    invalid = copy.deepcopy(payload)
    invalid["vendors"][0]["category"] = "不存在的分类"
    expect_invalid(invalid, "孤立分类")
    invalid = copy.deepcopy(payload)
    invalid["market_structure"].insert(
        0,
        {
            "kind": "技术路线",
            "name": "组合路线",
            "solves": "组合能力",
            "product_forms": ["组合"],
            "boundary": "需集成",
            "tradeoffs": "接口边界待核验",
            "source_ids": ["S1"],
        },
    )
    expect_invalid(invalid, "技术路线先于供给类型")
    invalid = copy.deepcopy(payload)
    invalid["sources"][0]["url"] = "example.com/no-scheme"
    expect_invalid(invalid, "无效 URL")
    invalid = copy.deepcopy(payload)
    invalid["commercial_signals"][0].update(
        {"price_type": "public_price", "price_signal": "$100"}
    )
    expect_invalid(invalid, "公开价格缺单位")
    invalid = copy.deepcopy(payload)
    invalid["vendors"][0]["evidence_status"] = "verified"
    expect_invalid(invalid, "非法枚举")
    invalid = copy.deepcopy(payload)
    invalid["vendors"][0]["enterprise_region"] = "domestic"
    expect_invalid(invalid, "非法企业地域")
    invalid = copy.deepcopy(payload)
    invalid["vendors"][0]["region_source_ids"] = []
    expect_invalid(invalid, "企业地域缺少来源")

    ratio = copy.deepcopy(payload)
    overseas = copy.deepcopy(payload["vendors"][0])
    overseas["vendor"] = "海外示例厂商"
    overseas["enterprise_region"] = "overseas"
    overseas["region_basis"] = "官方资料显示为海外企业，中国区履约主体待核验。"
    ratio["vendors"].append(overseas)
    expect_invalid(ratio, "大陆企业未占严格多数")
    ratio["scope"]["region_coverage_exception"] = "该测试品类仅识别到同量大陆与海外供给，保留例外以验证诚实披露。"
    validate_and_normalize(ratio)

    mixed = copy.deepcopy(payload)
    mainland_two = copy.deepcopy(payload["vendors"][0])
    mainland_two["vendor"] = "大陆示例厂商 B"
    overseas = copy.deepcopy(overseas)
    mixed["vendors"] = [overseas, mainland_two, mixed["vendors"][0]]
    mixed_html = render_html(validate_and_normalize(mixed))
    longlist_html = mixed_html[mixed_html.find('id="longlist"') :]
    assert longlist_html.find('data-vendor-name="大陆示例厂商 B"') < longlist_html.find(
        'data-vendor-name="海外示例厂商"'
    )
    assert mixed_html.find('data-enterprise-region="mainland_china"') < mixed_html.find(
        'data-enterprise-region="overseas"'
    )

    large = copy.deepcopy(payload)
    large["market_structure"] = []
    large["vendors"] = []
    for group_index in range(1, 7):
        name = f"供给类型 {group_index}"
        large["market_structure"].append(
            {
                "kind": "供给类型",
                "name": name,
                "solves": f"解决问题 {group_index}",
                "product_forms": ["平台"],
                "boundary": "边界待核验",
                "tradeoffs": "存在集成成本",
                "source_ids": ["S1"],
            }
        )
        for vendor_index in range(1, 5 if group_index < 2 else 6):
            vendor = copy.deepcopy(payload["vendors"][0])
            vendor["category"] = name
            vendor["vendor"] = f"厂商 {group_index}-{vendor_index}"
            large["vendors"].append(vendor)
    large_html = render_html(validate_and_normalize(large))
    assert large_html.count('class="market-layer"') == 6
    assert large_html.count('class="vendor-card"') == len(large["vendors"])
    assert large_html.count('class="table-tier"') == len(large["vendors"])
    assert 'class="longlist-disclosure" open' in large_html

    with tempfile.TemporaryDirectory(prefix="it-sourcing-map-test-") as temp_dir:
        data_path = Path(temp_dir) / "input.json"
        html_path = Path(temp_dir) / "output.html"
        data_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        html_path.write_text(rendered, encoding="utf-8")
        failures, _ = run_checks(html_path, data_path)
        assert not failures, "；".join(failures)

    if args.legacy_sample:
        legacy = json.loads(args.legacy_sample.read_text(encoding="utf-8"))
        legacy_html = render_html(validate_and_normalize(legacy))
        assert "priority_vendors" not in legacy_html
        assert "next_actions" not in legacy_html

    print("自检通过：大陆企业强约束、展示顺序、中立性、完整性与 25+ 厂商规模策略均正常。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
