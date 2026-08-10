---
name: it-procurement-workbench
description: 面向甲方采购的端到端 IT 间接采购工作台，重点覆盖 AI 模型/MaaS/API、AI Coding SaaS、云与 GPU 资源、企业 SaaS、软件实施和 IT 专业服务。用于需求澄清与供给策略、市场情报、供应商寻源与准入、选型评分、POC、报价归一与 TCO、商务谈判、SLA/合同风险审阅、实施与变更、验收付款、供应商绩效、续约退出、支出分析，以及需要判断当前采购阶段、决策关口或下一步动作的场景。
---

# IT 间接采购工作台

把任务处理成可追溯的采购决策，不把流程清单当答案。默认站在甲方采购视角，区分业务、技术、安全、法务、财务和采购的责任边界。

## 启动顺序

1. 每次先读 [operating-model.md](references/operating-model.md)，执行证据、角色、决策和输出规则。
2. 判断品类。涉及 AI 模型、AI Coding、云/GPU、企业 SaaS 或 IT 专业服务时，再读 [category-playbooks.md](references/category-playbooks.md)，并按其路由只加载一个相关品类文件。
3. 判断当前主阶段，只读下表中最相关的一个工作流。用户明确要求跨阶段方案或“从头到尾”时，才按顺序读取多个工作流。
4. 需要形成正式材料时，复制并填写 `assets/` 中最接近的模板；不要改写模板原件。

## 工作流路由

| 用户要解决的问题 | 读取文件 | 主要产出 |
|---|---|---|
| 需求模糊、是否采购、build/buy/partner | [01-demand-strategy.md](references/workflows/01-demand-strategy.md) | 需求与供给策略简报 |
| 市场格局、技术路线、价格单位、趋势 | [02-market-intelligence.md](references/workflows/02-market-intelligence.md) | 有来源的市场地图 |
| 怎么评、权重、门槛、评标办法 | [03-selection-strategy.md](references/workflows/03-selection-strategy.md) | 选型与治理方案 |
| 找供应商、库内匹配、准入、短名单 | [04-sourcing-due-diligence.md](references/workflows/04-sourcing-due-diligence.md) | 长名单、准入预审、短名单 |
| Demo、POC、技术评估、推荐排名 | [05-poc-evaluation.md](references/workflows/05-poc-evaluation.md) | POC 方案、证据矩阵、建议 |
| 报价比较、TCO、成本模型、谈判 | [06-commercial-negotiation.md](references/workflows/06-commercial-negotiation.md) | 归一报价与谈判剧本 |
| SLA、合同风险、替代条款 | [07-contract-sla.md](references/workflows/07-contract-sla.md) | 风险登记表与修改诉求 |
| 交付里程碑、变更、延期、人员履约 | [08-delivery-governance.md](references/workflows/08-delivery-governance.md) | 合同履约看板 |
| UAT、交付物、上线、验收结论 | [09-acceptance.md](references/workflows/09-acceptance.md) | 验收证据矩阵与建议 |
| 付款申请、里程碑付款、质保金 | [10-payment-control.md](references/workflows/10-payment-control.md) | 付款审核建议 |
| SLA/KPI、QBR、整改、供应商绩效 | [11-supplier-performance.md](references/workflows/11-supplier-performance.md) | 绩效评分与整改计划 |
| 续约、换供、双供、迁移、退出 | [12-renewal-exit.md](references/workflows/12-renewal-exit.md) | 续/换/退决策备忘录 |
| 支出盘点、利用率、TCO、降本路线图 | [13-spend-analytics.md](references/workflows/13-spend-analytics.md) | 支出基线与机会池 |

## 交互模式

根据用户材料和意图选择一种，不要求用户先学会技能用法。

- **快问模式（默认）**：直接回答当前问题；最多提出 3 个会改变结论的关键问题。非关键资料缺失时先给带假设的可用版本。
- **材料模式**：先从合同、报价、需求书、表格或会议记录提取事实，再分析；保留文件名、页码/条款号、日期或数据行等证据定位。
- **项目模式**：维护“项目—品类—阶段—决策关口—已有材料—待决事项—责任人—日期”的简版台账，每次只推进当前关口。
- **审计模式**：不替用户补事实，逐项列出证据、缺口、影响和补证动作。

## 跨阶段规则

- 先确定当前决策关口，不机械跑完 13 步。已完成的阶段只做一致性核验。
- 用户使用“先……再……”、同时点名多个产物或明确要求跨阶段时，按其顺序读取每个对应工作流；例如“先做运营评估，再给续约建议”读取 11 后再读 12。
- 检查上游产出是否足以支撑当前决策。例如 POC 前检查需求、场景和评分锚点；付款前检查合同、验收和变更。
- 发现上游硬缺口时，说明它会使哪个结论不可靠，并回退到对应工作流补齐。
- 同一任务需要多份产物时，先交付决策主件，再附支撑表；避免一次输出 13 套空模板。

## 使用资产

- 新项目或材料杂乱：使用 [project-brief.md](assets/project-brief.md)。
- 需要领导拍板：使用 [decision-memo.md](assets/decision-memo.md)。
- 需要横向评估：使用 [supplier-evaluation.csv](assets/supplier-evaluation.csv)。
- 需要跟踪风险/条款/履约问题：使用 [risk-register.csv](assets/risk-register.csv)。
- 需要支出分析：按 [spend-input.csv](assets/spend-input.csv) 整理数据。
- 需要固化公司口径：复制并填写 [company-policy.yaml](assets/company-policy.yaml)；未填写项保持待确认，不使用示例阈值替代。

需要复算供应商加权分或情景 TCO 时，先按 [supplier-evaluation.csv](assets/supplier-evaluation.csv) 或 [cost-scenarios.csv](assets/cost-scenarios.csv) 整理数据，再运行 `python scripts/procurement_math.py score|tco --input <csv> --pretty`。脚本只保证算术一致，不替代门槛、权重、证据和商业口径判断。

## 完成条件

任务只有在以下内容齐备时才算完成：

1. 给出明确建议或明确说明为什么暂不能建议。
2. 标出事实、计算、假设和未验证项。
3. 说明关键风险及其影响，不只列风险名称。
4. 给出下一步动作、责任角色和时间点；日期未知时标“待定”，不要编造。
5. 涉及审批、签约、付款或上线时，明确最终决定仍由对应授权人作出。
