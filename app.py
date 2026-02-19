from flask import Flask, render_template, request, jsonify
import json
import os
from collections import defaultdict, deque

app = Flask(__name__)

# File paths for persistence
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
LAYOUT_FILE = os.path.join(DATA_DIR, 'classroom_layout.json')
HISTORY_FILE = os.path.join(DATA_DIR, 'attendance_history.json')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# ================================================================
# DATA PERSISTENCE
# ================================================================

def save_layout(layout):
    with open(LAYOUT_FILE, 'w') as f:
        json.dump(layout, f, indent=2)

def load_layout():
    if os.path.exists(LAYOUT_FILE):
        with open(LAYOUT_FILE, 'r') as f:
            return json.load(f)
    return None

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {'sessions': [], 'neighbor_counts': {}}

# ================================================================
# NEIGHBOR-BASED PREDICTION ALGORITHM (HYBRID!)
# ================================================================

def get_neighbors(row, col, nodes):
    """Get adjacent students (up, down, left, right)"""
    neighbors = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for dr, dc in directions:
        nr, nc = row + dr, col + dc
        for node in nodes:
            if node.get('row') == nr and node.get('col') == nc:
                neighbors.append(node['name'])
    
    return neighbors

def update_neighbor_history(history, present_students, nodes):
    """
    Update neighbor co-occurrence counts.
    For each present student, record who was sitting near them.
    """
    if 'neighbor_counts' not in history:
        history['neighbor_counts'] = {}
    
    for node in nodes:
        if node['name'] in present_students:
            student = node['name']
            neighbors = get_neighbors(node['row'], node['col'], nodes)
            present_neighbors = [n for n in neighbors if n in present_students]
            
            if student not in history['neighbor_counts']:
                history['neighbor_counts'][student] = {}
            
            for neighbor in present_neighbors:
                if neighbor not in history['neighbor_counts'][student]:
                    history['neighbor_counts'][student][neighbor] = 0
                history['neighbor_counts'][student][neighbor] += 1
    
    return history

def predict_student_at_seat(row, col, present_neighbors, history, all_students):
    """
    PREDICTION ALGORITHM:
    Given present neighbors around a seat, predict who might sit there.
    
    P(student | neighbors) ∝ Σ (co-occurrence count with each neighbor)
    """
    predictions = {}
    neighbor_counts = history.get('neighbor_counts', {})
    
    for student in all_students:
        score = 0
        
        if student in neighbor_counts:
            for neighbor in present_neighbors:
                if neighbor in neighbor_counts[student]:
                    score += neighbor_counts[student][neighbor]
        
        for neighbor in present_neighbors:
            if neighbor in neighbor_counts:
                if student in neighbor_counts[neighbor]:
                    score += neighbor_counts[neighbor][student]
        
        if score > 0:
            predictions[student] = score
    
    total = sum(predictions.values()) if predictions else 1
    predictions = {k: round(v / total * 100, 1) for k, v in predictions.items()}
    
    sorted_predictions = sorted(predictions.items(), key=lambda x: -x[1])
    
    return sorted_predictions[:5]

# ================================================================
# SMART ROW DETECTION
# ================================================================

