# 中立市场调研数据规范

仅在生成 HTML 时读取。本规范保存市场事实、供应商公开信息、价格信号、风险信号与证据，不保存推荐、排序、Short List 或采购动作。

## 核心约束

- `vendors` 是供应商信息的唯一事实源。
- 不创建任何决策、排序或推进字段，包括 `decision`、`shortlist`、`priority_vendors`、`next_actions`、`recommendation`、`fit`、`rank` 或 `priority`。
- 不使用适配度、优先级、风险分数或推荐状态。
- `evidence_status` 只描述公开信息可得性，不评价产品质量。
- `market_structure` 先列粗粒度“供给类型”，再列“技术路线”；`vendors.category` 必须与某个供给类型的 `name` 完全一致，使市场图、分组卡片和 Long List 使用同一分类坐标。
- v3 至少需要一个供给类型、一家厂商、一条商业信号和一条风险/信息缺口；没有公开价格时使用 `quote_required`，不要省略商业信息。
- 默认大陆采购场景中，大陆企业必须占全部候选池严格多数；海外企业作为专项能力、替代路线或市场参照补充。若市场客观供给不足，必须填写 `scope.region_coverage_exception`，不得虚构大陆厂商。
- 完整市场扫描默认 `vendors` 不少于 25 家，其中 `mainland_china` 不少于 15 家且占严格多数。不能以缺少公开证据的名称凑数；客观不足时在 `scope.region_coverage_exception` 同时披露扫描边界、实际数量和不足原因。只有标题与 `scope.scan_scope` 明确标为“节选 / 非完整市场扫描”时，才允许低于该门槛。

## JSON v3

```json
{
  "schema_version": "3.0",
  "title": "市场调研信息整合｜<品类>",
  "category": "<采购品类>",
  "research_date": "YYYY-MM-DD",
  "scope": {
    "buying_object": "<研究对象>",
    "use_cases": ["<使用场景>"],
    "requirements": ["<关键需求或验收指标>"],
    "geography": "<地域、部署和数据边界>",
    "scan_scope": ["<本次纳入的市场边界>"],
    "constraints": ["<会影响市场边界的约束>"],
    "open_questions": ["<当前材料尚未说明的信息>"],
    "region_coverage_exception": "<无法形成大陆企业严格多数时填写；正常满足时留空>"
  },
  "market_structure": [
    {
      "kind": "供给类型",
      "name": "<市场类型或技术路线>",
      "solves": "<解决什么问题>",
      "product_forms": ["<典型产品形态>"],
      "boundary": "<适用范围或能力边界>",
      "tradeoffs": "<主要取舍>",
      "source_ids": ["S-001"]
    }
  ],
  "vendors": [
    {
      "category": "<所属供给类型>",
      "vendor": "<供应商>",
      "solution": "<产品/方案>",
      "product_form": "<SaaS/API/SDK/私有化/服务等>",
      "public_coverage": "<公开资料明确覆盖的需求>",
      "capabilities": ["<公开资料明确提到的能力>"],
      "deployment_integration": "<公开的部署与集成信息；未知写本次公开扫描未见>",
      "commercial_model": "<公开的商业模式；未知写需询价或本次公开扫描未见>",
      "information_gaps": ["<仍需核验的具体信息>"],
      "evidence_status": "documented",
      "enterprise_region": "mainland_china",
      "region_basis": "<产品能力主体或主要履约主体的地域判断依据>",
      "region_source_ids": ["S-001"],
      "business_entry": "https://example.com/contact",
      "contacts": [
        {
          "type": "phone",
          "value": "400-000-0000",
          "label": "全国服务热线",
          "scope": "中国大陆",
          "source_ids": ["S-001"]
        }
      ],
      "contact_note": "",
      "contact_source_ids": ["S-001"],
      "source_ids": ["S-001"]
    }
  ],
  "commercial_signals": [
    {
      "subject": "<产品、路线或市场类型>",
      "billing_model": "<计费单位或模式>",
      "price_type": "public_price",
      "price_signal": "<币种、单位、版本/层级、区域与条件；无公开价写需询价>",
      "cost_context": "<一次性/持续性成本和 TCO 驱动>",
      "limitations": "<该价格信号不能说明什么>",
      "source_ids": ["S-001"]
    }
  ],
  "risk_signals": [
    {
      "topic": "<风险或不确定性主题>",
      "observed_signal": "<公开资料或需求材料中观察到什么>",
      "relevance": "<为何与当前需求有关>",
      "information_needed": "<还需要获得什么资料或证明>",
      "source_ids": ["S-001"]
    }
  ],
  "trends": [
    {
      "trend": "<有可靠证据的市场/技术变化>",
      "horizon": "<时间范围>",
      "observed_change": "<发生了什么>",
      "possible_relevance": "<可能影响当前品类的方面，不写采购建议>",
      "source_ids": ["S-001"]
    }
  ],
  "sources": [
    {
      "id": "S-001",
      "subject": "<来源主体>",
      "title": "<来源标题>",
      "date": "YYYY-MM-DD",
      "claim_type": "vendor_claim",
      "url": "https://example.com/replace-with-real-source"
    }
  ]
}
```

