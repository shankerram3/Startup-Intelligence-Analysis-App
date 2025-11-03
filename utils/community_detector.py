"""
Community Detection for Knowledge Graph
Detect communities of related entities using graph algorithms
"""

from typing import Dict, List, Optional, Tuple
from neo4j import GraphDatabase
import json


class CommunityDetector:
    """Detect communities of related entities"""
    
    def __init__(self, driver: GraphDatabase):
        self.driver = driver
    
    def detect_communities(self, algorithm: str = "leiden", min_community_size: int = 3) -> Dict:
        """
        Detect communities in the graph using specified algorithm
        
        Args:
            algorithm: Algorithm to use ("leiden", "louvain", "label_propagation")
            min_community_size: Minimum nodes in a community
        
        Returns:
            Dictionary with community information
        """
        with self.driver.session() as session:
            if algorithm == "leiden":
                return self._detect_leiden_communities(session, min_community_size)
            elif algorithm == "louvain":
                return self._detect_louvain_communities(session, min_community_size)
            elif algorithm == "label_propagation":
                return self._detect_label_propagation_communities(session, min_community_size)
            else:
                raise ValueError(f"Unknown algorithm: {algorithm}")
    
    def _detect_leiden_communities(self, session, min_size: int) -> Dict:
        """
        Detect communities using Leiden algorithm (via GDS library)
        
        Note: Requires Neo4j Graph Data Science (GDS) library
        """
        # Check if GDS is available
        try:
            # Create projection
            session.run("""
                CALL gds.graph.project(
                    'entity-graph',
                    ['Company', 'Person', 'Investor', 'Technology', 'Product', 'Location', 'Event'],
                    {
                        FUNDED_BY: {orientation: 'UNDIRECTED'},
                        FOUNDED_BY: {orientation: 'UNDIRECTED'},
                        WORKS_AT: {orientation: 'UNDIRECTED'},
                        PARTNERS_WITH: {orientation: 'UNDIRECTED'},
                        COMPETES_WITH: {orientation: 'UNDIRECTED'},
                        USES_TECHNOLOGY: {orientation: 'UNDIRECTED'},
                        LOCATED_IN: {orientation: 'UNDIRECTED'}
                    }
                )
            """)
            
            # Run Leiden algorithm
            result = session.run("""
                CALL gds.leiden.stream('entity-graph')
                YIELD nodeId, communityId
                RETURN gds.util.asNode(nodeId).name as name, 
                       communityId as community
                ORDER BY community, name
            """)
            
            communities = {}
            for record in result:
                community_id = record["community"]
                entity_name = record["name"]
                
                if community_id not in communities:
                    communities[community_id] = []
                communities[community_id].append(entity_name)
            
            # Filter by minimum size
            filtered_communities = {
                cid: entities for cid, entities in communities.items() 
                if len(entities) >= min_size
            }
            
            # Store community IDs on nodes
            self._store_communities(session, communities)
            
            return {
                "algorithm": "leiden",
                "total_communities": len(filtered_communities),
                "communities": filtered_communities
            }
            
        except Exception as e:
            # Fallback if GDS not available
            print(f"⚠️  GDS library not available: {e}")
            print("Falling back to simple community detection...")
            return self._detect_simple_communities(session, min_size)
    
    def _detect_louvain_communities(self, session, min_size: int) -> Dict:
        """Detect communities using Louvain algorithm"""
        try:
            session.run("""
                CALL gds.graph.project(
                    'entity-graph',
                    ['Company', 'Person', 'Investor', 'Technology', 'Product', 'Location', 'Event'],
                    '*'
                )
            """)
            
            result = session.run("""
                CALL gds.louvain.stream('entity-graph')
                YIELD nodeId, communityId
                RETURN gds.util.asNode(nodeId).name as name, 
                       communityId as community
                ORDER BY community, name
            """)
            
            communities = {}
            for record in result:
                community_id = record["community"]
                entity_name = record["name"]
                
                if community_id not in communities:
                    communities[community_id] = []
                communities[community_id].append(entity_name)
            
            filtered_communities = {
                cid: entities for cid, entities in communities.items() 
                if len(entities) >= min_size
            }
            
            self._store_communities(session, communities)
            
            return {
                "algorithm": "louvain",
                "total_communities": len(filtered_communities),
                "communities": filtered_communities
            }
            
        except Exception as e:
            print(f"⚠️  GDS library not available: {e}")
            return self._detect_simple_communities(session, min_size)
    
    def _detect_label_propagation_communities(self, session, min_size: int) -> Dict:
        """Detect communities using Label Propagation algorithm"""
        try:
            session.run("""
                CALL gds.graph.project(
                    'entity-graph',
                    ['Company', 'Person', 'Investor', 'Technology', 'Product', 'Location', 'Event'],
                    '*'
                )
            """)
            
            result = session.run("""
                CALL gds.labelPropagation.stream('entity-graph')
                YIELD nodeId, communityId
                RETURN gds.util.asNode(nodeId).name as name, 
                       communityId as community
                ORDER BY community, name
            """)
            
            communities = {}
            for record in result:
                community_id = record["community"]
                entity_name = record["name"]
                
                if community_id not in communities:
                    communities[community_id] = []
                communities[community_id].append(entity_name)
            
            filtered_communities = {
                cid: entities for cid, entities in communities.items() 
                if len(entities) >= min_size
            }
            
            self._store_communities(session, communities)
            
            return {
                "algorithm": "label_propagation",
                "total_communities": len(filtered_communities),
                "communities": filtered_communities
            }
            
        except Exception as e:
            print(f"⚠️  GDS library not available: {e}")
            return self._detect_simple_communities(session, min_size)
    
    def _detect_simple_communities(self, session, min_size: int) -> Dict:
        """
        Simple community detection using connected components (fallback)
        Uses entity IDs instead of deprecated id() function
        """
        # Find connected components (communities)
        # Use entity IDs instead of internal Neo4j IDs
        result = session.run("""
            MATCH (n)
            WHERE NOT n:Article
            RETURN n.name as name, n.id as entity_id
            ORDER BY n.name
        """)
        
        # Build a graph of connections
        nodes = {}
        
        for record in result:
            entity_name = record["name"]
            entity_id = record.get("entity_id") or entity_name
            nodes[entity_id] = entity_name
        
        # Find connected components using breadth-first search
        # Use the session passed as parameter (already created in detect_communities)
        visited = set()
        communities = {}
        community_counter = 0
        
        for entity_id, entity_name in nodes.items():
            if entity_id in visited:
                continue
            
            # Start new community
            community_id = community_counter
            community_counter += 1
            communities[community_id] = []
            
            # BFS to find all connected nodes
            queue = [entity_id]
            visited.add(entity_id)
            
            while queue:
                current_id = queue.pop(0)
                current_name = nodes[current_id]
                communities[community_id].append(current_name)
                
                # Find connected nodes (within 3 hops) - using entity IDs, not Neo4j internal IDs
                connected = session.run("""
                    MATCH (n)-[*1..3]-(connected)
                    WHERE (n.id = $current_id OR n.name = $current_name)
                      AND NOT connected:Article
                    RETURN DISTINCT connected.id as conn_id, connected.name as conn_name
                """, current_id=current_id, current_name=current_name)
                
                for conn_record in connected:
                    conn_id = conn_record.get("conn_id") or conn_record["conn_name"]
                    if conn_id not in visited:
                        visited.add(conn_id)
                        if conn_id in nodes:
                            queue.append(conn_id)
        
        filtered_communities = {
            cid: entities for cid, entities in communities.items() 
            if len(entities) >= min_size
        }
        
        return {
            "algorithm": "connected_components",
            "total_communities": len(filtered_communities),
            "communities": filtered_communities
        }
    
    def _store_communities(self, session, communities: Dict):
        """Store community IDs on nodes"""
        # Convert community_id from elementId string to a numeric ID for storage
        community_map = {}
        for idx, (community_id, entities) in enumerate(communities.items()):
            for entity_name in entities:
                # Use entity_id if available, otherwise use name
                result = session.run("""
                    MATCH (e {name: $name})
                    WHERE NOT e:Article
                    RETURN e.id as entity_id
                    LIMIT 1
                """, name=entity_name)
                record = result.single()
                entity_id = record["entity_id"] if record else entity_name
                
                # Store numeric community ID
                if entity_id not in community_map:
                    community_map[entity_id] = idx
                
                session.run("""
                    MATCH (e {name: $name})
                    WHERE NOT e:Article
                    SET e.community_id = $community_id
                """, name=entity_name, community_id=idx)
    
    def get_community_summary(self, community_id: int) -> Dict:
        """Get summary information for a community"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                WHERE n.community_id = $community_id AND NOT n:Article
                RETURN labels(n)[0] as type, count(n) as count
                ORDER BY count DESC
            """, community_id=community_id)
            
            type_counts = {}
            for record in result:
                type_counts[record["type"]] = record["count"]
            
            # Get key relationships
            rel_result = session.run("""
                MATCH (n)-[r]->(m)
                WHERE n.community_id = $community_id 
                  AND m.community_id = $community_id
                  AND NOT n:Article AND NOT m:Article
                RETURN type(r) as rel_type, count(r) as count
                ORDER BY count DESC
                LIMIT 10
            """, community_id=community_id)
            
            relationships = {}
            for record in rel_result:
                relationships[record["rel_type"]] = record["count"]
            
            return {
                "community_id": community_id,
                "entity_types": type_counts,
                "key_relationships": relationships
            }
    
    def find_related_communities(self, entity_name: str) -> List[Dict]:
        """Find communities related to a given entity"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e {name: $name})
                WHERE NOT e:Article
                WITH e.community_id as community_id
                
                MATCH (n)
                WHERE n.community_id = community_id AND NOT n:Article
                RETURN n.name as name, labels(n)[0] as type
                LIMIT 50
            """, name=entity_name)
            
            related = []
            for record in result:
                related.append({
                    "name": record["name"],
                    "type": record["type"]
                })
            
            return related

