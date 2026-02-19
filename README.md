# Smart-Attendance-System
Smart Attendance System using Graph Algorithms - DSA Project
# 🎓 Smart Attendance System Using Graph Algorithms

A DSA project that models classroom seating as a graph and uses 7 algorithms to analyze attendance patterns and find influential students.

## 📚 Algorithms Implemented

| Algorithm | Purpose | Time Complexity |
|-----------|---------|-----------------|
| Union-Find | Cycle detection | O(α(n)) ≈ O(1) |
| Kruskal's MST | Minimum connections | O(E log E) |
| Dijkstra's | Shortest path | O(V²) |
| BFS | Clustering | O(V+E) |
| Degree Centrality | Count connections | O(N) |
| Betweenness Centrality | Find bridges | O(N(N+E)) |
| Influence Propagation | Cascade modeling | O(N+E) |

## 🔧 My Modifications

1. **Maximum Spanning Tree** - Sort edges descending to find strongest bonds
2. **Probabilistic BFS** - Added decay: `P = weight × 0.7^level`

## 🚀 How to Run
```bash
pip install flask
python app.py
```

Then open: http://localhost:5000

## 👤 Author

- **Name:** Arunya