## 字段规则

### 市场分层与供应商分类

- `market_structure.kind` 使用“供给类型”或“技术路线”；所有供给类型排在技术路线之前；
- 供给类型应是采购能看懂的粗粒度市场层，通常 4–8 类，不要把“国内/国际”“SaaS/私有化”“原厂/代理”等每个标签拆成独立市场层；
- `vendors.category` 必须逐字匹配一个供给类型名称；同一供应商只归入一个主要市场层；
- 产品形态、地域、部署方式和生态身份放在对应字段或能力标签中，不另起一套分类；
- 市场层的数组顺序就是 HTML 的浏览顺序，但不代表推荐、排名或成熟度。
- HTML 中供应商卡片承载完整公开信息与缺口；末尾 Long List 仅从同一 `vendors` 数据派生分类索引，不重复整段描述。
- 市场结构名称和供应商名称均不得重复；孤立分类、先列技术路线再列供给类型等结构错误必须拒绝，不能静默新增分组。

### 企业地域与大陆优先约束

- `enterprise_region` 只允许 `mainland_china`、`overseas`、`unverified`；
- 按产品能力主体或主要履约主体的注册地判断，不以品牌中文名、中文官网、代理商或销售入口判断；
- `mainland_china` 与 `overseas` 必须填写 `region_basis` 和至少一个 `region_source_ids`；优先引用工商/监管公示、正式主体说明或可核验签约资料；
- `unverified` 不得帮助满足大陆企业比例，且 `information_gaps` 必须明确能力主体、注册地、签约主体或履约主体中的待核验项；
- 无地域覆盖例外时，`mainland_china` 必须超过全部候选池的一半，并多于 `overseas`；
- 完整市场扫描中，`vendors` 总数不得少于 25，且 `mainland_china` 不得少于 15；小样本仅用于用户明确限定的节选、演示或结构回归，并必须显著标注非完整扫描；
- 同一市场层和供应商卡片按 `mainland_china → overseas → unverified` 排列；Long List 在全表范围先按该地域顺序连续分组，再在每个地域组内按市场层排列。该顺序只执行用户地域约束，不表示能力、价格或采购优先级；
- 若无法满足严格多数，填写 `scope.region_coverage_exception`，说明哪些供给层缺少可核验大陆企业及依据；HTML 必须显著展示，不能静默放宽。

### 公开企业联系方式

- 每家必须提供 `contacts`、`contact_note` 和 `contact_source_ids`。大陆企业至少列一条 `phone`，海外企业至少列一条 `email`；官网未公开对应联系方式时，`contacts` 可为空，但 `contact_note` 必须写清“本次官方公开扫描未见电话/邮箱”，并用 `contact_source_ids` 指向已核验的一手页面。
- `contacts[].type` 只允许 `phone`、`email`；每条必须填写 `value`、用途 `label`、适用地区/渠道 `scope` 和来源。大陆只收企业总机、客服、销售、售后、支持电话；海外只收销售、支持、安全、隐私、法务等角色邮箱。
- 不收个人手机号、员工个人邮箱、第三方黄页号码或推测邮箱。同一厂商的同值联系方式去重，但可在用途标签中合并多个用途。

### 证据状态 `evidence_status`

只允许：

- `documented`：公开资料已覆盖主要描述字段；
- `partial`：有公开资料，但关键字段不完整；
- `unverified`：本次公开扫描可用资料不足。

证据状态不代表产品好坏、需求适配度或采购优先级。

### 价格类型 `price_type`

