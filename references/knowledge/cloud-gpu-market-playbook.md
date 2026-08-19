---
category: cloud-gpu
type: market-playbook
snapshot_date: 2026-08-19
valid_until: 2026-11-19
sources:
  - https://www.spheron.network/blog/gpu-cloud-pricing-comparison-2026/
  - https://axecompute.com/gpu-cloud-providers-comparison-2026/
  - https://sedai.io/blog/gcp-vs-aws-vs-azure-savings-plans-comparison
  - https://www.automatum.io/blog-posts/aws-edp-enterprise-discount-program-guide
  - https://www.finops.org/framework/capabilities/unit-economics/
---

# 云 / GPU 市场剧本

## 市场格局分层（2026-08 快照）

| 层级 | 海外 | 中国大陆 | 定位 |
|------|------|----------|------|
| 超大规模云（Hyperscaler） | AWS、Azure、GCP | 阿里云、腾讯云、华为云 | 全栈服务、企业合规、生态锁定强 |
| GPU 专业云（Neo-cloud） | CoreWeave、Lambda Labs、Nebius、RunPod、Spheron | 火山引擎、优刻得、天翼云（昇腾） | 低价裸算力；CoreWeave 偏企业长约，Lambda/RunPod/Spheron 偏按需/Spot |
| 去中心化 / 市场化 | Vast.ai、TensorDock、io.net | — | 价格最低、SLA 最弱 |

结构性价差（数据快照 2026-08-19）：Neo-cloud 的 GPU 按需价格比超大规模云低 40-85%【公开价格】，差距来自更低管理费、更少附加服务和更薄利润率。中国大陆受管控 GPU 型号（A800/H800、昇腾）普遍不公示时租，官网仅见包月/包年优惠价，按需价【需询价】。

## 定价模型与基准（数据段）

折扣机制基准（数据快照 2026-08-19，均为【公开价格】口径）：

| 机制 | 云商 | 期限 | 典型折扣率 |
|------|------|------|-----------|
| Reserved Instance | AWS | 1年 | ~30%（全预付可达 40%） |
| Reserved Instance 全预付 | AWS | 3年 | 最高 72-75% |
| Savings Plan | AWS | 1/3年 | 最高 72%，跨 instance family |
| Reserved VM | Azure | 3年 | 最高 72% |
| Savings Plan | Azure | 1-3年 | 最高 65% |
| CUD（资源型） | GCP | 3年 | 55-70%（内存优化型可达 70%） |
| EDP / PPA（全账单） | AWS | 1-5年 | 5-20%，门槛 $1M+/年 |
| Spot 实例 | AWS/Azure/GCP | 无 | 60-90% off on-demand，可被回收 |
| Reserved Cluster | Neo-cloud | 1-12月 | 20-40% off on-demand，谈判制 |

AWS EDP 折扣梯度（数据快照 2026-08-19）：$1M-$5M 承诺对应 3-7%；$5M-$20M 对应 7-12%；$20M-$50M 对应 10-15%；$50M+ 对应 15-20%+。

GPU 时租基准（USD/hr，按需，数据快照 2026-08-19，来源见文末）：

| GPU | 提供商 | 时租 | 标注 |
|-----|--------|------|------|
| H100 SXM5 | AWS (p5) | ~$6.88 | 【公开价格】2026-05 |
| H100 SXM5 | Azure (ND H100 v5) | ~$12.29 | 【公开价格】2026-05 |
| H100 SXM5 | GCP (A3-high) | ~$3.00 | 【公开价格】2026-05 |
| H100 SXM5 | Lambda Labs | $4.29 | 【公开价格】2026-08 |
| H100 SXM5 | Spheron | $2.54 | 【公开价格】2026-07 |
| H100 | CoreWeave | ~$4.25 (PCIe) / $6.16 (HGX) | 【公开价格】2026 |
| H200 SXM | AWS / Spheron | ~$4.98 / $3.70 | 【公开价格】2026 |
| B200 SXM6 | AWS (p6) / Lambda | ~$14.24 / $6.99 | 【公开价格】2026 |
| B200 | 28+ 供应商中位数 | $6.25 | 【公开价格】2026 |
| 昇腾 910B | 华为云/天翼云 | 【需询价】 | 经价格计算器或商务询价 |
| A10（GN7i 包月） | 阿里云 | ¥3,213.99/月起 | 【公开价格】2026 |
| A100/A800 | 火山引擎 | 【需询价】 | 官方未公示时租 |

FinOps 与谈判锚点（数据快照 2026-08-19）：承诺覆盖率目标 70-90%；承诺利用率 ≥85% 为健康；资源标签覆盖率目标 ≥70%；分配覆盖率成熟实践 80-90%；Hyperscaler 出网费 $0.08-0.12/GB；AWS EDP 允许最多 25% 承诺额用于 Marketplace ISV 采购。

## TCO 驱动因子

排序：GPU 计算费 > 承诺折扣执行 > 数据出网费 > 存储费 > 网络/IP 费 > 运维人力。计算费本身由"有效利用率"放大或稀释：标称卡时不等于有效算力，承诺买多用少与买贵型号跑轻负载是最常见的隐性浪费。大模型训练场景需单独评估 checkpoint 跨区同步产生的出网费。

