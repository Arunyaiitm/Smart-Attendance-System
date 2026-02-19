# Smart-Attendance-System
Smart Attendance System using Graph Algorithms - DSA Project
# 🎓 Smart Attendance System Using Graph Algorithms

> A novel approach to analyzing classroom attendance patterns by modeling seating arrangements as graphs and combining 7 DSA algorithms to identify socially influential students.

![Python](https://img.shields.io/badge/Python-3.x-blue?style=flat&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-green?style=flat&logo=flask)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat)
![Status](https://img.shields.io/badge/Status-Completed-success?style=flat)

---

## 📌 Problem Statement

**Question:** Can we use graph algorithms to analyze classroom attendance and find "influencer" students whose absence causes others to skip?

**Key Insight:** A classroom naturally forms a graph!
- Each **student** = Node
- **Adjacent seats** (up, down, left, right) = Edges
- **Attendance patterns** = Graph properties to analyze

---

## ✨ Features

- 🖱️ **Interactive Setup** - Click to add students on classroom image
- 📊 **Graph Visualization** - See MST, shortest paths, and clusters
- 🔍 **Influence Analysis** - Find top influential students
- 👥 **Community Detection** - Identify friend groups
- 📈 **Cascade Prediction** - Predict attendance spread
- 💾 **Data Persistence** - Save/load classroom layouts

---

## 🧠 Algorithms Implemented

| # | Algorithm | Type | Time Complexity | Space |
|---|-----------|------|-----------------|-------|
| 1 | Smart Row Detection | Sorting | O(n log n) | O(n) |
| 2 | Union-Find | DSU | O(α(n)) ≈ O(1) | O(n) |
| 3 | Kruskal's MST | Greedy | O(E log E) | O(V) |
| 4 | Dijkstra's | Shortest Path | O(V²) | O(V) |
| 5 | BFS Clustering | Traversal | O(V + E) | O(V) |
| 6 | Betweenness Centrality | Graph Analysis | O(N(N+E)) | O(N) |
| 7 | Influence Propagation | Modified BFS | O(N + E) | O(N) |

---

## 📦 Data Structures Used

```
📂 Data Structures
├── Dictionary (HashMap)  → Union-Find parents, Adjacency List   → O(1) lookup
├── Set                   → Visited node tracking                → O(1) membership
├── Deque                 → BFS queue operations                 → O(1) popleft
├── List                  → Storing nodes, edges, steps          → O(1) append
└── 2D Dictionary         → Co-absence correlation matrix        → O(1) access
```

---

## 💡 My Novel Contributions

### 🔄 Modification 1: Maximum Spanning Tree

| Standard Kruskal's | My Modification |
|-------------------|-----------------|
| Sort edges **ASCENDING** | Sort edges **DESCENDING** |
| Finds **minimum** weight | Finds **maximum** weight |
| Gets weakest connections | Gets **strongest friendships!** |

```python
# Standard: sorted(edges, key=lambda e: e['weight'])
# Mine:
sorted_edges = sorted(edges, key=lambda e: e['weight'], reverse=True)
```

### 🔄 Modification 2: Probabilistic BFS

| Standard BFS | My Modification |
|--------------|-----------------|
| Output: Reachable? Yes/No | Output: Probability % |
| All nodes equal | Decay with distance |

```python
# My Formula:
P = weight × 0.7^level

# Result:
# Level 1 (direct friend)    = 70%
# Level 2 (friend of friend) = 49%
# Level 3                    = 34%
```

### 📊 Combined Influence Score

```
Score = (Degree × 40) + (Betweenness × 40) + (AbsenceRate × 20)
```

---

## 🛠️ Installation

### Prerequisites
- Python 3.x
- pip (Python package manager)

### Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/Smart-Attendance-System.git

# Navigate to project folder
cd Smart-Attendance-System

# Install dependencies
pip install flask

# Run the application
python app.py
```

### Open in Browser
```
http://localhost:5000
```

---

## 🚀 How to Use

### 1️⃣ Setup Mode
- Click on the classroom area to add students
- Enter student names when prompted
- System automatically detects rows and columns

### 2️⃣ Algorithm Mode
- Click **"Run All"** to execute MST, Dijkstra, and BFS
- Watch step-by-step animation
- View algorithm logs in the panel

### 3️⃣ Attendance Mode
- Click students to mark Present (green) / Absent (red)
- Save attendance sessions
- Algorithms run on present students only

### 4️⃣ Influence Mode
- Click **"Analyze Network"** after 3+ attendance sessions
- View top influencers ranked by score
- See communities and influence graph

---

## 📁 Project Structure

```
Smart-Attendance-System/
│
├── app.py                 # Main Flask backend (700+ lines)
│   ├── UnionFind class    # With path compression & union by rank
│   ├── kruskal_mst()      # Minimum Spanning Tree
│   ├── dijkstra()         # Shortest path algorithm
│   ├── bfs_clusters()     # Connected components
│   └── influence_network  # 7-algorithm pipeline
│
├── templates/
│   └── index.html         # Frontend UI (2000+ lines)
│
├── data/
│   ├── classroom_layout.json    # Saved student positions
│   └── attendance_history.json  # Attendance records
│
└── README.md
```

---

## 📊 Results

| Metric | Result |
|--------|--------|
| Cascade Prediction Accuracy | **70-80%** |
| Processing Time (10 students) | **< 50ms** |
| Union-Find Optimization | 5-6 → **1-2 traversals** |
| Community Detection | Matches real friend groups |

---

## 🔮 Future Improvements

- [ ] Face recognition for automatic attendance
- [ ] Priority queue for O((V+E) log V) Dijkstra
- [ ] Louvain algorithm for better community detection
- [ ] Machine learning for attendance prediction
- [ ] Mobile app version

---

## 📚 References

1. Cormen, T. H., et al. *Introduction to Algorithms*, MIT Press, 3rd ed., 2009.
2. Newman, M. *Networks: An Introduction*, Oxford University Press, 2010.

---
  
