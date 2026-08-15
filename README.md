# 数字生态系统韧性分析 – 复现数据与脚本

本仓库配套论文《Structural Evolution and Resilience of Digital Economy Ecosystems Based on Complex Networks》，提供从 Crunchbase 全球企业投融资数据库筛选出的 **ICT-DE500** 核心子集（2018‑2023年）的脱敏拓扑数据，以及 TERGM 动态演化估计与级联故障仿真脚本。

## 数据说明
- **数据来源**：基于 Crunchbase 公开数据集，聚焦信息通信技术（ICT）与数字经济领域，提取 2018‑2023 年间互连最活跃的 500 个核心企业节点（ICT‑DE500 子集）。
- **数据结构**：
  - 年度有向边列表（`ICT-DE500_edges_YYYY.csv`）：每行代表一笔战略投资或并购形成的资本/数据流，方向体现控制或业务依赖关系。
  - 节点属性表（`data/ICT-DE500.xlsx`）：包含企业节点的总度（`degree_total`）和介数中心性（`betweenness`），用于校准初始负载与攻击目标排序。
- **统计特征**：数据保留了原始网络的幂律度分布、高互惠性及局部聚集效应，与论文图3、图5所示特征一致。

## 脚本说明
| 脚本文件 | 功能描述 |
| :--- | :--- |
| `tergm_estimation.py` | 调用 R 的 `btergm` 包，对时序网络估计 TERGM 参数（模型公式：`edges + mutual + gwesp`），输出系数与显著性。 |
| `cascade_simulation.py` | 实现改进的 Motter‑Lai 算法（算法1），模拟基于介数中心性的定点攻击，追踪最大连通分量（LCC）和全局效率（E）的衰减。 |

## 环境配置

**Python 依赖**：
```bash
pip install -r requirements.txt
