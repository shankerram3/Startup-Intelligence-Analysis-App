from neo4j import GraphDatabase
from pyvis.network import Network
from utils.community_detector import CommunityDetector

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j","password"))
net = Network(height="800px", width="100%", notebook=False)

community_id = 5
with driver.session() as s:
    # Check if communities have been detected (nodes with community_id exist)
    existing_communities = s.run("""
        MATCH (n)
        WHERE n.community_id IS NOT NULL AND NOT n:Article
        RETURN count(DISTINCT n.community_id) as count
        LIMIT 1
    """).single()
    
    community_count = existing_communities["count"] if existing_communities else 0
    
    # If no communities detected, run detection
    if community_count == 0:
        print("No communities detected. Running community detection...")
        detector = CommunityDetector(driver)
        result = detector.detect_communities(algorithm="label_propagation", min_community_size=3)
        print(f"✓ Community detection complete: {result.get('total_communities', 0)} communities found (min_size >= 3)")
        print(f"  Algorithm: {result.get('algorithm', 'unknown')}")
    else:
        print(f"Found {community_count} existing communities. Skipping detection.")

    # Get all available communities with their sizes
    community_stats = s.run("""
        MATCH (n)
        WHERE n.community_id IS NOT NULL AND NOT n:Article
        WITH n.community_id AS cid, count(n) AS size
        WHERE size >= 3
        RETURN cid, size
        ORDER BY size DESC
    """).data()
    
    print(f"\nAvailable communities (size >= 3): {len(community_stats)}")
    if community_stats:
        print("Top 10 communities by size:")
        for stat in community_stats[:10]:
            print(f"  Community {stat['cid']}: {stat['size']} nodes")
    
    # Visualize ALL communities (or just selected one if specified)
    # Set visualize_all=True to show all communities, False to show just one
    visualize_all = True
    
    if visualize_all:
        print(f"\nVisualizing ALL {len(community_stats)} communities...")
        # Get all nodes from all communities
        nodes = s.run("""
          MATCH (n)
          WHERE n.community_id IS NOT NULL AND NOT n:Article
          RETURN elementId(n) AS id, n.name AS name, labels(n)[0] AS label, n.community_id AS cid
        """).data()
        # Get all edges within communities
        edges = s.run("""
          MATCH (a)-[r]->(b)
          WHERE a.community_id IS NOT NULL AND b.community_id IS NOT NULL
            AND a.community_id = b.community_id
            AND NOT a:Article AND NOT b:Article
          RETURN elementId(a) AS s, elementId(b) AS t, type(r) AS type, a.community_id AS cid
        """).data()
    else:
        # If selected community_id doesn't exist, pick the largest one
        available = [r["cid"] for r in community_stats]
        if available and community_id not in available:
            community_id = available[0]  # Pick the largest (first in DESC order)
        print(f"\nVisualizing community {community_id}...")
        
        nodes = s.run("""
          MATCH (n)
          WHERE n.community_id IS NOT NULL AND n.community_id = $cid AND NOT n:Article
          RETURN elementId(n) AS id, n.name AS name, labels(n)[0] AS label, n.community_id AS cid
        """, cid=community_id).data()
        edges = s.run("""
          MATCH (a)-[r]->(b)
          WHERE a.community_id IS NOT NULL AND b.community_id IS NOT NULL
            AND a.community_id = $cid AND b.community_id = $cid
          RETURN elementId(a) AS s, elementId(b) AS t, type(r) AS type
        """, cid=community_id).data()

# Color function: each community gets a unique color
color = lambda cid: f"hsl({(cid*47)%360},70%,60%)"
for n in nodes:
    net.add_node(n["id"], label=f'{n["name"]} ({n["label"]})', color=color(n["cid"]), title=f'Community {n["cid"]}')
for e in edges:
    net.add_edge(e["s"], e["t"], title=e["type"])

net.write_html("community.html", notebook=False)
driver.close()