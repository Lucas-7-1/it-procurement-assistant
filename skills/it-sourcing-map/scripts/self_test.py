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
from render_sourcing_report import (
    ValidationError,
    render_html,
    truncate_text,
    validate_and_normalize,
)


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


def legacy_neutralize_payload() -> dict:
    """Pre-v3 payload that mixes legitimate wording with legacy recommendation phrases."""
    return {
        "schema_version": "2.0",
        "title": "旧版回归样例｜测试品类",
        "category": "测试品类",
        "research_date": "2026-08-12",
        "scope": {
            "buying_object": "旧版结构回归对象",
            "use_cases": ["测试场景"],
            "p0_requirements": ["测试需求"],
            "geography": "中国大陆",
            "scan_scope": ["公开产品页"],
            "procurement_constraints": [
                "值得注意的是，需要求供应商确认交付边界。",
                "适合大型企业的部署模式，覆盖范围待核验。",
            ],
            "pending_items": [],
        },
        "market_landscape": [
            {
                "segment": "平台型供给",
                "what_it_solves": "覆盖通用流程",
                "product_forms": ["软件平台"],
                "best_for": "边界待核验",
                "tradeoffs": "模块边界可能不同",
                "source_ids": ["S1"],
            }
        ],
        "technology_routes": [],
        "long_list": [
            {
                "category": "国内平台厂商",
                "vendor": "旧版示例厂商",
                "solution": "旧版示例产品",
                "product_form": "软件平台",
                "requirement_match": "值得注意的是，公开资料只覆盖部分需求。",
                "business_entry": "官网表单",
                "source_ids": ["S1"],
            }
        ],
        "priority_vendors": [],
        "commercial_benchmark": {
            "pricing_models": [
                {
                    "route_or_segment": "平台订阅",
                    "billing_model": "按年订阅",
                    "price_type": "quote_required",
                    "price_signal": "需询价",
                    "source_ids": ["S1"],
                }
            ]
        },
        "key_risks": [
            {
                "risk": "能力边界",
                "impact": "公开资料只覆盖部分功能。",
                "validation": "逐项能力证明与样本结果。",
                "source_ids": ["S1"],
            }
        ],
        "trends": [],
        "sources": [
            {
                "id": "S1",
                "subject": "旧版示例厂商",
                "title": "产品页",
                "date": "2026-08-12",
                "claim_type": "vendor_claim",
                "url": "https://example.com/legacy",
                "source_locator": "",
            }
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

    # neutralize 误伤回归：legacy 中立化只应命中孤立短语，不得破坏“值得注意”“需要求供应商”等正常行文
    legacy_html = render_html(validate_and_normalize(legacy_neutralize_payload()))
    assert "值得注意的是" in legacy_html, "neutralize 误伤：‘值得注意’被错误改写"
    assert "需要求供应商确认交付边界" in legacy_html, "neutralize 误伤：‘需要求供应商’被错误改写"
    assert "常见于大型企业的部署模式" in legacy_html, "neutralize 缺失：‘适合大型企业’应被中立化为‘常见于大型企业’"
    assert "适合大型企业" not in legacy_html

    # golden 大样本回归：渲染到临时目录，QA 通过且计数与基线一致（26/26/5）
    golden_large = Path(__file__).resolve().parents[3] / "tests" / "golden" / "sample-large.json"
    assert golden_large.exists(), f"缺少 golden 基线：{golden_large}"
    with tempfile.TemporaryDirectory(prefix="it-sourcing-map-golden-") as temp_dir:
        golden_html_path = Path(temp_dir) / "golden-large.html"
        golden_data = json.loads(golden_large.read_text(encoding="utf-8"))
        golden_html_path.write_text(
            render_html(validate_and_normalize(golden_data)), encoding="utf-8"
        )
        failures, metrics = run_checks(golden_html_path, golden_large)
        assert not failures, "；".join(failures)
        assert metrics["vendor_cards"] == 26, metrics
        assert metrics["longlist_rows"] == 26, metrics
        assert metrics["market_layers"] == 5, metrics

    # 转义攻击样本：<script>、" onmouseover= 文本与 emoji 均被转义，QA 通过
    attack = copy.deepcopy(payload)
    attack["vendors"][0]["solution"] = "示例产品 <script>alert(1)</script>"
    attack["vendors"][0]["public_coverage"] = '公开资料 " onmouseover=alert(1) 覆盖测试能力 🚀。'
    attack_html = render_html(validate_and_normalize(attack))
    assert "<script>alert(1)</script>" not in attack_html
    assert html.escape("<script>alert(1)</script>", quote=True) in attack_html
    assert '" onmouseover=' not in attack_html
    assert "&quot; onmouseover=alert(1)" in attack_html
    assert 'href="javascript:' not in attack_html
    assert "🚀" in attack_html
    with tempfile.TemporaryDirectory(prefix="it-sourcing-map-attack-") as temp_dir:
        data_path = Path(temp_dir) / "attack.json"
        html_path = Path(temp_dir) / "attack.html"
        data_path.write_text(json.dumps(attack, ensure_ascii=False), encoding="utf-8")
        html_path.write_text(attack_html, encoding="utf-8")
        failures, _ = run_checks(html_path, data_path)
        assert not failures, "；".join(failures)
    # business_entry 含危险协议（含无 // 的裸写法）在校验阶段即被拒绝
    invalid = copy.deepcopy(payload)
    invalid["vendors"][0]["business_entry"] = "javascript:alert(1)"
    expect_invalid(invalid, "business_entry 危险协议")
    # business_entry 含 ftp:// 等非危险协议：校验放行，仅作转义后的纯文本展示、不生成链接
    ftp_entry = copy.deepcopy(payload)
    ftp_entry["vendors"][0]["business_entry"] = "ftp://example.com/contact"
    ftp_html = render_html(validate_and_normalize(ftp_entry))
    assert html.escape("ftp://example.com/contact", quote=True) in ftp_html
    assert '<a href="ftp' not in ftp_html
    # business_entry 含 mailto:：校验通过、渲染为纯文本、QA 通过
    mailto_entry = copy.deepcopy(payload)
    mailto_entry["vendors"][0]["business_entry"] = "mailto:sales@example.com"
    mailto_html = render_html(validate_and_normalize(mailto_entry))
    assert "mailto:sales@example.com" in mailto_html
    assert '<a href="mailto' not in mailto_html
    with tempfile.TemporaryDirectory(prefix="it-sourcing-map-mailto-") as temp_dir:
        data_path = Path(temp_dir) / "mailto.json"
        html_path = Path(temp_dir) / "mailto.html"
        data_path.write_text(json.dumps(mailto_entry, ensure_ascii=False), encoding="utf-8")
        html_path.write_text(mailto_html, encoding="utf-8")
        failures, _ = run_checks(html_path, data_path)
        assert not failures, "；".join(failures)

    # 边界：0 家厂商与 sources 为空均必须被拒绝
    invalid = copy.deepcopy(payload)
    invalid["vendors"] = []
    expect_invalid(invalid, "0 家厂商")
    invalid = copy.deepcopy(payload)
    invalid["sources"] = []
    expect_invalid(invalid, "sources 为空")

    # 50 家大样本渲染 + QA 通过
    fifty = copy.deepcopy(payload)
    fifty["market_structure"] = []
    fifty["vendors"] = []
    for group_index in range(1, 6):
        name = f"规模供给 {group_index}"
        fifty["market_structure"].append(
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
        for vendor_index in range(1, 11):
            vendor = copy.deepcopy(payload["vendors"][0])
            vendor["category"] = name
            vendor["vendor"] = f"规模厂商 {group_index}-{vendor_index}"
            fifty["vendors"].append(vendor)
    with tempfile.TemporaryDirectory(prefix="it-sourcing-map-fifty-") as temp_dir:
        data_path = Path(temp_dir) / "fifty.json"
        html_path = Path(temp_dir) / "fifty.html"
        data_path.write_text(json.dumps(fifty, ensure_ascii=False), encoding="utf-8")
        html_path.write_text(render_html(validate_and_normalize(fifty)), encoding="utf-8")
        failures, metrics = run_checks(html_path, data_path)
        assert not failures, "；".join(failures)
        assert metrics["vendor_cards"] == 50 and metrics["longlist_rows"] == 50, metrics

    # 价格信号含 $100/user/月与 $USD 不再触发未替换变量误报中断
    price = copy.deepcopy(payload)
    price["commercial_signals"][0].update(
        {
            "price_type": "industry_estimate",
            "price_signal": "行业估算：$100/user/月（按 $USD 口径）",
        }
    )
    price_html = render_html(validate_and_normalize(price))
    assert "$100/user/月" in price_html and "$USD" in price_html

    # 厂商名含大括号渲染成功（str.format 解析风险已消除）
    brace = copy.deepcopy(payload)
    brace["vendors"][0]["vendor"] = "示例厂商 {test}"
    assert "{test}" in render_html(validate_and_normalize(brace))

    # 全部 commercial_signals 为 quote_required 渲染成功且 QA 通过
    quotes = copy.deepcopy(payload)
    quotes["commercial_signals"].append(
        {
            "subject": "实施服务",
            "billing_model": "按项目",
            "price_type": "quote_required",
            "price_signal": "需询价",
            "cost_context": "范围界定后另行确认",
            "limitations": "公开资料未披露服务报价",
            "source_ids": ["S2"],
        }
    )
    assert all(item["price_type"] == "quote_required" for item in quotes["commercial_signals"])
    with tempfile.TemporaryDirectory(prefix="it-sourcing-map-quotes-") as temp_dir:
        data_path = Path(temp_dir) / "quotes.json"
        html_path = Path(temp_dir) / "quotes.html"
        data_path.write_text(json.dumps(quotes, ensure_ascii=False), encoding="utf-8")
        html_path.write_text(render_html(validate_and_normalize(quotes)), encoding="utf-8")
        failures, _ = run_checks(html_path, data_path)
        assert not failures, "；".join(failures)

    # 200 字符超长厂商名：truncate_text 正常截断，渲染与 QA 通过
    long_name = "超长厂商" + "名" * 196
    assert len(long_name) == 200
    truncated = truncate_text(long_name, 24)
    assert truncated.endswith("…") and len(truncated) <= 24
    long_vendor = copy.deepcopy(payload)
    long_vendor["vendors"][0]["vendor"] = long_name
    with tempfile.TemporaryDirectory(prefix="it-sourcing-map-longname-") as temp_dir:
        data_path = Path(temp_dir) / "longname.json"
        html_path = Path(temp_dir) / "longname.html"
        data_path.write_text(json.dumps(long_vendor, ensure_ascii=False), encoding="utf-8")
        html_path.write_text(
            render_html(validate_and_normalize(long_vendor)), encoding="utf-8"
        )
        failures, _ = run_checks(html_path, data_path)
        assert not failures, "；".join(failures)

    if args.legacy_sample:
        legacy = json.loads(args.legacy_sample.read_text(encoding="utf-8"))
        legacy_html = render_html(validate_and_normalize(legacy))
        assert "priority_vendors" not in legacy_html
        assert "next_actions" not in legacy_html

    print(
        "自检通过：大陆企业强约束、展示顺序、中立性、完整性与 25+ 厂商规模策略均正常；"
        "新增 T6 加固回归 10 组断言（neutralize 误伤、golden 大样本、转义攻击、危险协议拦截与 ftp/mailto 纯文本放行、"
        "0/50 家边界、$ 变量误报、大括号、全需询价、空 sources、超长厂商名）均通过。"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
