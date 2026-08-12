# IT 采购助理 Skill 审视报告
## ——基于 CIPS / CPPM 成熟采购视角

- 审视日期：2026-08-12
- 审视对象：`it-procurement-assistant`（commit `f07ba76`），含子技能 `it-sourcing-map`
- 审视目的：从成熟采购体系（CIPS、CPPM）出发，识别该 Skill 的优势、缺口与改进点，服务 IT 间接采购个人提效

---

## 一、这个 Skill 是做什么的

**一句话定位**：面向甲方 IT 间接采购（AI 模型/MaaS、AI Coding、云/GPU、企业 SaaS、IT 专业服务）的自然语言工作助理。用户描述问题或上传材料（需求书、报价、合同、周报、账单等），Agent 自动判断任务类型并交付可直接用于沟通、比较、谈判、审批、执行的结果。

### 1.1 架构

```
SKILL.md                    入口：交互纪律 + 内部路由（不向用户暴露流程）
├─ references/
│  ├─ operating-model.md    运行准则：证据账本 F/C/A/U、决策关口 G0–G7、
│  │                        职责边界(RACI)、门槛与评分分离、口径统一、自检
│  ├─ category-playbooks.md 品类路由 → categories/ 5 个品类手册
│  └─ workflows/01–13       13 个工作流：需求→市场→选型→寻源→POC→商务谈判
│                           →合同SLA→交付→验收→付款→绩效→续退→支出透视
├─ assets/                  底稿：公司政策占位、项目简报、决策备忘录、
│                           风险台账、评分表/TCO/支出/付款 CSV（仅表头）
├─ scripts/procurement_math.py   确定性计算：加权评分 score + 情景 TCO tco
└─ skills/it-sourcing-map/  子技能：需求文档→华为五看实时调研→供应商地图 HTML
```

### 1.2 设计哲学（值得注意的几个特点）

1. **"用户说需求，Agent 选方法"**：明确禁止让用户选模式/阶段/模板，路由全部在后台完成——这是效率导向的交互设计。
2. **证据纪律**：所有影响结论的信息标 `F事实 / C计算 / A假设 / U未验证`；"没查到"≠"无风险"；供应商自述标待验证。
3. **关口制（G0–G7）**：13 个工作流不是瀑布，而是可回退的证据检查；关口未过不用下游动作掩盖上游缺口。
4. **职责边界自觉**：采购输出"风险意见/审核建议"，不冒充法务意见、财务审批、技术验收、管理层批准；不发明"我方红线"。
5. **反伪精确**：不硬编码税率、抽样比例、通知期天数、供应商集中度阈值；要求低/基准/高三情景 + 敏感性分析。
6. **品类深度**：5 个品类手册写到 token 计数口径、席位"未活跃≠可回收"、GPU 标称卡时≠有效算力、T&M 重复报工这一级——超过多数通用采购框架的颗粒度。

---

## 二、对标框架说明