def smart_row_detection(nodes):
    if len(nodes) == 0:
        return nodes
    
    if len(nodes) == 1:
        nodes[0]['row'] = 0
        nodes[0]['col'] = 0
        return nodes
    
    sorted_by_y = sorted(nodes, key=lambda n: n['y'])
    
    y_gaps = []
    for i in range(1, len(sorted_by_y)):
        gap = sorted_by_y[i]['y'] - sorted_by_y[i-1]['y']
        y_gaps.append(gap)
    
    if len(y_gaps) > 0:
        min_y_gap = min(y_gaps) if min(y_gaps) > 5 else 20
        y_threshold = min_y_gap * 2.0
        y_threshold = max(y_threshold, 20)
        
        current_row = 0
        sorted_by_y[0]['row'] = 0
        
        for i in range(1, len(sorted_by_y)):
            if y_gaps[i-1] > y_threshold:
                current_row += 1
            sorted_by_y[i]['row'] = current_row
        
        for sn in sorted_by_y:
            for orig in nodes:
                if orig['id'] == sn['id']:
                    orig['row'] = sn['row']
    else:
        for n in nodes:
            n['row'] = 0
    
    rows = {}
    for n in nodes:
        r = n['row']
        if r not in rows:
            rows[r] = []
        rows[r].append(n)
    
    for r in rows:
        rows[r] = sorted(rows[r], key=lambda n: n['x'])
    
    ref_row_num = max(rows.keys(), key=lambda r: len(rows[r]))
    ref_row = rows[ref_row_num]
    
    for col_idx, node in enumerate(ref_row):
        for orig in nodes:
            if orig['id'] == node['id']:
                orig['col'] = col_idx
    
    ref_x_positions = [n['x'] for n in ref_row]
    
    for row_num, row_nodes in rows.items():
        if row_num == ref_row_num:
            continue
        
        for node in row_nodes:
            best_col = 0
            best_dist = float('inf')
            
            for col_idx, ref_x in enumerate(ref_x_positions):
                dist = abs(node['x'] - ref_x)
                if dist < best_dist:
                    best_dist = dist
                    best_col = col_idx
            
            for orig in nodes:
                if orig['id'] == node['id']:
                    orig['col'] = best_col
    
    for row_num, row_nodes in rows.items():
        row_cols = {}
        for node in sorted(row_nodes, key=lambda n: n['x']):
            for orig in nodes:
                if orig['id'] == node['id']:
                    col = orig['col']
                    while col in row_cols:
                        col += 1
                    orig['col'] = col
                    row_cols[col] = True
    
    return nodes

# ================================================================
# UNION-FIND
# ================================================================

class UnionFind:
    def __init__(self, elements):
        self.parent = {e: e for e in elements}
        self.rank = {e: 0 for e in elements}
    
    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self.rank[rx] < self.rank[ry]:
            self.parent[rx] = ry
        elif self.rank[rx] > self.rank[ry]:
            self.parent[ry] = rx
        else:
            self.parent[ry] = rx
            self.rank[rx] += 1
        return True

# ================================================================
# BUILD EDGES
# ================================================================

def build_edges(nodes):
    edges = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    node_map = {}
    for n in nodes:
        node_map[(n.get('row', 0), n.get('col', 0))] = n
    
    for node in nodes:
        r, c = node.get('row', 0), node.get('col', 0)
        for dr, dc in directions:
            neighbor = node_map.get((r + dr, c + dc))
            if neighbor and neighbor['id'] > node['id']:
                edges.append({
                    'from': node['id'],
                    'to': neighbor['id'],
                    'weight': 1
                })
    
    return edges

# ================================================================
# KRUSKAL'S MST
# ================================================================

def kruskal_mst(nodes, edges):
    steps = []
    mst = []
    total = 0
    
    if len(nodes) < 2:
        return [], [], 0
    
    steps.append({'step': 0, 'action': 'INIT', 'detail': f'{len(nodes)} nodes, {len(edges)} edges'})
    
    uf = UnionFind([n['id'] for n in nodes])
    step = 1
    
    for edge in edges:
        fn = next((n['name'] for n in nodes if n['id'] == edge['from']), '?')
        tn = next((n['name'] for n in nodes if n['id'] == edge['to']), '?')
        
        if uf.union(edge['from'], edge['to']):
            mst.append(edge)
            total += 1
            steps.append({'step': step, 'action': 'ADD', 'detail': f'{fn} — {tn} ✓'})
            if len(mst) == len(nodes) - 1:
                break
        else:
            steps.append({'step': step, 'action': 'SKIP', 'detail': f'{fn} — {tn} (cycle)'})
        step += 1
    
    steps.append({'step': step, 'action': 'DONE', 'detail': f'MST weight: {total}'})
    return mst, steps, total

# ================================================================
# DIJKSTRA
# ================================================================

