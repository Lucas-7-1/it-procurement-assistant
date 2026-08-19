---
category: ai-model-services
type: market-playbook
snapshot_date: 2026-08-19
valid_until: 2026-11-19
sources:
  - https://benchlm.ai
  - https://aipricing.guru
  - https://www.deepseek.ai/pricing
  - https://www.volcengine.com
  - https://www.aliyun.com
---

# AI 模型 / MaaS / API 市场手册

## 市场格局分层（2026-08 快照）

| 层级 | 海外厂商 | 中国大陆厂商 |
|------|---------|-------------|
| 旗舰/前沿 | OpenAI（GPT-5.6 Sol）、Anthropic（Claude Opus 5）、Google（Gemini 3.1 Pro） | 阿里通义（Qwen3.8-Max）、字节豆包（Doubao-Seed-Evolving）、月之暗面（Kimi K3） |
| 主力/性价比 | OpenAI（GPT-4.1 / GPT-5.6 Terra）、Anthropic（Claude Sonnet 5）、Google（Gemini 3.6 Flash） | 阿里（Qwen3.5-Plus）、智谱（GLM-5.3）、DeepSeek（V4-Pro）、豆包（Seed-2.1-Turbo） |
| 轻量/经济 | OpenAI（GPT-5.6 Luna / GPT-4o-mini）、Anthropic（Claude Haiku 4.5）、Google（Gemini Flash-Lite） | DeepSeek（V4-Flash）、阿里（Qwen-Long）、豆包（Seed-2.0-mini） |

聚合网关与云市场渠道（数据快照 2026-08-19）：

| 渠道 | 特征 |
|------|------|
| Azure OpenAI | 与 OpenAI 同价或 +10% 数据驻留溢价（2026-03-05 后新模型），支持 PTU 承诺折扣【公开价格】 |
| AWS Bedrock | 按需定价，Claude Sonnet 约 $3/$15 每百万 token，支持 Reserved/Priority 分层【公开价格】 |
| 阿里云百炼 | 千问全系列 + 第三方模型（含 DeepSeek），阶梯计费 + 节省计划 |
| 火山方舟 | 豆包全系列 + DeepSeek，支持 TPM 保障包、模型单元预留 |

同一底层模型经不同渠道供应时，比较重点在价格结构、容量保障、数据路径与责任承接，不重复评"模型效果"。

## 定价模型与基准（数据段）

定价机制摘要（数据快照 2026-08-19）：

| 机制 | 说明 |
|------|------|
| 按 token 计量 | 输入/输出分别计价，输出单价通常为输入的 3-5x，行业标准 |
| 缓存折扣 | OpenAI 命中 75-90% off；Anthropic 90% off；百炼 90% off；火山方舟 80% off【公开价格】 |
| 批处理折扣 | OpenAI/Anthropic/Gemini 统一 50% off（24h 内返回）；百炼 50% off【公开价格】 |
| 承诺用量折扣 | OpenAI 企业版 25-40% off（年承诺 $100K+）；Anthropic 20-40% off（年承诺 $250K+）【行业估算，来源 Redress/VendorBenchmark】 |
| 阶梯计费 | 百炼/火山方舟按单次输入长度分档，长上下文单价上浮 1.5-3x【公开价格】 |
| 峰谷时段 | DeepSeek 峰时 2x 价格【公开价格】 |

主流模型价格基准，每百万 token（数据快照 2026-08-19）：

| 模型 | 输入价 | 输出价 | 币种 | 来源与标注 |
|------|--------|--------|------|-----------|
| OpenAI GPT-5.6 Sol | $5.00 | $30.00 | USD | benchlm.ai/openai、aipricing.guru【公开价格】 |
| OpenAI GPT-5.6 Terra | $2.00 | $12.00 | USD | benchlm.ai/openai【公开价格】 |
| OpenAI GPT-5.6 Luna | $0.20 | $1.20 | USD | aipricing.guru【公开价格】 |
| Anthropic Claude Opus 5 | $5.00 | $25.00 | USD | benchlm.ai/anthropic【公开价格】 |
| Anthropic Claude Sonnet 5 | $2.00 | $10.00 | USD | benchlm.ai/anthropic【公开价格】；8/31 前促销价，原定 9/1 涨至 $3/$15 已取消 |
| Anthropic Claude Haiku 4.5 | $1.00 | $5.00 | USD | benchlm.ai/anthropic【公开价格】 |
| Google Gemini 3.1 Pro | $2.00 | $12.00 | USD | benchlm.ai/google【公开价格】；≤200K 上下文 |
| DeepSeek V4-Pro | $0.435 | $0.87 | USD | deepseek.ai/pricing、benchlm.ai【公开价格】；8/16 涨价后 |
| DeepSeek V4-Flash | $0.14 | $0.28 | USD | deepseek.ai/pricing【公开价格】；火山方舟 8/21 将调至 ¥3/¥9 |
| 智谱 GLM-5.3 | $1.40 | $4.40 | USD | docs.z.ai【公开价格】 |
| 阿里 Qwen3-Max | ¥2.5 | ¥10 | CNY | 阿里云帮助文档、dayuyun.com【公开价格】；≤32K，32K-128K 为 ¥4/¥16 |
| 豆包 Seed-2.1-Turbo | ¥3.0 | ¥15.0 | CNY | volcengine.com【公开价格】 |

