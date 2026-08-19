# Golden 回归基线

本目录是 it-sourcing-map 渲染链路的回归对照基线：`sample-small.json`（3 家厂商，节选 / 非完整市场扫描）与 `sample-large.json`（26 家厂商，大陆企业 16 家占严格多数，按大陆→海外补充→主体待核验排序）为符合 schema v3 的虚构演示数据，`sample-small.html` / `sample-large.html` 是由 `render_sourcing_report.py` 渲染并经 `qa_sourcing_report.py` 验收通过的对应输出。改动模板或渲染器后，用同一命令重新渲染两份 JSON，与本目录 HTML 做 diff 对比，并重新跑 QA，确认无非预期回归。
