import networkx as nx
import pandas as pd
import numpy as np

# ========== 参数设置（与论文表1完全对应）==========
N = 500
LAMBDA = 0.5  # 均衡权重因子（λ）
BETA = 1.25  # 负载非线性指数（β），可调 [1.0, 1.5]
ALPHA = 0.3  # 容量容差（α），可调 >0
EPS_SINK = 1e-8  # 沉没项（算法1第15行）

# 读数据
edges = pd.read_csv("data/ICT-DE500_edges_2023.csv", header=None, names=["s", "t"])
G = nx.DiGraph()
G.add_edges_from(zip(edges["s"], edges["t"]))

attr = pd.read_csv("data/node_attributes.csv")
degree_total = attr["degree_total"].values
betweenness = attr["betweenness"].values

# 归一化（Min-Max）
deg_norm = (degree_total - degree_total.min()) / (degree_total.max() - degree_total.min() + EPS_SINK)
bet_norm = (betweenness - betweenness.min()) / (betweenness.max() - betweenness.min() + EPS_SINK)

# 式(2)：初始负载 L_i(0) = (λ*k~ + (1-λ)*B~)^β
L0 = np.power(LAMBDA * deg_norm + (1 - LAMBDA) * bet_norm, BETA)

# 式(3)：容量 C_i = (1+α) * L_i(0)
C = (1 + ALPHA) * L0

# 攻击顺序：按介数中心性降序
node_ids = attr["node_id"].values
sorted_nodes = sorted(zip(node_ids, betweenness), key=lambda x: -x[1])
attack_order = [int(n) for n, _ in sorted_nodes]


# ========== 算法1：改进的优先负载重分配引擎 ==========
def run_cascade(G, L0, C, initial_failed):
    idx_map = {node: i for i, node in enumerate(G.nodes())}
    load = {node: float(L0[idx_map[node]]) for node in G.nodes()}
    cap = {node: float(C[idx_map[node]]) for node in G.nodes()}

    active = set(G.nodes()) - set(initial_failed)
    failed = set(initial_failed)
    tau = 0

    while failed and tau < 1000:
        next_failed = set()
        # 计算本轮每个失败节点转移的负载
        for i in failed:
            Li = load.get(i, 0)
            neighbors = list(G.successors(i))
            active_neighbors = [j for j in neighbors if j in active]
            if not active_neighbors:
                continue  # 负载溢出系统（沉没）

            # 计算各存活邻居的剩余容量 ΔC_j
            delta_C = {}
            total_delta = 0.0
            for j in active_neighbors:
                rem = max(cap[j] - load[j], 0.0)
                delta_C[j] = rem
                total_delta += rem
            if total_delta == 0:
                continue  # 所有邻居满载，负载丢失

            # 式(4)：分配权重
            for j in active_neighbors:
                w = delta_C[j] / (total_delta + EPS_SINK)
                load[j] += w * Li  # 式(5)：更新负载

        # 并行检查超载（算法1第19-30行）
        for j in active:
            if load[j] > cap[j] + 1e-9:
                next_failed.add(j)

        # 更新状态
        active -= next_failed
        failed = next_failed
        tau += 1

    return active, load


# ========== 主仿真：追踪最大连通分量与全局效率 ==========
removal_ratios = []
S_LCC_list = []
E_global_list = []

max_steps = int(0.5 * N)
for step in range(1, max_steps + 1):
    initial_failed = attack_order[:step]
    active_set, final_load = run_cascade(G, L0, C, initial_failed)

    # 式(6)：最大连通分量相对规模 S_LCC
    subG = G.subgraph(active_set)
    if subG.number_of_nodes() > 0:
        comps = list(nx.weakly_connected_components(subG))
        largest = max(len(c) for c in comps) if comps else 0
        S_lcc = largest / N
    else:
        S_lcc = 0
    S_LCC_list.append(S_lcc)

    # 式(7)：全局传输效率 E(τ)（分母为 N(N-1)）
    if len(active_set) > 1:
        eff_sum = 0.0
        # 为防止大规模全遍历耗时，若活动节点>300则随机采样200对加快速度（但此处保留精确计算，N=500可接受）
        for i in active_set:
            for j in active_set:
                if i == j: continue
                try:
                    d = nx.shortest_path_length(subG, source=i, target=j)
                    eff_sum += 1.0 / d
                except nx.NetworkXNoPath:
                    continue
        E = eff_sum / (N * (N - 1))
    else:
        E = 0.0
    E_global_list.append(E)

    removal_ratios.append(step / N)
    if step % 10 == 0:
        print(f"移除节点 {step}/{N}，LCC={S_lcc:.4f}，E={E:.4f}")

# 保存结果
results = pd.DataFrame({
    "removal_ratio": removal_ratios,
    "S_LCC": S_LCC_list,
    "E_global": E_global_list
})
results.to_csv("data/cascade_results.csv", index=False)
print("级联仿真完成，结果保存至 cascade_results.csv")