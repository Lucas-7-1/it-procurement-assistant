---
category: cross-category
type: methodology
snapshot_date: 2026-08-19
valid_until: 2027-08-19
sources:
  - https://www.gartner.com/en/research/methodologies/research-methodologies-gartner-critical-capabilities
  - http://www.mof.gov.cn/gkml/bulinggonggao/tongzhitonggao/200805/t20080519_25532.htm
  - https://szfb.sz.gov.cn/zxbs/ywgz_3_1/sfjdl_3/content/post_10214112.html
  - https://wicely.com/resources/supplier-evaluation-criteria-weighted-scoring
---

# 评分与 RFP 基准（跨品类方法论）

本文件只提供评估维度、权重基准区间、锚点模板与评标规定；"如何设计评分框架与治理"的流程见 `references/workflows/03-selection-strategy.md`，此处不复述。

## 1. 八大评估维度与子指标

| 维度 | 子指标示例 |
|------|-----------|
| 功能适配 | 核心功能覆盖率、定制化能力、API 开放度、路线图匹配 |
| 技术架构 | 可扩展性、性能基准、多租户/部署模式、技术栈兼容 |
| 安全合规 | ISO 27001/SOC2 认证、数据驻留、加密标准、GDPR/个保法合规 |
| 服务支持 | SLA 等级、响应时间、CSM 配备、文档质量、7×24 支持 |
| 商务 TCO | 单价、总拥有成本、价格锁定、付款条件、价格透明度 |
| 供应商实力 | 财务健康度、市场份额、客户基数、融资阶段、员工稳定性 |
| 生态集成 | 合作伙伴生态、预建集成数、社区活跃度、第三方工具兼容 |
| 退出便利 | 数据可移植性、合同终止条件、标准格式导出、迁移辅助承诺 |

方法论依据：Gartner Critical Capabilities——按用例对产品打分，再按用例权重加权。

## 2. 按品类权重基准区间

| 维度 | AI API | AI Coding | 云/GPU | 企业 SaaS | IT 服务 |
|------|--------|-----------|--------|----------|--------|
| 功能适配 | 25-30% | 30-35% | 15-20% | 25-30% | 20-25% |
| 技术架构 | 20-25% | 20-25% | 25-30% | 15-20% | 15-20% |
| 安全合规 | 15-20% | 10-15% | 15-20% | 15-20% | 10-15% |
| 服务支持 | 5-10% | 10-15% | 10-15% | 15-20% | 25-30% |
| 商务 TCO | 15-20% | 10-15% | 20-25% | 15-20% | 15-20% |
| 供应商实力 | 5-10% | 5-10% | 5-10% | 5-10% | 5-10% |
| 生态集成 | 5-10% | 10-15% | 5-10% | 10-15% | 5-10% |
| 退出便利 | 5-10% | 5-10% | 5-10% | 5-10% | 5-10% |

【综合建议】上表为基准区间而非定值，基于 Gartner CC 方法论（按用例差异化权重）+ SemiAnalysis ClusterMAX GPU 云评估六维度（硬件/定价/安全/合规/SLA/生态）+ 行业惯例综合。依据：AI API 因模型能力差异大故功能权重最高；云/GPU 因高支出故 TCO 权重提升；IT 服务因交付依赖人故服务支持权重最高。实际权重按项目目标在区间内取值，合计须为 100%。

## 3. 1-5 分锚点定义模板

| 分值 | 锚点定义 |
|------|----------|
| 5 - 卓越 | 显著超越需求，业界最佳实践水准，有独特差异化优势 |
| 4 - 良好 | 完全满足需求，部分超出，有明确证据支撑 |
| 3 - 合格 | 基本满足需求，无明显短板，可接受范围 |
| 2 - 不足 | 部分满足需求，存在可识别差距，需补救措施 |
| 1 - 不可接受 | 未能满足基本要求，存在重大风险或缺失 |

各标准的具体锚点在此模板上按子指标具体化，使评委可对照证据打分。

## 4. 门槛项与加权项分离

- 门槛项（一票否决）：安全认证（如 SOC2 Type II）、数据驻留合规、最低 SLA（如 99.9%）、财务稳定性底线。不满足则直接淘汰，不进入评分。
- 加权项：通过门槛后按权重计算综合得分。
- 门槛与评分不混用：门槛只判定通过/不通过，不折算为分数；普通弱项进入加权评价。

## 5. RFI / RFP / RFQ 适用场景

| 文件类型 | 适用场景 | 核心内容 |
|----------|----------|----------|
| RFI | 市场摸底、初步筛选（5+ 供应商） | 供应商概况、能力声明、参考案例 |
| RFP | 正式评选（3-5 家短名单） | 详细需求响应、技术方案、商务报价、SLA 承诺 |
| RFQ | 标准化采购/仅比价 | 明确规格、单纯报价竞争 |

**技术商务分离评审**：先评技术（不含报价），达到及格线后再评商务价格，防止低价导向。中国政府采购已引入此两阶段模式。

## 6. 中国政府采购综合评分法价格分权重规定

依据财政部《关于加强政府采购货物和服务项目价格评审管理的通知》：

- 货物类项目：价格分权重 **30%-60%**。
- 服务类项目：价格分权重 **10%-30%**。
- 评审因素须量化、可评分。
- 价格分计算：满足实质性响应条件中报价最低的为价格满分基准，其他按比例折算。

## 7. 常见评标偏差与纠偏

| 偏差 | 纠偏 |
|------|------|
| 评委主观分不一致 | 设置客观量化锚点、召开校准评分会议 |
| 价格权重过低导致高价中标 | 遵循法定最低权重 |
| 技术指标指向性过强 | 使用功能描述而非品牌参数 |

## 8. 与现有资产衔接

本文件的维度/权重/锚点对应 `assets/supplier-evaluation.csv` 的 `criterion_id/criterion_name/weight/score/score_anchor` 列，门槛项对应 `mandatory_gate/gate_result` 列，填好后由 `scripts/procurement_math.py score` 计算加权得分与门槛状态。

## 来源

| 来源 | 类型 | URL | 查询日期 |
|------|------|-----|----------|
| Gartner Critical Capabilities Methodology | 官方/权威 | https://www.gartner.com/en/research/methodologies/research-methodologies-gartner-critical-capabilities | 2026-08-19 |
| 财政部价格评审管理通知 | 官方/权威 | http://www.mof.gov.cn/gkml/bulinggonggao/tongzhitonggao/200805/t20080519_25532.htm | 2026-08-19 |
| 深圳财政局综合评分法说明 | 官方/权威 | https://szfb.sz.gov.cn/zxbs/ywgz_3_1/sfjdl_3/content/post_10214112.html | 2026-08-19 |
| Wicely Supplier Evaluation Framework | 行业文章 | https://wicely.com/resources/supplier-evaluation-criteria-weighted-scoring | 2026-08-19 |