def dijkstra(nodes, edges, source_id):
    steps = []
    
    if not source_id or len(nodes) < 1:
        return {}, {}, [], []
    
    adj = {n['id']: [] for n in nodes}
    for e in edges:
        adj[e['from']].append(e['to'])
        adj[e['to']].append(e['from'])
    
    dist = {n['id']: float('inf') for n in nodes}
    prev = {n['id']: None for n in nodes}
    visited = set()
    dist[source_id] = 0
    
    sname = next((n['name'] for n in nodes if n['id'] == source_id), '?')
    steps.append({'step': 0, 'action': 'INIT', 'detail': f'Source: {sname}'})
    
    step = 1
    while len(visited) < len(nodes):
        min_d, min_n = float('inf'), None
        for n in nodes:
            if n['id'] not in visited and dist[n['id']] < min_d:
                min_d = dist[n['id']]
                min_n = n['id']
        
        if min_n is None:
            break
        
        visited.add(min_n)
        cname = next((n['name'] for n in nodes if n['id'] == min_n), '?')
        steps.append({'step': step, 'action': 'VISIT', 'detail': f'{cname} (d={dist[min_n]})'})
        step += 1
        
        for neighbor_id in adj[min_n]:
            if neighbor_id not in visited:
                new_d = dist[min_n] + 1
                if new_d < dist[neighbor_id]:
                    nname = next((n['name'] for n in nodes if n['id'] == neighbor_id), '?')
                    dist[neighbor_id] = new_d
                    prev[neighbor_id] = min_n
                    steps.append({'step': step, 'action': 'RELAX', 'detail': f'{nname}: {new_d}'})
                    step += 1
    
    steps.append({'step': step, 'action': 'DONE', 'detail': 'Complete'})
    path_edges = [{'from': prev[n], 'to': n} for n in prev if prev[n] is not None]
    
    return dist, prev, steps, path_edges

# ================================================================
# BFS
# ================================================================

def bfs_clusters(nodes, edges):
    steps = []
    clusters = []
    
    adj = {n['id']: [] for n in nodes}
    for e in edges:
        adj[e['from']].append(e['to'])
        adj[e['to']].append(e['from'])
    
    visited = set()
    step = 0
    cnum = 1
    
    for node in nodes:
        if node['id'] not in visited:
            cluster = []
            queue = [node['id']]
            
            while queue:
                curr = queue.pop(0)
                if curr not in visited:
                    visited.add(curr)
                    cluster.append(curr)
                    for nb in adj[curr]:
                        if nb not in visited:
                            queue.append(nb)
            
            clusters.append(cluster)
            names = [n['name'] for n in nodes if n['id'] in cluster]
            steps.append({'step': step, 'action': f'CLUSTER {cnum}', 'detail': ', '.join(names)})
            step += 1
            cnum += 1
    
    return clusters, steps

# ================================================================
# ATTENDANCE INFLUENCE NETWORK ALGORITHM
# ================================================================
# This combines multiple DSA algorithms:
# 1. Co-Absence Matrix (2D Array)
# 2. Weighted Graph Construction (Adjacency List)
# 3. Degree Centrality (Array counting)
# 4. Betweenness Centrality (BFS from all nodes)
# 5. Community Detection (BFS + Union-Find)
# 6. Influence Propagation (BFS with levels)
# 7. MST Backbone (Kruskal's Algorithm)
# ================================================================

def build_coabsence_matrix(history):
    """
    ALGORITHM 1: Build Co-Absence Correlation Matrix
    Data Structure: 2D Dictionary (simulating matrix)
    Time Complexity: O(S * N^2) where S = sessions, N = students
    
    For each pair of students, calculate how often they are absent together.
    """
    sessions = history.get('sessions', [])
    if len(sessions) < 2:
        return {}, {}, []
    
    # Get all unique students
    all_students = set()
    for session in sessions:
        present = set(session.get('present', []))
        # We need to know total students - get from first session or infer
        all_students.update(present)
    
    all_students = list(all_students)
    
    # Build absence records for each student
    # Data Structure: Dictionary mapping student -> list of session indices where absent
    absence_record = {student: [] for student in all_students}
    
    for idx, session in enumerate(sessions):
        present = set(session.get('present', []))
        for student in all_students:
            if student not in present:
                absence_record[student].append(idx)
    
    # Build Co-Absence Matrix
    # coabsence[A][B] = number of times A and B were both absent in same session
    coabsence = {s: {t: 0 for t in all_students} for s in all_students}
    
    for i, student_a in enumerate(all_students):
        for j, student_b in enumerate(all_students):
            if i < j:  # Only upper triangle (undirected)
                absent_a = set(absence_record[student_a])
                absent_b = set(absence_record[student_b])
                both_absent = len(absent_a.intersection(absent_b))
                coabsence[student_a][student_b] = both_absent
                coabsence[student_b][student_a] = both_absent
    
    return coabsence, absence_record, all_students