价格波动备注：DeepSeek 2026-08-16 单方面涨价，Reuters 报道涨幅 50%-1100%。旗舰与轻量模型单价差距可达 10-25x。企业级承诺折扣的具体档位【需询价】。

## TCO 驱动因子

1. 输出 token 占比。输出单价显著高于输入，输出密集型应用 TCO 远超单价直觉。
2. 上下文长度。长上下文请求触发阶梯加价或消耗更多 token。
3. 峰谷用量分布。部分厂商峰时加价、部分渠道有区域溢价。
4. 缓存命中率。最大的输入成本优化杠杆，架构设计阶段就应纳入。
5. 批处理可行性。非实时场景改用 Batch API 可显著降低有效单价。
6. 模型选择与路由。按任务难度分流至不同档位模型是主要降本手段。
7. 多供应商切换成本。prompt 适配、评测、集成维护均计入退出成本。

## 评分权重参考

| 维度 | 建议权重 | 说明 |
|------|---------|------|
| 模型能力/质量 | 25-30% | 基准测试 + 业务场景评测 |
| 定价经济性 | 20-25% | 含折扣、缓存、批处理后的有效单价 |
| 可用性/SLA | 15% | TPM/RPM 保障、故障恢复 |
| 安全合规 | 15% | 数据留存、训练 opt-out、合规认证 |
| 生态/集成 | 10% | SDK 成熟度、多模型路由支持 |
| 商务灵活性 | 5-10% | 合同条款、true-down、退出机制 |

## 谈判杠杆与话术

1. 承诺换折扣。以年度 token 消费承诺换取阶梯折扣，主流厂商均支持。模板："我们已完成 POC，准备年化承诺 $XXK，希望获得与此对应的阶梯折扣。"
2. 多供应商路由。展示已对接多家模型的技术能力，暗示流量可随时切换。模板："我们的 LLM Gateway 已支持 3 家模型热切换，希望看到有竞争力的报价。"
3. 架构优化压基线。先用批处理/缓存压低有效单价，再以优化后的低基线要求进一步折扣。
4. 季度复价条款。要求写入 quarterly price review 或 MFN（最惠价格）条款，应对模型快速降价趋势。
5. 预付换深折扣。以预付承诺换折扣时，同步要求 true-down 或额度滚存（rollover）。

## 合同/SLA 品类要点

| 要点 | 行业惯例 | 注意事项 |
|------|---------|---------|
| 模型下线通知期 | OpenAI 官方 deprecation 页面明确 6 个月；AWS Bedrock 有结构化生命周期日历 | 合同写入不低于 6 个月通知期 |
| 版本变更 | OpenAI、百炼提供日期版本锚定（pinned version） | 要求 pinned version 至少维护 12 个月 |
| 训练 opt-out | OpenAI/Anthropic API 默认不训练 | 企业版必须合同写入 zero-retention training opt-out |
| 数据留存 | OpenAI API 默认 30 天日志，可申请 zero-retention；Anthropic 类似 | 合同明确留存期限 + 删除 SLA |
| 容量承诺 | Azure PTU 可锁定容量；火山方舟有 TPM 保障包 | 高峰需求锁定保障包，避免限流 |
| SLA 可用性 | Azure OpenAI PTU 为 99.9%；一般按需通常无 SLA | 要求写入 SLA + 赔偿条款 |

## 典型风险 Top5

1. 价格波动。模型厂商可单方面调价，DeepSeek 2026 年 8 月大幅涨价为典型案例（幅度见定价节）。
2. 模型退役/能力退化。版本迭代后旧模型下线或行为变化，产生应用回归测试成本。
3. 供应商锁定。prompt 优化与 fine-tune 权重不可移植。
4. 数据安全与合规。训练数据泄露、跨境数据传输合规（中国/欧洲）。
5. 容量限制与性能不稳定。高峰期限流、延迟飙升影响生产 SLA。

## 来源与时效

| 来源 | 覆盖内容 | 类型 |
|------|---------|------|
| https://benchlm.ai | OpenAI/Anthropic/Google/Moonshot 模型价格聚合 | 【公开价格】 |
| https://aipricing.guru | GPT-5.6 系列价格 | 【公开价格】 |
| https://www.deepseek.ai/pricing | DeepSeek V4 系列官方定价 | 【公开价格】 |
| https://www.volcengine.com | 火山方舟豆包系列定价、TPM 保障包 | 【公开价格】 |
| https://www.aliyun.com | 阿里云百炼千问系列定价（帮助文档） | 【公开价格】 |
| https://docs.z.ai | 智谱 GLM-5.3 定价 | 【公开价格】 |
| Redress Compliance / VendorBenchmark 公开文章 | 企业级承诺折扣区间 | 【行业估算】 |

数据快照可能过期，重大决策前联网核实当前价格。