只允许：

- `public_price`：厂商或权威渠道明确标价；
- `industry_estimate`：依据公开信号形成的估算；
- `quote_required`：没有可靠公开价格，需要询价。

公开价必须说明查询日期、币种、金额、计费单位、版本/层级、区域和条件，并引用带明确日期的来源；缺少任一关键口径时改标为行业估算或需询价。行业估算必须明确写“估算”并说明依据。询价项必须明确写“需询价”。

### 来源类型 `claim_type`

只允许 `fact`、`vendor_claim`、`inference`、`reference`、`estimate`。

- 厂商官网、产品文档、厂商案例和白皮书中的自述标为 `vendor_claim`；
- `inference` 只用于跨来源的信息归纳，并在正文说明不确定性；
- `estimate` 只用于价格或规模估算；
- 所有 `source_ids` 必须引用已存在来源。
- `sources.url` 只允许 `http://` 或 `https://`；本地附件、工作簿或不可公开定位的材料使用 `source_locator`，且 `url` 与 `source_locator` 至少填写一项。

## 信息完整性规则

- 每家厂商至少填写公开覆盖、具体信息缺口、证据状态、企业地域、地域依据和地域来源；商务入口可为空，渲染时显示“本次公开扫描未见商务入口”；
- `documented` 和 `partial` 至少引用一个来源；
- `unverified` 可无外部来源，但必须写明具体信息缺口；
- 字段缺失写“本次公开扫描未见”，不要写成“没有”；
- 市场结构与趋势不得只由单一厂商来源证明；
- 同一厂商只出现一次；多个产品可合并或在方案名称中明确产品线。
- 卡片主视图可以只显示摘要和前几项标签，但每项能力、每条信息缺口、完整字段原文和全部 `source_ids` 必须保留在可展开区域或来源台账中。

## HTML 展开策略

- 首屏一句话研究对象控制在约 80 个汉字内，并直接显示大陆/海外厂商数量；完整范围放折叠区；
- 市场全景图每层直接列出解决的问题与玩家名字，玩家按大陆、海外、主体待核验分行；色带宽度只编码本次识别厂商数量；
- 1–6 家：供应商卡片直接展开，Long List 默认折叠；单家卡片使用宽版居中，两家使用两列；
- 7–18 家：市场层可折叠且默认展开，Long List 默认折叠；
- 19 家以上或供给类型达到 6 类：市场层默认折叠，Long List 默认展开；
- 0 条技术路线时不生成路线模块；约束或趋势为空时不生成对应章节和导航；
- 点击市场图、导航、Long List 或来源徽标时，自动展开包含目标的折叠区域；
- 市场层颜色按分类动态生成，在同一报告内保持唯一，只用于定位，不表达等级。
- 厂商卡主视图只显示厂商/产品、企业地域、证据状态、公开覆盖摘要、少量能力标签、部署/数据摘要、价格状态和一个关键缺口；完整字段放同卡展开区。

## 旧数据兼容

渲染器可读取旧版研究 JSON：

- `market_landscape` 与 `technology_routes` 合并为中立的 `market_structure`；
- `long_list` 转为 `vendors`，旧版优先级、适配度和推荐状态不显示；
- `priority_vendors` 仅用于补充公开能力、部署和商业字段，不显示推荐理由或下一步建议；
- `commercial_benchmark` 转为 `commercial_signals`；
- `key_risks` 转为无等级的 `risk_signals`；
- `decision`、`shortlist` 和 `next_actions` 被忽略。

兼容转换后仍会扫描采购决策措辞；若旧数据中的推荐、排序或推进语言无法被安全中和，渲染器拒绝生成 HTML，必须先改写为 v3 的事实、风险或信息缺口。

新任务必须直接创建 v3 数据，不得继续写入决策字段。

## 运行

```bash
python scripts/render_sourcing_report.py market-research-data.json --output "市场调研信息整合-<品类>-<YYYYMMDD>.html"
python scripts/qa_sourcing_report.py "市场调研信息整合-<品类>-<YYYYMMDD>.html" --data market-research-data.json
python scripts/self_test.py
```

渲染器校验来源、证据状态、价格语义、中立措辞和字段完整性；QA 脚本校验章节顺序、数量、信息保留、折叠策略、导航目标与模板残留，并生成不依赖外部资源的单文件 HTML。