def calculate_correlation_score(student_a, student_b, coabsence, absence_record):
    """
    Calculate correlation score between two students.
    Formula: Score = (times_both_absent) / max(times_either_absent, 1)
    
    Range: 0.0 to 1.0 (1.0 = perfect correlation)
    """
    both_absent = coabsence.get(student_a, {}).get(student_b, 0)
    
    absent_a = len(absence_record.get(student_a, []))
    absent_b = len(absence_record.get(student_b, []))
    
    # Union of absences
    either_absent = len(set(absence_record.get(student_a, [])).union(
                       set(absence_record.get(student_b, []))))
    
    if either_absent == 0:
        return 0.0
    
    return round(both_absent / either_absent, 3)


def build_influence_graph(coabsence, absence_record, all_students, threshold=0.3):
    """
    ALGORITHM 2: Build Weighted Influence Graph
    Data Structure: Adjacency List with weights
    Time Complexity: O(N^2)
    
    Create edges between students with correlation > threshold
    Edge weight = correlation score
    """
    # Adjacency list: {student: [(neighbor, weight), ...]}
    adj_list = {student: [] for student in all_students}
    edges = []
    
    steps = []
    step = 0
    steps.append({'step': step, 'action': 'INIT', 'detail': f'Building graph for {len(all_students)} students'})
    step += 1
    
    for i, student_a in enumerate(all_students):
        for j, student_b in enumerate(all_students):
            if i < j:
                score = calculate_correlation_score(student_a, student_b, coabsence, absence_record)
                
                if score >= threshold:
                    adj_list[student_a].append((student_b, score))
                    adj_list[student_b].append((student_a, score))
                    edges.append({
                        'from': student_a,
                        'to': student_b,
                        'weight': score
                    })
                    steps.append({
                        'step': step, 
                        'action': 'EDGE', 
                        'detail': f'{student_a} ↔ {student_b} (corr: {score})'
                    })
                    step += 1
    
    steps.append({'step': step, 'action': 'DONE', 'detail': f'Graph: {len(edges)} edges'})
    
    return adj_list, edges, steps


def calculate_degree_centrality(adj_list, all_students):
    """
    ALGORITHM 3: Degree Centrality
    Data Structure: Dictionary
    Time Complexity: O(N)
    
    Degree Centrality = number of connections / (total_nodes - 1)
    Higher = more connected = more influential
    """
    centrality = {}
    n = len(all_students)
    
    for student in all_students:
        degree = len(adj_list.get(student, []))
        # Normalize: divide by max possible connections
        centrality[student] = round(degree / max(n - 1, 1), 3)
    
    return centrality


def calculate_betweenness_centrality(adj_list, all_students):
    """
    ALGORITHM 4: Betweenness Centrality using BFS
    Data Structure: Queue (BFS), Dictionary
    Time Complexity: O(N * (N + E))
    
    Betweenness = how often a student lies on shortest path between others
    Uses BFS to find all shortest paths
    """
    betweenness = {student: 0 for student in all_students}
    
    for source in all_students:
        # BFS from source
        queue = deque([source])
        dist = {source: 0}
        paths = {source: 1}  # Number of shortest paths to each node
        pred = {s: [] for s in all_students}  # Predecessors on shortest paths
        
        # Forward BFS
        while queue:
            curr = queue.popleft()
            for neighbor, weight in adj_list.get(curr, []):
                # First time visiting
                if neighbor not in dist:
                    dist[neighbor] = dist[curr] + 1
                    queue.append(neighbor)
                
                # Found a shortest path
                if dist.get(neighbor, float('inf')) == dist[curr] + 1:
                    paths[neighbor] = paths.get(neighbor, 0) + paths[curr]
                    pred[neighbor].append(curr)
        
        # Backward accumulation
        dependency = {s: 0 for s in all_students}
        
        # Process nodes in reverse BFS order (by distance)
        nodes_by_dist = sorted(dist.keys(), key=lambda x: dist.get(x, 0), reverse=True)
        
        for node in nodes_by_dist:
            for p in pred[node]:
                # Fraction of shortest paths through p
                fraction = paths.get(p, 1) / max(paths.get(node, 1), 1)
                dependency[p] += fraction * (1 + dependency[node])
            
            if node != source:
                betweenness[node] += dependency[node]
    
    # Normalize
    n = len(all_students)
    norm = max((n - 1) * (n - 2), 1)
    
    for student in betweenness:
        betweenness[student] = round(betweenness[student] / norm, 3)
    
    return betweenness


