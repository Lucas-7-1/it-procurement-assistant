---
category: cross-category
type: methodology
snapshot_date: 2026-08-19
valid_until: 2027-08-19
sources:
  - https://mindsetcyber.com.au/iso-31000-risk-matrix/
  - https://mitti.com/topics/risk-assessment/5x5-risk-matrix
  - https://www.auravms.com/blogs/procurement-risk-register-template-supplier-risk-tracking
  - https://www.ivalua.com/blog/procurement-risk-management/
---

# 风险登记方法（跨品类方法论）

本文件提供 IT 采购风险分类、五级概率/影响定义、评级切分与应对策略选择逻辑，以及与 `assets/risk-register.csv` 的字段映射；各阶段何时识别与升级风险由 `references/workflows/` 各流程文件约定，此处不复述。

## 1. 五大风险域定义

| 风险域 | 说明 | 典型风险 |
|--------|------|----------|
| 供应连续性 | 供应商无法持续提供服务 | 供应商破产、被收购、产品 EOL |
| 技术锁定 | 深度依赖致迁移困难 | 专有格式、API 不兼容、定制化深度 |
| 商业风险 | 价格/合同条款不利 | 价格暴涨、承诺废弃、汇率波动 |
| 合规数据 | 法律法规/数据安全问题 | GDPR 违规、数据泄露、跨境传输 |
| 交付运营 | 服务质量/交付不达标 | SLA 不达标、响应迟缓、功能延期 |

## 2. 概率/影响五级定义

**概率等级**：

| 等级 | 分值 | 定义 |
|------|------|------|
| 极低 | 1 | <5% 概率，极少发生 |
| 低 | 2 | 5-20%，可能但不太常见 |
| 中等 | 3 | 20-50%，合理预期范围 |
| 高 | 4 | 50-80%，很可能发生 |
| 极高 | 5 | >80%，几乎确定 |

**影响等级**：

| 等级 | 分值 | 定义 |
|------|------|------|
| 微小 | 1 | 可忽略损失，<1% 预算影响 |
| 轻微 | 2 | 小损失，1-5% 预算/1 天中断 |
| 中等 | 3 | 显著损失，5-15% 预算/1 周中断 |
| 重大 | 4 | 严重损失，15-30% 预算/1 月中断 |
| 灾难 | 5 | 毁灭性，>30% 预算/核心业务停摆 |

## 3. 评级切分与应对策略选择逻辑

风险评级 = 概率 × 影响（1-25），切分如下：

| 评级区间 | 等级 | 默认动作 |
|----------|------|----------|
| 1-6 | 低风险（绿） | 接受/监控 |
| 7-14 | 中风险（黄） | 缓解/转移 |
| 15-25 | 高风险（红） | 规避/立即行动 |

**应对策略选择逻辑**：

| 策略 | 选择条件 | 典型手段 |
|------|----------|----------|
| 规避 | 风险评级高且成本可控 | 改变方案消除风险源 |
| 转移 | 影响大但可通过合同/保险转嫁 | SLA 罚则、保险 |
| 缓解 | 最常用，降低概率或影响 | 备选供应商、监控预警 |
| 接受 | 低风险或缓解成本 > 风险损失 | 记录 + 定期复查 |

## 4. 五品类典型风险 Top5

| 排序 | AI API | AI Coding | 云/GPU | 企业 SaaS | IT 服务 |
|------|--------|-----------|--------|----------|--------|
| 1 | 模型能力突变/替代（技术锁定） | 代码质量/安全漏洞注入（交付运营） | 承诺废弃/利用率不足（商业） | 供应商大幅涨价（商业） | 关键人员离职（供应连续） |
| 2 | API 定价不透明/暴涨（商业） | IP 归属不明/代码泄露（合规数据） | 数据出站费用失控（商业） | 深度定制致锁定（技术锁定） | 交付质量不达标（交付运营） |
| 3 | 数据隐私/合规风险（合规数据） | 供应商被收购/停服（供应连续） | 区域可用性/合规要求（合规数据） | 自动续费陷阱（商业） | 需求范围蔓延（商业） |
| 4 | 调用量突增致账单爆炸（交付运营） | 模型 hallucination 导致事故（交付运营） | GPU 缺货/排队（供应连续） | 数据迁移困难（技术锁定） | 合同终止纠纷（合规） |
| 5 | 供应商政策变更/限流（供应连续） | 产品 roadmap 偏移（技术锁定） | 单一可用区故障（交付运营） | 集成中断/API 变更（交付运营） | 知识转移不完整（技术锁定） |

## 5. 与 `assets/risk-register.csv` 字段映射及枚举值建议

现有表头：`risk_id, case_id, stage, category, vendor_id, source_ref, risk_domain, current_fact, trigger_and_impact, likelihood, impact, rating, status, mitigation_or_clause_request, owner, due_date, approval_required, evidence_status, residual_risk, notes`。字段设计已与 ISO 31000 框架高度兼容，无需修改该 CSV，仅在枚举值上对齐本文件分类体系：

| 现有字段 | 方法论映射 | 建议用法 |
|----------|-----------|----------|
| risk_domain | 本文件五大风险域 | 枚举：supply_continuity / tech_lockin / commercial / compliance_data / delivery_ops |
| likelihood | 1-5 概率等级 | 整数 1-5 |
| impact | 1-5 影响等级 | 整数 1-5 |
| rating | likelihood × impact | 自动计算 1-25 |
| status | 应对策略阶段 | 枚举：identified / mitigating / accepted / closed |
| mitigation_or_clause_request | 对应应对策略 | 具体措施 + 合同条款要求 |
| residual_risk | 缓解后残余风险评级 | 重新评估后的 rating 值 |
| category | 品类标签 | 枚举：ai_api / ai_coding / cloud_gpu / enterprise_saas / it_service |

如后续需要扩展（不改动现有表头即可选加）：`risk_response_type`（枚举 avoid/transfer/mitigate/accept）、`review_frequency`（复查频率 monthly/quarterly）。

## 来源

| 来源 | 类型 | URL | 查询日期 |
|------|------|-----|----------|
| ISO 31000 Risk Matrix (MindsetCyber) | 社区经验 | https://mindsetcyber.com.au/iso-31000-risk-matrix/ | 2026-08-19 |
| SafetyCulture 5x5 Matrix Guide | 行业文章 | https://mitti.com/topics/risk-assessment/5x5-risk-matrix | 2026-08-19 |
| AuraVMS Procurement Risk Register | 行业文章 | https://www.auravms.com/blogs/procurement-risk-register-template-supplier-risk-tracking | 2026-08-19 |
| Ivalua Procurement Risk Management | 行业文章 | https://www.ivalua.com/blog/procurement-risk-management/ | 2026-08-19 |
