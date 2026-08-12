# 五看与供应商地图数据规范

仅在完成实时公开研究后构造数据。事实性结论必须能回链到 `sources`；不能取得公开证据时，把候选放入 `pending_verification_vendors`，不放入 `vendors`，也不填坐标。

## 研究与五看

先按需求边界限定品类、地域、时间、部署方式、预算、现有系统、数据与合规约束。再分别收集：

- **看行业**：政策、标准、技术范式与行业驱动。
- **看市场**：细分市场、部署 / 采购模式与可观察的供给信号。
- **看客户**：同类客户的公开场景、采用路径与可复制条件。
- **看竞争**：产品厂商、方案商、细分位置、技术路径与替代关系。
- **看自己**：需求方现有系统、团队能力、数据 / 合规约束、迁移和运维承受度。

“看自己”可引用需求文档；其余外部事实用公开来源。厂商官网、公开财报、政府公示、标准组织、公开招投标、公开客户案例、分析师 / 媒体报告都可用，但要把厂商自述标成 `vendor_claim`，不能当作独立事实。

## JSON 结构

传给脚本的是一个 UTF-8 JSON 对象。下面是字段结构；示例中的占位主体和 URL 必须替换成实际研究结果，示例本身不是证据。

```json
{
  "title": "供应商地图｜<品类>",
  "category": "<品类>",
  "research_date": "YYYY-MM-DD",
  "demand_boundary": {
    "business_goal": "<要解决的业务问题>",
    "in_scope": ["<范围内>"],
    "out_of_scope": ["<范围外>"],
    "timeline": "<时间约束或待确认>",
    "budget": "<预算约束或待确认>",
    "system_data_compliance_constraints": ["<系统/数据/合规约束>"],
    "success_criteria": ["<成功标准或待确认>"]
  },
  "map_axes": {
    "x_label": "横轴：<分析维度>",
    "y_label": "纵轴：<分析维度>"
  },
  "five_looks": {
    "industry": {"summary": "<看行业结论或待验证>", "source_ids": ["S-001"]},
    "market": {"summary": "<看市场结论或待验证>", "source_ids": ["S-001"]},
    "customer": {"summary": "<同类客户路径或待验证>", "source_ids": ["S-001"]},
    "competition": {"summary": "<看竞争结论或待验证>", "source_ids": ["S-001"]},
    "self": {"summary": "<看自己匹配或待确认>", "source_ids": []}
  },
  "technical_paths": [
    {"name": "<技术路径>", "summary": "<适用边界与取舍>", "source_ids": ["S-001"]}
  ],
  "peer_paths": [
    {"name": "<同类需求路径>", "summary": "<公开可验证的客户路径与前提>", "source_ids": ["S-001"]}
  ],
  "compliance_risks": [
    {"name": "<风险主题>", "heat": "high", "summary": "<适用的风险与待核验事项>", "source_ids": ["S-001"]}
  ],
  "vendors": [
    {
      "name": "<已验证供应商>",
      "segment": "<所在细分>",
      "status": "shortlist",
      "x": 60,
      "y": 70,
      "summary": "<基于证据的定位>",
      "technology_path": "<技术路径>",
      "fit_note": "<与需求边界的匹配 / 待验证>",
      "compliance_note": "<合规待验证项>",
      "source_ids": ["S-001"],
      "coordinate_rationale": "<为什么基于公开证据放在该坐标；这是分析定位，不是市场排名>",
      "coordinate_source_ids": ["S-001"]
    }
  ],
  "pending_verification_vendors": [
    {
      "name": "<无公开证据候选>",
      "reason": "<为何尚不能验证>",
      "next_validation": "<下一步核验动作>"
    }
  ],
  "sources": [
    {
      "id": "S-001",
      "subject": "<来源主体>",
      "title": "<来源标题>",
      "date": "YYYY-MM-DD",
      "claim_type": "fact",
      "url": "https://example.com/replace-with-real-source"
    }
  ],
  "pending_items": ["<仍待验证的事实或问题>"]
}
```

## 强制证据规则

- 每个 `sources` 条目都必须有唯一 `id`、非空 `subject`、非空 `title`、`date`、合法 `claim_type`，以及非空 `url` 或 `source_locator`。
- `date` 只允许真实的 `YYYY-MM-DD` 或 `日期未公开`；`claim_type` 只允许 `fact`、`vendor_claim`、`inference`、`reference`。
- 每个 `vendors` 条目必须有至少一个有效 `source_id`（用 `source_ids` 数组承载）、非空 `coordinate_rationale`、至少一个有效 `coordinate_source_id`（用 `coordinate_source_ids` 数组承载）。所有 ID 都必须存在于 `sources`。
- `vendors` 非空时，`sources` 不得为空。所有外部事实性条目的 `source_ids` 都必须引用存在的来源；无法证明的内容写为“待验证”，不要伪造引用。
- `x` 和 `y` 是 0–100 的**分析定位**。不得把坐标或气泡大小解释为市场份额、营收、排名或能力评分；`coordinate_rationale` 要解释定位依据，`coordinate_source_ids` 要指向依据来源。
- 气泡大小由脚本按去重后的 `source_ids` 数量计算，只表示公开证据覆盖度。
- `status` 只用 `shortlist`（入围）、`watch`（观察）、`exclude`（排除）。这些是当前采购判断，不等同于好坏或市场份额。
- `pending_verification_vendors` 只能放没有足够公开来源的候选；不得带 `x`、`y`、`coordinate_rationale`、`coordinate_source_ids`、`source_id` 或 `source_ids`。这些候选会被列为待验证项，不会画进地图。

## 最小运行方式

```bash
python scripts/render_supplier_map.py supplier-map-data.json --output "供应商地图-<品类>-<YYYYMMDD>.html"
```

脚本会在写出 HTML 前校验来源、日期、引用和坐标规则。修正校验错误后再运行；不要为通过校验而编造来源或坐标依据。