def detect_influence_communities(adj_list, all_students):
    """
    ALGORITHM 5: Community Detection using BFS
    Data Structure: Queue, Set, Union-Find concept
    Time Complexity: O(N + E)
    
    Find groups of students who influence each other
    """
    visited = set()
    communities = []
    
    for student in all_students:
        if student not in visited:
            # BFS to find all connected students
            community = []
            queue = deque([student])
            
            while queue:
                curr = queue.popleft()
                if curr not in visited:
                    visited.add(curr)
                    community.append(curr)
                    
                    for neighbor, weight in adj_list.get(curr, []):
                        if neighbor not in visited:
                            queue.append(neighbor)
            
            if community:
                communities.append(community)
    
    return communities


def calculate_influence_propagation(adj_list, source_student, all_students):
    """
    ALGORITHM 6: Influence Propagation using BFS with Levels
    Data Structure: Queue with level tracking
    Time Complexity: O(N + E)
    
    Starting from an influencer, how does absence spread?
    Returns levels showing propagation depth
    """
    if source_student not in all_students:
        return {}, []
    
    # BFS with level tracking
    levels = {source_student: 0}
    queue = deque([(source_student, 0)])
    propagation_steps = []
    
    propagation_steps.append({
        'level': 0,
        'student': source_student,
        'probability': 100
    })
    
    while queue:
        curr, level = queue.popleft()
        
        for neighbor, weight in adj_list.get(curr, []):
            if neighbor not in levels:
                levels[neighbor] = level + 1
                # Probability decreases with distance
                prob = round(weight * 100 * (0.7 ** level), 1)
                
                propagation_steps.append({
                    'level': level + 1,
                    'student': neighbor,
                    'probability': prob
                })
                
                queue.append((neighbor, level + 1))
    
    return levels, propagation_steps


def influence_mst_backbone(edges, all_students):
    """
    ALGORITHM 7: MST of Influence Network (Kruskal's)
    Data Structure: Union-Find
    Time Complexity: O(E log E)
    
    Find the minimum connections that explain maximum influence
    We use MAXIMUM spanning tree (sort descending) to keep strongest connections
    """
    if not edges:
        return [], []
    
    # Sort by weight DESCENDING (we want strongest connections)
    sorted_edges = sorted(edges, key=lambda e: e['weight'], reverse=True)
    
    # Union-Find
    parent = {s: s for s in all_students}
    rank = {s: 0 for s in all_students}
    
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x, y):
        rx, ry = find(x), find(y)
        if rx == ry:
            return False
        if rank[rx] < rank[ry]:
            parent[rx] = ry
        elif rank[rx] > rank[ry]:
            parent[ry] = rx
        else:
            parent[ry] = rx
            rank[rx] += 1
        return True
    
    mst_edges = []
    steps = []
    step = 0
    
    for edge in sorted_edges:
        if union(edge['from'], edge['to']):
            mst_edges.append(edge)
            steps.append({
                'step': step,
                'action': 'ADD',
                'detail': f"{edge['from']} — {edge['to']} (w={edge['weight']})"
            })
            step += 1
            
            if len(mst_edges) == len(all_students) - 1:
                break
    
    return mst_edges, steps


def calculate_influence_score(student, degree_cent, between_cent, absence_record):
    """
    COMBINED INFLUENCE SCORE
    Formula: Score = (DegreeCentrality * 40) + (BetweennessCentrality * 40) + (AbsenceRate * 20)
    
    Weights can be adjusted based on what matters more
    """
    degree = degree_cent.get(student, 0)
    between = between_cent.get(student, 0)
    
    # Absence rate
    total_sessions = max(len(absence_record.get(list(absence_record.keys())[0], [])) if absence_record else 1, 1)
    absence_rate = len(absence_record.get(student, [])) / 10  # Normalize
    
    score = (degree * 40) + (between * 40) + (absence_rate * 20)
    
    return round(score, 2)


