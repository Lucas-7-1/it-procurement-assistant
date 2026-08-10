# 品类路由

先识别采购对象和实际价值链，再加载一个最相关的品类文件。一个项目横跨多个品类时，按“主采购对象”处理主线，仅在成本、风险或合同责任无法拆分时加载第二个文件。

| 品类判断 | 读取文件 | 容易混淆的对象 |
|---|---|---|
| 大模型/专用模型 API、MaaS、模型聚合、推理服务 | [ai-model-services.md](categories/ai-model-services.md) | 底层模型厂商、云平台、聚合商、代理商、签约主体 |
| 企业 AI 编程助手、IDE 插件、代码智能平台 | [ai-coding-saas.md](categories/ai-coding-saas.md) | SaaS 产品、底层模型、代码托管平台、实施/培训服务 |
| 公有云、GPU/算力、IaaS/PaaS、托管推理基础设施 | [cloud-gpu.md](categories/cloud-gpu.md) | 云资源、模型调用、托管服务、专线/网络与软件许可 |
| CRM、协作、HR、财务、数据等企业订阅软件 | [enterprise-saas.md](categories/enterprise-saas.md) | 软件订阅、实施商、定制开发、增值支持 |
| 咨询、实施、开发、运维、外包、T&M 人力服务 | [it-professional-services.md](categories/it-professional-services.md) | 结果交付、工时采购、人员派驻和软件许可 |

## 混合项目拆分

把混合报价拆为可独立比较、验收和退出的组成项：

1. 产品/许可或 API 使用权；
2. 云/算力与网络资源；
3. 实施、集成、迁移和定制；
4. 运维、支持和客户成功；
5. 数据、模型、代码/IP 与退出服务。

分别确认每项的供应商主体、交付责任、计费单位、验收证据、SLA 和终止后义务。不要用一个“整体折扣”掩盖不可比单价或责任空白。
