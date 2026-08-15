import subprocess
import os
import sys

# 检查R环境
try:
    subprocess.run(["R", "--version"], capture_output=True, check=True)
except:
    print("错误：未找到R环境，请安装R并配置PATH。")
    sys.exit(1)

r_script = """
library(btergm)
library(igraph)
library(network)

years <- 2018:2023
networks <- list()
for (t in 1:length(years)) {
  edges <- read.csv(paste0("data/ICT-DE500_edges_", years[t], ".csv"), header=FALSE)
  g <- graph_from_edgelist(as.matrix(edges), directed=TRUE)
  # 显式设置节点数
  V(g)$name <- 1:500
  net <- asNetwork(g)
  # 设定网络大小
  net %v% "vertex.names" <- 1:500
  networks[[t]] <- net
}

# 模型公式：edges(边数) + mutual(互惠性) + gwesp(星形聚集/闭合三角效应)
# 对应论文 2.1 节 式(1) 中的 h(G^t, G^{t-1}) 统计向量
formula <- networks ~ edges + mutual + gwesp(0.1, fixed=TRUE)

# MCMC-MLE 估计，R=5000次迭代（论文建议>10000，此处为测试速度设为5000，可手动调高）
est <- btergm(formula, R=5000, parallel="snow", ncpus=2)

cat("\\n========== TERGM 估计结果 ==========\\n")
print(summary(est))

# 保存模型供后续分析
saveRDS(est, file="data/tergm_model.rds")
cat("模型已保存至 data/tergm_model.rds\\n")
"""

with open("temp_tergm.R", "w") as f:
    f.write(r_script)

try:
    subprocess.run(["Rscript", "temp_tergm.R"], check=True)
    print("TERGM 估计完成。")
except subprocess.CalledProcessError as e:
    print("R脚本执行失败，请检查 btergm 包是否安装。")
finally:
    os.remove("temp_tergm.R")