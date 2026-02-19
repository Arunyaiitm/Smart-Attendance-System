"""
================================================================================
🎓 ATTENDANCE INFLUENCE NETWORK ALGORITHM
================================================================================
A HYBRID ALGORITHM combining 7 DSA concepts to discover hidden patterns 
in classroom attendance!

PROBLEM STATEMENT:
-----------------
"Some students are social influencers - when THEY skip class, their friend 
group also skips. Can we identify these key students using only attendance data?"

================================================================================
ALGORITHM BREAKDOWN
================================================================================

STEP 1: CO-ABSENCE MATRIX (2D Array)
------------------------------------
Data Structure: Dictionary of dictionaries (simulating 2D matrix)
Time Complexity: O(S × N²) where S = sessions, N = students

For each pair of students, count how often they were BOTH absent in the same 
session. This reveals hidden "friend groups" based on absence patterns.

Example:
         Day1  Day2  Day3  Day4  Day5
Rahul     ✗     ✓     ✗     ✓     ✗
Priya     ✗     ✓     ✗     ✓     ✗
Amit      ✓     ✗     ✓     ✗     ✓

Co-Absence Matrix:
        Rahul  Priya  Amit
Rahul     -      3      0
Priya     3      -      0
Amit      0      0      -

Result: Rahul and Priya are ALWAYS absent together (correlation = 3)!

--------------------------------------------------------------------------------

STEP 2: CORRELATION SCORE CALCULATION
-------------------------------------
Formula: Score(A,B) = (Times both absent) / (Times either was absent)

Range: 0.0 to 1.0 (1.0 = perfect correlation)

Example:
- Rahul absent 3 times, Priya absent 3 times
- Both absent together: 3 times
- Either absent: 3 times (same sessions)
- Score = 3/3 = 1.0 (Perfect correlation!)

--------------------------------------------------------------------------------

STEP 3: BUILD INFLUENCE GRAPH (Adjacency List)
----------------------------------------------
Data Structure: Dictionary {student: [(neighbor, weight), ...]}
Time Complexity: O(N²)

Create weighted edges between students with correlation > threshold (default 0.3)
Edge weight = correlation score

Example Graph:
    Rahul ═══════ Priya    (weight: 1.0 - very strong)
      │
      │ (0.4)
      │
    Amit ─────── Sneha     (weight: 0.35 - moderate)

--------------------------------------------------------------------------------

STEP 4: DEGREE CENTRALITY
-------------------------
Data Structure: Dictionary
Time Complexity: O(N)

Formula: Degree Centrality = connections / (total_students - 1)

Meaning: How many "absence buddies" does each student have?
Higher = more connected = more influential

Example:
- Rahul: 2 connections → 2/4 = 0.5
- Priya: 1 connection → 1/4 = 0.25
- Amit: 2 connections → 2/4 = 0.5

--------------------------------------------------------------------------------

STEP 5: BETWEENNESS CENTRALITY (BFS from all nodes)
---------------------------------------------------
Data Structure: Queue (BFS), Dictionary
Time Complexity: O(N × (N + E))

Meaning: How often does a student lie on the shortest path between others?
High betweenness = "bridge" between different friend groups

Algorithm:
1. Run BFS from each node
2. Count shortest paths through each intermediate node
3. Accumulate dependencies backward
4. Normalize by (n-1)(n-2)

Example:
If Sneha connects two separate friend groups:
  Group A ←→ Sneha ←→ Group B
  
Sneha has HIGH betweenness (she's the bridge!)

--------------------------------------------------------------------------------

STEP 6: COMMUNITY DETECTION (BFS)
---------------------------------
Data Structure: Queue, Set, Union-Find concept
Time Complexity: O(N + E)

Find connected components = friend groups who influence each other

Algorithm:
1. Start from unvisited node
2. BFS to find all connected students
3. Mark as one community
4. Repeat for remaining unvisited nodes

Example Result:
- Community 1: [Rahul, Priya, Amit] - always absent together
- Community 2: [Sneha, Neha] - different pattern
- Lone wolves: [Ananya] - no correlations

--------------------------------------------------------------------------------

STEP 7: INFLUENCE PROPAGATION (BFS with Levels)
-----------------------------------------------
Data Structure: Queue with level tracking
Time Complexity: O(N + E)

Question: If the #1 influencer is absent, who else might skip?

Algorithm:
1. BFS from influencer with level tracking
2. Probability decreases with distance: P = weight × 100 × (0.7^level)

Example:
Level 0: Rahul (SOURCE) - 100%
Level 1: Priya (90%), Amit (60%) - directly connected
Level 2: Sneha (40%) - connected through Amit

Influence Depth: 2
Cascade Risk: HIGH 🔴

--------------------------------------------------------------------------------

STEP 8: MST BACKBONE (Kruskal's Algorithm)
-----------------------------------------
Data Structure: Union-Find (Disjoint Set)
Time Complexity: O(E log E)

Find the MINIMUM set of connections that explains MAXIMUM influence patterns.
(Actually Maximum Spanning Tree - we sort by weight DESCENDING)

This reveals the "backbone" of the social network - the strongest connections.

Algorithm:
1. Sort edges by weight (descending for max spanning tree)
2. Use Union-Find to avoid cycles
3. Add edge if it connects different components
4. Stop when we have N-1 edges

Example MST:
    Rahul ═══ Priya (1.0)     ← Strongest connection
       │
    Amit (0.6)
       │
    Sneha (0.4)

================================================================================
COMBINED INFLUENCE SCORE FORMULA
================================================================================

Score = (DegreeCentrality × 40) + (BetweennessCentrality × 40) + (AbsenceRate × 20)

Weights can be adjusted:
- Degree: How connected (many friends)
- Betweenness: How important (bridge between groups)  
- Absence Rate: How often absent (risk factor)

================================================================================
WHAT THIS TELLS TEACHERS
================================================================================

1. TOP INFLUENCERS
   - Who are the "social hubs"?
   - If they're absent, expect others to be absent too

2. FRIEND GROUPS
   - Who hangs out together?
   - Useful for seating arrangements

3. BRIDGE STUDENTS
   - Who connects different groups?
   - Important for communication flow

4. RISK PREDICTION
   - If student X is absent, probability of cascade
   - Proactive intervention possible

5. LONE WOLVES
   - Students with no correlations
   - May need different attention

================================================================================
VIVA DISCUSSION POINTS
================================================================================

1. "Why use BFS for community detection instead of DFS?"
   → BFS ensures we visit all nodes at each level before going deeper.
     For community detection, both work, but BFS gives us level information.

2. "How is this different from regular social network analysis?"
   → We're inferring relationships from ABSENCE patterns, not explicit connections.
     This reveals hidden social structures!

3. "What's the time complexity of the entire algorithm?"
   → O(S × N²) for co-absence matrix (dominant factor)
   → O(N × (N + E)) for betweenness centrality
   → Overall: O(S × N² + N × (N + E))

4. "Why use Maximum Spanning Tree instead of Minimum?"
   → We want to keep the STRONGEST connections, not the weakest!
     The MST backbone shows the core influence paths.

5. "How could this be improved?"
   → Add temporal weighting (recent sessions matter more)
   → Use more sophisticated community detection (Louvain algorithm)
   → Add machine learning prediction

================================================================================
"""

# The actual implementation is in app.py - this is documentation only!
print(__doc__)