## 评分权重参考

| 维度 | 建议权重 |
|------|---------|
| 单价（时租/承诺价） | 30-35% |
| 容量保证 / 可用性 SLA | 20-25% |
| 灵活性（最小承诺、计费粒度） | 15% |
| 网络 / 出网费用 | 10% |
| 技术生态 / 兼容性 | 10% |
| 安全合规 | 10% |

紧缺 GPU 场景可将"容量保证"权重上调，价格权重相应下调；容量拿不到时价格没有意义。

## 谈判杠杆与话术

- 承诺换折扣：以多年 EDP/CUD 承诺换全账单折扣，折扣随承诺金额递增（梯度见基准表）；承诺规模从基准情景的覆盖率目标下限起步，超出部分保留弹性。
- 多云议价：向 Hyperscaler 出示 Neo-cloud 等规格报价（价差见时租基准表）施压，即使不真迁移也能压缩报价。
- 迁移补贴：利用 AWS MAP 等迁移计划争取专项折扣与 credits。
- 出网费减免：以承诺换出网费率锁定或减免；或将出网密集型负载放到零出网费的 Neo-cloud。
- Marketplace 抵消：把既有 ISV 采购走 Marketplace 计入 EDP 承诺额，降低承诺缺口风险。

可复制话术模板：

1. "我们已拿到 GPU 专业云同规格集群的书面报价，如贵方能在本季度内给出承诺折扣方案，并在合同中写入容量保证与出网费减免条款，我们可以签多年承诺。"
2. "承诺额度按基准情景覆盖率目标的下限起步；未用承诺需支持 rollover 或缺口容忍条款，否则我们只能下调承诺规模。"

## 合同 / SLA 品类要点

- 容量保证 vs 尽力交付：GPU 合同必须区分 guaranteed capacity 与 best-effort，并明确 GPU 不可用时的 SLA credits 赔付机制。
- 承诺未用处理：AWS EDP 年底 shortfall 会按无折扣价追缴差额，应争取 rollover 或缺口容忍度。
- 折扣叠加规则：EDP 折扣不叠加 RI；签约前核算实际有效折扣路径。
- 价格与粒度：锁定出网费率；确认最低计费粒度（per-second / per-minute / per-hour）。
- 退出条款：数据导出、镜像/IaC 可移植与终止协助写入合同，对关键负载定义连续不达标的替代资源与退出权。

## 典型风险 Top5

1. 承诺过度：实际用量低于预测，承诺变成浪费。
2. GPU 容量不可得：Spot 回收或供应不足导致训练中断。
3. 出网费失控：大模型 checkpoint 频繁跨区域同步。
4. 供应商锁定：技术栈深耦合导致无法迁移。
5. 价格波动：GPU 供需变化引发 Spot/按需价格大幅波动。

## 来源与时效

| 来源 | URL |
|------|-----|
| Spheron GPU 价格对比 2026 | https://www.spheron.network/blog/gpu-cloud-pricing-comparison-2026/ |
| Axe Compute 供应商对比 2026 | https://axecompute.com/gpu-cloud-providers-comparison-2026/ |
| Sedai 三云 Savings Plans 对比 | https://sedai.io/blog/gcp-vs-aws-vs-azure-savings-plans-comparison |
| nOps / Hykell / Automatum / Redress AWS EDP 指南 | https://www.nops.io/blog/ultimate-guide-aws-edp/ ; https://hykell.com/knowledge-base/aws-edp/ ; https://www.automatum.io/blog-posts/aws-edp-enterprise-discount-program-guide ; https://redresscompliance.com/aws-edp-discount-benchmarks |
| computeprices Lambda 价格 | https://computeprices.com/providers/lambda |
| buildmvpfast GPU 云成本对比 2026 | https://www.buildmvpfast.com/blog/gpu-cloud-cost-comparison-runpod-lambda-labs-coreweave-2026 |
| AIMultiple GPU Index / getdeploying B200 | https://aimultiple.com/gpu-index ; https://getdeploying.com/gpus/nvidia-b200 |
| 华为云昇腾 / 阿里云 GN7i / 火山引擎 | https://www.huaweicloud.com/product/ecs/ascend.html ; https://developer.aliyun.com/article/1741459 ; https://www.volcengine.com/docs/6419/69805 |
| DoiT / Opsolute / Cloudaware / FinOps Foundation | https://www.doit.com/blog/finops-best-practices-9-proven-strategies-to-optimize-and-reduce-cloud-costs ; https://opsolute.io/blog/finops-best-practices-for-cloud-cost-optimization ; https://cloudaware.com/blog/cloud-cost-optimization-metrics/ ; https://www.finops.org/framework/capabilities/unit-economics/ |
| VendorBenchmark GCP / Azure 官方 | https://vendorbenchmark.com/vendors/google-cloud-platform-gcp-pricing ; https://azure.microsoft.com/en-us/pricing/offers/reservations |

数据快照可能过期，重大决策前联网核实当前价格。