def run_influence_network_analysis(history):
    """
    MAIN FUNCTION: Run complete Influence Network Analysis
    Combines all 7 algorithms
    """
    results = {
        'success': False,
        'error': None,
        'students': [],
        'influence_graph': {'nodes': [], 'edges': []},
        'influencers': [],
        'communities': [],
        'mst_backbone': [],
        'steps': [],
        'stats': {}
    }
    
    sessions = history.get('sessions', [])
    
    if len(sessions) < 3:
        results['error'] = f'Need at least 3 attendance sessions for analysis. Currently have: {len(sessions)}'
        return results
    
    # Step 1: Build Co-Absence Matrix
    coabsence, absence_record, all_students = build_coabsence_matrix(history)
    
    if len(all_students) < 2:
        results['error'] = 'Need at least 2 students for analysis'
        return results
    
    results['students'] = all_students
    
    # Step 2: Build Influence Graph
    adj_list, edges, graph_steps = build_influence_graph(
        coabsence, absence_record, all_students, threshold=0.2
    )
    results['influence_graph']['edges'] = edges
    results['steps'].extend(graph_steps)
    
    # Step 3: Calculate Degree Centrality
    degree_cent = calculate_degree_centrality(adj_list, all_students)
    
    # Step 4: Calculate Betweenness Centrality
    between_cent = calculate_betweenness_centrality(adj_list, all_students)
    
    # Step 5: Detect Communities
    communities = detect_influence_communities(adj_list, all_students)
    results['communities'] = communities
    
    # Step 6: Calculate combined influence scores
    influence_scores = {}
    for student in all_students:
        influence_scores[student] = calculate_influence_score(
            student, degree_cent, between_cent, absence_record
        )
    
    # Build node data with all metrics
    for student in all_students:
        absence_count = len(absence_record.get(student, []))
        node_data = {
            'name': student,
            'degree_centrality': degree_cent.get(student, 0),
            'betweenness_centrality': between_cent.get(student, 0),
            'influence_score': influence_scores.get(student, 0),
            'absences': absence_count,
            'absence_rate': round(absence_count / len(sessions) * 100, 1)
        }
        results['influence_graph']['nodes'].append(node_data)
    
    # Step 7: Find top influencers
    sorted_by_influence = sorted(
        results['influence_graph']['nodes'],
        key=lambda x: x['influence_score'],
        reverse=True
    )
    results['influencers'] = sorted_by_influence[:5]
    
    # Step 8: MST Backbone
    mst_edges, mst_steps = influence_mst_backbone(edges, all_students)
    results['mst_backbone'] = mst_edges
    results['steps'].extend(mst_steps)
    
    # Step 9: Calculate propagation for top influencer
    if results['influencers']:
        top_influencer = results['influencers'][0]['name']
        levels, prop_steps = calculate_influence_propagation(adj_list, top_influencer, all_students)
        results['propagation'] = {
            'source': top_influencer,
            'levels': levels,
            'steps': prop_steps
        }
    
    # Stats
    results['stats'] = {
        'total_students': len(all_students),
        'total_sessions': len(sessions),
        'total_edges': len(edges),
        'communities_count': len(communities),
        'avg_connections': round(sum(len(adj_list[s]) for s in all_students) / max(len(all_students), 1), 2)
    }
    
    results['success'] = True
    return results

