---
category: cross-category
type: methodology
snapshot_date: 2026-08-19
valid_until: 2027-08-19
sources:
  - https://enersys.co.th/en/insights/tco-total-cost-ownership-software-purchase-framework-2026
  - https://www.finops.org/wg/how-to-calculate-percentage-of-cb-discount-waste/
  - https://resources.rework.com/guides/saas-buying-framework/switching-saas-vendors
  - https://www.investopedia.com/terms/n/npv.asp
  - https://www.paddle.com/resources/discount-rate-formula
---

# TCO 高级模型（跨品类方法论）

本文件只提供 TCO 建模基准、公式与脚本字段约定；报价归一与谈判流程见 `references/workflows/06-commercial-negotiation.md`，此处不复述。

## 1. 五层成本分类

| 层级 | 成本类别 | 包含项目 |
|------|----------|----------|
| L1 | 订阅/消耗成本 | 许可费/订阅费、按用量计费（API 调用/存储/计算）、模块附加费 |
| L2 | 实施集成成本 | 定制开发、数据迁移、系统集成（API/中间件）、咨询与项目管理 |
| L3 | 运维人力成本 | 托管/基础设施、维护升级、技术支持（分级）、安全合规审计、内部管理工时 |
| L4 | 培训与变更成本 | 供应商培训费、内部材料制作、生产力下降期（"Valley of Loss"：切换后 4-10 周产能降 20-40%）、变更管理 |
| L5 | 退出/迁移成本 | 数据导出、迁移工时、并行期双付、合同终止罚金、再培训、业务中断损失 |

Gartner 将 TCO 分为直接成本（软硬件+运维）与间接成本（支持+停机+低效使用）；Panorama Consulting 2025 报告指出软件许可仅占 ERP 总支出 20-30%，L2-L5 层不可省略。

## 2. 折现规则与 NPV 公式

| 参数 | 惯例 | 说明 |
|------|------|------|
| 企业 WACC 常用区间 | 8%-12% | 技术型上市公司典型区间；非上市中小企业可高至 14-16% |
| 是否折现判断 | 合同≤1 年：不折现；2-3 年：建议折现；≥3 年：必须折现 | McKinsey 建议以 3 年 NPV 为迁移决策的标准门槛 |
| NPV 公式 | NPV = Σ[CFₜ / (1+r)^t] − 初始投资 | CFₜ 为第 t 期净现金流，r 为折现率 |
| 简化惯例 | 内部 IT 投资，年化差异<5% 且合同≤2 年可不折现 | 【综合建议】 |

## 3. 退出成本分类与估算方法

| 退出成本项 | 估算方法 | 典型金额 |
|------------|----------|----------|
| 数据导出费 | 厂商报价，按数据量计 | 部分厂商免费，部分按 GB 收费 |
| 迁移工时 | 记录数×复杂度系数；中等 CRM：80-200 人时 | 外部承包商 $5K-80K |
| 并行期双付 | 月费×重叠周数/4；通常 4-8 周 | 月费的 1-2 倍 |
| 再培训 | 用户数×人均培训时×时薪；CRM 切换：6 周×25% 产能降 | 15 人团队约 $72K |
| 合同终止费 | 剩余合同期金额（无 TFC 条款时） | 0 至全部剩余合同价值 |
| 业务中断 | 收入/小时×停机时数×事件频率 | 因企业而异 |
| 集成重建 | 单个集成 $500-50K；中等 6 个集成 $30K-60K | REST API：$5K-15K/个 |

Gartner 研究显示迁移总成本平均为首年许可节省的 2-4 倍，退出成本须计入多年期 TCO 的末期。

## 4. 承诺废弃损失（FinOps）与利用率建模

FinOps Foundation 官方公式：

```
承诺折扣废弃率(%) = (未使用的承诺折扣成本 / 承诺折扣总成本) × 100
```

- 输入：承诺总额（如 RI/Savings Plan 年费）、实际利用额。
- 行业基准：组织通常仅利用 47% 的已购 SaaS 许可（Chief Wise Officer 引用数据）。
- 云承诺目标：成熟 FinOps 团队将废弃率控制在 <5%。
- 建模方式：每期废弃损失 = 承诺总额 × (1 − 预计利用率)，与订阅/消耗成本一并计入该期成本。

## 5. 敏感性分析方法

- 对利用率做 ±10%、±20% 波动假设。
- 对价格上涨率做 0% / 5% / 10% 三档。
- 输出 TCO 在不同组合下的区间（最优/基线/最差），并说明排名是否因此翻转。

## 6. 与 `procurement_math.py` `tco-advanced` 子命令字段映射

在现有 `tco` 命令输入列（`vendor_id, scenario, item_id, item, quantity, unit_price, periods, escalation_rate, currency, evidence_status`）基础上新增 5 列：

| 列名 | 语义 | 数据类型 | 计算约定 |
|------|------|----------|----------|
| discount_rate | 年折现率 | float (0-1) | 0 表示不折现；典型 0.08-0.12；折现因子 (1+r)^t，t=1..N |
| exit_cost | 退出一次性成本 | float | 计入最后一期（period=N）成本后再折现 |
| commitment_amount | 每期承诺总额 | float | 如年度 RI/Savings Plan 承诺额 |
| expected_utilization | 预计利用率 | float (0-1) | 每期废弃损失 = commitment_amount × (1 − expected_utilization) |
| migration_cost | 迁移一次性成本 | float | 计入首期（period=1）成本 |

**计算公式约定**（t=1..N）：

```
period_cost[t] = quantity × unit_price × (1 + escalation_rate)^(t-1)
                 + commitment_amount × (1 - expected_utilization)
period_cost[1] += migration_cost
period_cost[N] += exit_cost
NPV = Σ [period_cost[t] / (1 + discount_rate)^t]   (t = 1..N)
```

要点：涨价上浮首期不生效（指数为 t−1，与现有 `tco` 命令 `(1+e)^period, period=0..N-1` 的口径一致）；折现从第 1 期即开始（指数为 t）。

**对照示例**（6 行场景，r=0.10）：I01 订阅 50×100×3 期、e=5% → NPV≈13,026；I02 实施 25,000 一次性 → 22,727；I03 云计算 8,000/期、e=8%、承诺 12,000、利用率 75%（每期废弃 3,000）→ 28,884；I04 migration_cost=15,000 计首期 → 13,636；I05 exit_cost=20,000 计末期 → 15,026；I06 培训 5,000 一次性 → 4,545；合计 NPV ≈ 97,844 USD。实现方可用该组数值做回归验证。

## 来源

| 来源 | 类型 | URL | 查询日期 |
|------|------|-----|----------|
| Enersys 5-Layer TCO Framework | 行业文章 | https://enersys.co.th/en/insights/tco-total-cost-ownership-software-purchase-framework-2026 | 2026-08-19 |
| FinOps Foundation CB Discount Waste | 官方/权威 | https://www.finops.org/wg/how-to-calculate-percentage-of-cb-discount-waste/ | 2026-08-19 |
| Rework: Switching SaaS Vendors | 行业文章 | https://resources.rework.com/guides/saas-buying-framework/switching-saas-vendors | 2026-08-19 |
| Investopedia NPV | 权威参考 | https://www.investopedia.com/terms/n/npv.asp | 2026-08-19 |
| Paddle WACC formula | 行业文章 | https://www.paddle.com/resources/discount-rate-formula | 2026-08-19 |
