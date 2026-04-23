import networkx as nx
import plotly.graph_objects as go

# --------------------------------------------------
# 1. BASIC STRUCTURE
# --------------------------------------------------

tank_nodes = [f"T{i}" for i in range(28)]
field_nodes = [f"F{i}" for i in range(28)]
catchment_nodes = [f"C{i}" for i in range(28)]

G = nx.DiGraph()

# System nodes
G.add_node("Rainfall", layer="Rainfall")
G.add_node("Groundwater", layer="Groundwater")

for t in tank_nodes:
    G.add_node(t, layer="Tank")

for f in field_nodes:
    G.add_node(f, layer="Field")

for c in catchment_nodes:
    G.add_node(c, layer="Catchment")

# --------------------------------------------------
# 2. WEIGHTS
# --------------------------------------------------

rainfall_to_catchment_weight = 100

rainfall_to_tank_weights = {
    f"T{i}": 10 + i * 0.5 for i in range(28)
}

catchment_to_tank_weights = {
    f"T{i}": 0.7 + (i % 5) * 0.02 for i in range(28)
}

tank_to_gw_weights = {f"T{i}": 0.1 for i in range(28)}

field_to_gw_weights = {f"F{i}": 0.3 + (i % 10) * 0.005 for i in range(28)}

tank_to_field_weights = {
    f"T{i}": {f"F{i}": 30 + (i % 10)} for i in range(28)
}

# --------------------------------------------------
# 3. RAINFALL FLOWS
# --------------------------------------------------

for c in catchment_nodes:
    G.add_edge("Rainfall", c, weight=rainfall_to_catchment_weight)

for t, w in rainfall_to_tank_weights.items():
    G.add_edge("Rainfall", t, weight=w)

for i in range(28):
    G.add_edge(f"C{i}", f"T{i}", weight=catchment_to_tank_weights[f"T{i}"])

# --------------------------------------------------
# 4. TANK → FIELD + GROUNDWATER
# --------------------------------------------------

for t in tank_nodes:
    for f, w in tank_to_field_weights[t].items():
        G.add_edge(t, f, weight=w)

for t, w in tank_to_gw_weights.items():
    G.add_edge(t, "Groundwater", weight=w)

for f, w in field_to_gw_weights.items():
    G.add_edge(f, "Groundwater", weight=w)

# --------------------------------------------------
# 5. TANK → TANK INTERCONNECTIONS
# --------------------------------------------------

tank_connections = {
    "T15": [5, 7, 8, 9, 10, 12, 13, 14],
    "T18": [17],
    "T12": [11],
    "T5": [4, 3],
    "T7": [6],
    "T3": [2],
    "T2": [1],
    "T21": [20],
    "T23": [22]
}

main_out = [15, 16, 18, 20, 21, 23, 24, 25, 19]

for src in main_out:
    for tgt in main_out:
        if src != tgt:
            G.add_edge(f"T{src}", f"T{tgt}", weight=0.05)

for src, targets in tank_connections.items():
    for tgt in targets:
        G.add_edge(src, f"T{tgt}", weight=0.2)

# --------------------------------------------------
# 6. FLOW FUNCTIONS
# --------------------------------------------------

def node_inflow(node):
    return sum(G[u][node]["weight"] for u in G.predecessors(node))

# --------------------------------------------------
# 7. ANALYSIS
# --------------------------------------------------

betweenness = nx.betweenness_centrality(G, weight="weight")
critical_nodes = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:5]

tank_power = {}
for t in tank_nodes:
    tank_power[t] = sum(G[t][v]["weight"] for v in G.successors(t))

tank_inflow = {t: node_inflow(t) for t in tank_nodes}

gw_total = sum(G[u]["Groundwater"]["weight"] for u in G.predecessors("Groundwater"))

# --------------------------------------------------
# 8. PRINT RESULTS
# --------------------------------------------------

print("\nTop 5 Critical Nodes:")
for n, s in critical_nodes:
    print(n, round(s, 4))

print("\nTop Tank Power:")
for t, w in sorted(tank_power.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(t, round(w, 2))

print("\nTank Inflow Sample:")
for t in list(tank_nodes)[:10]:
    print(t, round(tank_inflow[t], 2))

print("\nTotal Groundwater Recharge:", round(gw_total, 2))

# --------------------------------------------------
# 9. ZIG-ZAG 3D VISUALIZATION (FIXED PART)
# --------------------------------------------------

pos = {}

# Tanks → ZIG-ZAG LAYOUT (MAIN FIX)
for i, t in enumerate(tank_nodes):
    x = i
    y = (i % 2) * 1.5   # zig-zag effect
    z = 3
    pos[t] = (x, y, z)

# Fields slightly above tanks
for i, f in enumerate(field_nodes):
    x = i
    y = 2 + (i % 2) * 0.8
    z = 2
    pos[f] = (x, y, z)

# Catchments below
for i, c in enumerate(catchment_nodes):
    x = i
    y = -2 - (i % 2) * 0.8
    z = 4
    pos[c] = (x, y, z)

# System nodes
pos["Rainfall"] = (14, 0, 5)
pos["Groundwater"] = (14, 0, 1)

# --------------------------------------------------
# 10. EDGE CREATION FOR PLOTLY
# --------------------------------------------------

edge_x, edge_y, edge_z = [], [], []

for u, v in G.edges():
    x0, y0, z0 = pos[u]
    x1, y1, z1 = pos[v]
    edge_x += [x0, x1, None]
    edge_y += [y0, y1, None]
    edge_z += [z0, z1, None]

node_x, node_y, node_z = [], [], []

for n in G.nodes():
    x, y, z = pos[n]
    node_x.append(x)
    node_y.append(y)
    node_z.append(z)

# --------------------------------------------------
# 11. PLOTLY VISUALIZATION
# --------------------------------------------------

fig = go.Figure()

fig.add_trace(go.Scatter3d(
    x=edge_x,
    y=edge_y,
    z=edge_z,
    mode="lines",
    line=dict(color="gray", width=2)
))

# Catchments
fig.add_trace(go.Scatter3d(
    x=[pos[n][0] for n in catchment_nodes],
    y=[pos[n][1] for n in catchment_nodes],
    z=[pos[n][2] for n in catchment_nodes],
    mode="markers+text",
    text=catchment_nodes,
    marker=dict(size=5, color="blue"),
    name="Catchments"
))

# Tanks
fig.add_trace(go.Scatter3d(
    x=[pos[n][0] for n in tank_nodes],
    y=[pos[n][1] for n in tank_nodes],
    z=[pos[n][2] for n in tank_nodes],
    mode="markers+text",
    text=tank_nodes,
    marker=dict(size=6, color="orange"),
    name="Tanks"
))

# Fields
fig.add_trace(go.Scatter3d(
    x=[pos[n][0] for n in field_nodes],
    y=[pos[n][1] for n in field_nodes],
    z=[pos[n][2] for n in field_nodes],
    mode="markers+text",
    text=field_nodes,
    marker=dict(size=5, color="green"),
    name="Fields"
))

# System nodes
fig.add_trace(go.Scatter3d(
    x=[pos["Rainfall"][0], pos["Groundwater"][0]],
    y=[pos["Rainfall"][1], pos["Groundwater"][1]],
    z=[pos["Rainfall"][2], pos["Groundwater"][2]],
    mode="markers+text",
    text=["Rainfall", "Groundwater"],
    marker=dict(size=8, color="red"),
    name="System"
))

fig.update_layout(
    title="Tank-Catchment Cascade System ",
    height=800,
    showlegend=False
)

fig.show()