# ================================================================
# ROUTES
# ================================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/convert_and_run', methods=['POST'])
def convert_and_run():
    try:
        data = request.get_json()
        nodes = data.get('nodes', [])
        source_id = data.get('source_id')
        present_only = data.get('present_only', [])  # List of present student names
        
        # If present_only filter is provided, filter nodes to only present students
        if present_only and len(present_only) > 0:
            nodes = [n for n in nodes if n['name'] in present_only]
        
        nodes = smart_row_detection(nodes)
        
        max_row = max([n.get('row', 0) for n in nodes], default=0)
        max_col = max([n.get('col', 0) for n in nodes], default=0)
        
        edges = build_edges(nodes)
        mst, kruskal_steps, mst_weight = kruskal_mst(nodes, edges)
        dist, prev, dijkstra_steps, path_edges = dijkstra(nodes, edges, source_id)
        clusters, bfs_steps = bfs_clusters(nodes, edges)
        
        dist_json = {str(k): (v if v != float('inf') else '∞') for k, v in dist.items()}
        
        return jsonify({
            'nodes_with_grid': nodes,
            'grid_size': {'rows': max_row + 1, 'cols': max_col + 1},
            'edges': edges,
            'kruskal': {'mst_edges': mst, 'steps': kruskal_steps, 'total_weight': mst_weight},
            'dijkstra': {'distances': dist_json, 'steps': dijkstra_steps, 'path_edges': path_edges},
            'bfs': {'clusters': clusters, 'steps': bfs_steps}
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/save_layout', methods=['POST'])
def api_save_layout():
    try:
        data = request.get_json()
        save_layout(data)
        return jsonify({'success': True, 'message': 'Layout saved!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load_layout', methods=['GET'])
def api_load_layout():
    try:
        layout = load_layout()
        if layout:
            return jsonify({'success': True, 'layout': layout})
        else:
            return jsonify({'success': False, 'message': 'No saved layout found'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/save_attendance', methods=['POST'])
def api_save_attendance():
    try:
        data = request.get_json()
        nodes = data.get('nodes', [])
        present_students = data.get('present', [])
        date = data.get('date', 'unknown')
        
        history = load_history()
        
        history['sessions'].append({
            'date': date,
            'present': present_students,
            'total': len(nodes)
        })
        
        history = update_neighbor_history(history, present_students, nodes)
        save_history(history)
        
        return jsonify({
            'success': True, 
            'message': f'Attendance saved! {len(present_students)}/{len(nodes)} present',
            'sessions_count': len(history['sessions'])
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def api_predict():
    try:
        data = request.get_json()
        row = data.get('row')
        col = data.get('col')
        nodes = data.get('nodes', [])
        present_students = data.get('present', [])
        
        present_neighbors = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            for node in nodes:
                if node.get('row') == nr and node.get('col') == nc:
                    if node['name'] in present_students:
                        present_neighbors.append(node['name'])
        
        history = load_history()
        all_students = [n['name'] for n in nodes if n['name'] not in present_students]
        predictions = predict_student_at_seat(row, col, present_neighbors, history, all_students)
        
        return jsonify({
            'success': True,
            'predictions': predictions,
            'neighbors': present_neighbors,
            'history_sessions': len(history.get('sessions', []))
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_history', methods=['GET'])
def api_get_history():
    try:
        history = load_history()
        return jsonify({
            'success': True,
            'sessions': history.get('sessions', []),
            'total_sessions': len(history.get('sessions', [])),
            'neighbor_data': len(history.get('neighbor_counts', {}))
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear_history', methods=['POST'])
def api_clear_history():
    try:
        save_history({'sessions': [], 'neighbor_counts': {}})
        return jsonify({'success': True, 'message': 'History cleared!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/influence_network', methods=['GET'])
def api_influence_network():
    """
    API Endpoint for Attendance Influence Network Analysis
    
    Combines 7 DSA algorithms:
    1. Co-Absence Matrix (2D Array)
    2. Weighted Graph Construction (Adjacency List)
    3. Degree Centrality (Counting)
    4. Betweenness Centrality (BFS from all nodes)
    5. Community Detection (BFS)
    6. Influence Propagation (BFS with levels)
    7. MST Backbone (Kruskal's with Union-Find)
    """
    try:
        history = load_history()
        results = run_influence_network_analysis(history)
        return jsonify(results)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/influence_propagation', methods=['POST'])
def api_influence_propagation():
    """
    Get influence propagation from a specific student
    """
    try:
        data = request.get_json()
        source_student = data.get('student')
        
        history = load_history()
        coabsence, absence_record, all_students = build_coabsence_matrix(history)
        adj_list, edges, _ = build_influence_graph(coabsence, absence_record, all_students, threshold=0.2)
        
        levels, prop_steps = calculate_influence_propagation(adj_list, source_student, all_students)
        
        return jsonify({
            'success': True,
            'source': source_student,
            'propagation': prop_steps,
            'max_depth': max(levels.values()) if levels else 0
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  SMART ATTENDANCE SYSTEM")
    print("  • Save/Load Layout  • Attendance Mode  • AI Prediction")
    print("  Open: http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, port=5000)