- **CIPS**（英国皇家采购与供应学会）：采购与供应周期（7 阶段模型；细分 13 阶段：规格定义、市场分析、供应策略、资格预审、招标文件、评标、供应商核验、授标、交付管理、合同绩效评审、SRM、资产管理、流程改进）[3](https://ramp.com/blog/procurement-process-lifecycle)；职业道德准则与利益冲突管理 [1](https://log.logcluster.org/sites/default/files/2022-09/CIPS%20Ethics%20Guide.pdf)；品类管理、Kraljic 矩阵、供应商分层的成熟实践 [4](https://wingswaytraining.com/how-can-you-implement-cips-procurement-practices-in-your-organisation/)；全生命周期成本（TCO）、价值工程、采购 KPI 体系 [4](https://wingswaytraining.com/how-can-you-implement-cips-procurement-practices-in-your-organisation/)。
- **CPPM**（美国采购协会 APS 注册职业采购经理，2005 年获中国人社部批准注册，劳引字〔2005〕001 号）：六大模块——供应商选择与评估、采购谈判技巧、采购合同管理（含修改/违约/争议解决）、供应链管理、采购成本管理、采购战略及风险控制（含内部控制与审计）[2](https://www.cppmrz.com/h-nd-544.html)。

---

## 三、映射对照：Skill 现状 vs 成熟框架

### 3.1 对 CIPS 采购周期

| CIPS 阶段 | Skill 对应 | 评估 |
|---|---|---|
| 1. 规格/需求定义 | 01-demand-strategy | ✅ 强：问题重写、P0 可测口径、解空间比较、供给策略 |
| 2. 市场分析 | 02-market-intelligence + it-sourcing-map | ✅ 强：研究协议、证据卡、五看 |
| 3. 供应策略 | 01/03 部分覆盖 | ⚠️ 缺品类策略文档与组合定位工具（见缺口 G3） |
| 4. 资格预审 | 04-sourcing-due-diligence | ✅ 主体拆分、准入预审登记做得细 |
| 5. 招标文件 | **无** | ❌ 缺 RFI/RFP/RFQ/资格预审问卷模板（缺口 G1） |
| 6. 评标 | 03/05 + procurement_math.py | ✅ 方法强；❌ 缺正式评标报告模板（缺口 G1） |
| 7. 供应商核验 | 04 尽调 | ✅ |
| 8. 授标 | decision-memo 底稿 | ⚠️ 有决策件，缺授标/谢绝通知（缺口 G1） |
| 9. 交付管理 | 08/09 | ✅ 强：RAG 状态有证据要求、验收与付款分离 |
| 10. 合同绩效评审 | 10-payment-control、11-supplier-performance | ✅ |
| 11. SRM | 11 部分覆盖 | ⚠️ 只有"测量绩效"，缺关系分层与治理（缺口 G2） |
| 12. 资产管理 | IT 间接采购多为订阅制，不适用 | 13 支出透视实际承担了类似职能 ✅ |
| 13. 流程改进 | 13-spend-analytics | ⚠️ 有机会池，缺 lessons-learned 闭环（缺口 G8） |

### 3.2 对 CPPM 六大模块

| CPPM 模块 | Skill 覆盖 | 短板 |
|---|---|---|
| 供应商选择与评估 | 03/04/05，含评分锚点、门槛分离 | 供应商**等级评定/分层管理**、关系冲突协调机制缺失 |
| 采购谈判技巧 | 06：BATNA、交换包、让步日志概念 | 无谈判计划/让步日志**模板资产**，落地靠 Agent 自由发挥 |
| 采购合同管理 | 07 签约前风险初审 | **签约后**管理弱：义务台账、变更台账、违约与争议处置（缺口 G4） |
| 供应链管理 | 02 供给地图、12 退出/连续性 | 需求管理流程、伙伴关系发展涉及较浅 |
| 采购成本管理 | 06 TCO + 脚本、13 支出透视 | 节省**验证与台账**缺失：基线、公式、一次性/经常性、cost avoidance 区分（缺口 G5） |
| 采购战略及风险控制 | 01 供给策略、operating-model 风险分级 | **内控与审计**视角、职业道德模板（利益冲突申报、礼品登记）缺失（缺口 G6） |

---

## 四、已经做得好的（保持）

1. **生命周期完整度高**：13 个工作流 ≈ CIPS 13 阶段模型，且包含多数工具只做到"签约"就停止的后半程（履约、验收、付款、绩效、续退、支出）。
2. **可审计性**：F/C/A/U 证据标签 + 来源定位 + 关口证据清单，直接满足 CIPS 强调的透明与问责 [1](https://log.logcluster.org/sites/default/files/2022-09/CIPS%20Ethics%20Guide.pdf)。
3. **TCO/单位经济性纪律**：低/基准/高情景、可比单位归一、"目录价折扣≠节省"——与 CIPS 全生命周期成本方法论一致。
4. **门槛与加权评分分离 + 敏感性分析**：避免"中间分掩盖缺证据"，这是很多评标实践中的真实病灶。
5. **职业边界伦理**：不越权、不发明红线、评标含利益冲突声明要求——与 CIPS 行为准则、CPPM 道德准则同向 [2](https://www.cppmrz.com/h-nd-544.html)。
6. **品类陷阱知识**：共享上游≠真双供、席位"回收候选"需多月验证、GPU 只锁价不锁容量风险等——属于一线踩坑经验，框架类材料通常没有。
7. **确定性计算与文档分离**：脚本只保证算术一致，不替代商业判断——工程上干净。

---

## 五、缺口清单（按提效价值排序）

### P0｜高频交付物缺失——每天都用、现在没有

**G1. RFx 与评标交付物模板族**（对应 CIPS 阶段 5/6/8；CPPM 供应商评估模块）
- 现状：03/04/05 有方法论，但 `assets/` 里没有可发出的 RFI/RFP/RFQ 模板、资格预审问卷、评标报告、授标/谢绝信。CIPS 实施指南明确把 RFP/RFQ 框架与评分矩阵列为结构化采购的核心动作 [4](https://wingswaytraining.com/how-can-you-implement-cips-procurement-practices-in-your-organisation/)。
- 影响：寻源阶段最耗时的"写文件"环节没有提效，用户仍要从零起草。
- 建议：新增 `assets/rfp-template.md`（含 IT 品类可裁剪章节：范围、P0 场景、报价表结构、SLA/数据/退出问卷）、`assets/evaluation-report.md`（门槛结果、评分、敏感性、推荐与授标建议）、`assets/supplier-letters.md`（授标、谢绝、澄清函、整改通知、升级函、终止/过渡通知）。

**G2. 谈判落地模板**（CPPM 模块二"如何制定谈判计划"）
- 现状：06 要求"一页谈判剧本、让步日志"，但无模板；让步价值、授权人、累计变化没有结构化载体，多轮谈判容易重复让步。
- 建议：`assets/negotiation-playbook.md`（目标位/可接受位/授权红线、议题全景、交换包、BATNA）+ `assets/concession-log.csv`（轮次、让步项、价值、换回条件、授权人、累计）。

**G5. 节省台账与收益实现**（CIPS KPI：cost savings achieved [4](https://wingswaytraining.com/how-can-you-implement-cips-procurement-practices-in-your-organisation/)）
- 现状：13 有"机会池"概念但无资产；节省如何验证（基线、公式、一次性 vs 经常性、cost avoidance vs hard saving）无规范。向领导汇报降本成绩时这是最常被挑战的点。
- 建议：`assets/savings-ledger.csv` + 在 13 中加"节省认定规则"小节；`procurement_math.py` 增加 `savings` 子命令（年度化、净现值可选、置信度加权）。

**G9. 付款对账工具**
- 现状：10-payment-control 描述了"合同—履约—账单—已付"四路匹配，但无脚本，全靠 Agent 手工推演，易错且不可复算。
- 建议：`procurement_math.py payment` 子命令：输入账单 CSV + 合同价目，输出差异项、重复项、累计已付核对。

### P1｜框架级缺口——决定专业上限

**G2b. SRM 从"绩效测量"升级为"关系管理"**（CIPS 阶段 11；CPPM"供应商等级评定与管理"）
- 现状：11 是打分与整改；没有供应商分层（战略/优选/交易）、QBR 议程模板、CAPA 模板、供应商发展/联合价值创造。
- 建议：11 增补"分层与治理节奏"小节；`assets/qbr-agenda.md`、`assets/capa-template.md`；供应商等级字段进 `supplier-evaluation.csv` 体系。

**G3. 品类策略与组合定位工具**（CIPS Category Management、Kraljic 矩阵 [4](https://wingswaytraining.com/how-can-you-implement-cips-procurement-practices-in-your-organisation/)）
- 现状：有品类"手册"（怎么买），没有品类"策略"（这类支出未来 1–3 年怎么经营）；没有支出×风险的组合定位来驱动差异化策略（杠杆→竞争性压价、瓶颈→保供去依赖、关键→伙伴关系、常规→流程自动化）。
- 建议：`assets/category-strategy.md` 模板（支出画像、供应市场、Kraljic 定位、策略主张、行动路线图），并在 01/03 路由中提示使用。

**G4. 签约后合同管理**（CIPS post-award administration [2](https://www.theknowledgeacademy.com/us/courses/cips-courses/)；CPPM 模块三"合同修改、违约和争议解决"）
- 现状：07 只管签约前；签约后的义务登记、关键日期、变更台账、违约/索赔/争议处置没有工作流。
- 建议：新增 `14-contract-administration.md`（义务台账、交付物/证书登记、变更与索赔、争议升级路径、到期提醒联动 12）+ `assets/obligation-register.csv`。

**G6. 职业道德与内控模板**（CIPS Code of Conduct、利益冲突 [1](https://log.logcluster.org/sites/default/files/2022-09/CIPS%20Ethics%20Guide.pdf)；CPPM 模块六"内部控制——控制和审计"）
- 现状：03 提到评委利益冲突声明，但无申报/礼品登记模板；无审计就绪（audit trail）清单。
- 建议：`assets/coi-declaration.md`；在 operating-model 增加"审计就绪"要求（每个决策可回溯到证据、评委、授权）。

**G10. 干系人管理**（CIPS 强调的内部客户管理）
- 现状：RACI 已有，但无干系人地图/参与计划模板——IT 采购推进受阻多数是内部阻力而非供应商问题。
- 建议：`assets/stakeholder-map.md`（影响力×态度、参与动作、沟通节奏），挂到 01。

### P2｜加分项与工程完善

- **G7. 跨境采购合规清单**：海外 SaaS/AI 采购常见的预提所得税、付汇/汇率、数据出境安全评估（个保法/数据安全法）、GPU/AI 出口管制筛查——目前散落在 07 的数据条款里，建议独立 `references/cross-border-it-checklist.md`。IT 间接采购买海外软件是常态，这是真实痛点。
- **G8. 知识沉淀闭环**：lessons-learned 模板 + "项目结束回写市场地图/供应商卡"的约定；it-sourcing-map 的五看产物与 02 的研究协议目前各写一套，建议统一 schema 复用。
- **G11. ESG/可持续采购视角**：CIPS 把道德与可持续采购嵌入周期首尾两阶段 [1](https://log.logcluster.org/sites/default/files/2022-09/CIPS%20Ethics%20Guide.pdf)。IT 视角落地：数据中心 PUE/绿电、供应商行为准则、负责任 AI 条款。可先作为 07 风险域清单中的一个可选项，不必重。
- **G12. 示例与上手引导**：`assets/` 全部为空表头、`company-policy.yaml` 全部"待填写"。设计意图正确（不硬编码），但建议给 1 份**带注释的示例数据**（放 `references/examples/`），显著提升 Agent 填表一致性和用户首次使用体验。
- **G13. 脚本扩展**：敏感性分析（权重/价格翻转阈值自动计算）、TCO 可选折现率（NPV）、FX 换算（带汇率日期字段）、席位回收节省测算。
- **G14. 采购职能 KPI 看板**：周期时长、合同合规率、节省达成率、供应商质量分——CIPS 推荐的职能级指标 [4](https://wingswaytraining.com/how-can-you-implement-cips-procurement-practices-in-your-organisation/)，可作为 13 的扩展输出。
- **G15. 版本管理**：Skill 无 changelog；dist zip 是二进制入库，建议构建脚本化（可复现打包）。

---

## 六、改进路线图（建议）

| 阶段 | 内容 | 预计工作量 | 提效收益 |
|---|---|---|---|
| 1 | G1 RFx/评标/信函模板族、G2 谈判模板、G5 节省台账、G9 付款脚本 | 小 | ★★★★★（覆盖日常最高频产出） |
| 2 | G2b SRM 三件套、G4 合同管理工作流、G10 干系人模板 | 中 | ★★★★ |
| 3 | G3 品类策略模板、G13 脚本扩展、G12 示例数据 | 中 | ★★★ |
| 4 | G7 跨境合规、G6 道德/内控、G8 知识闭环、G11/G14/G15 | 小-中 | ★★★ |

原则提醒：该 Skill 的核心设计纪律是"**不硬编码阈值、不发明红线、不冒充授权**"。补模板时应保持这一风格——模板提供结构与设计方法，数值留给公司制度/授权人填写。

---

## 七、结论

这个 Skill 在**流程骨架（13 阶段全覆盖）、证据纪律、TCO 方法、品类深度、职业伦理**五个方面已达到甚至超过 CIPS/CPPM 同类主题的通用要求；主要差距不在"方法论"，而在：

1. **交付物模板层**（RFx、评标报告、谈判/让步、信函）——方法有了，纸面武器没配齐；
2. **签约后到续约之间的合同与关系管理**（义务台账、SRM 分层、CAPA、争议处置）；
3. **价值证明层**（节省台账、收益实现、职能 KPI）——降本成果可验证性；
4. **本土与跨境合规细节**（数据出境、预提税、出口管制）与**道德内控模板**。

按第六节路线图逐阶段补齐后，该 Skill 可以从"高质量采购分析引擎"升级为"覆盖 Source-to-Pay 全流程的个人采购作业系统"。
