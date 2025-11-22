"""
Community Detection for Knowledge Graph
Detect communities of related entities using graph algorithms
Supports both Aura Graph Analytics (GDS Sessions) and simple fallback
"""

from typing import Dict, List, Optional, Tuple
from neo4j import GraphDatabase, Driver
import json
import os
from dotenv import load_dotenv

# Try to import Aura Graph Analytics
try:
    from utils.aura_graph_analytics import AuraGraphAnalytics
    AURA_GDS_AVAILABLE = True
except (ImportError, ValueError):
    AURA_GDS_AVAILABLE = False


class CommunityDetector:
    """Detect communities of related entities"""
    
    def __init__(self, driver: Driver):
        self.driver = driver
        self.aura_gds = None
        
        # Try to initialize Aura Graph Analytics if available
        load_dotenv()
        if AURA_GDS_AVAILABLE:
            try:
                # Check if Aura API credentials are available
                if os.getenv("AURA_API_CLIENT_ID") and os.getenv("AURA_API_CLIENT_SECRET"):
                    self.aura_gds = AuraGraphAnalytics()
                    print("✅ Aura Graph Analytics initialized (will use advanced algorithms)")
                else:
                    print("ℹ️  Aura Graph Analytics not configured (missing API credentials)")
            except Exception as e:
                print(f"⚠️  Aura Graph Analytics not available: {e}")
                self.aura_gds = None
    
    def detect_communities(self, algorithm: str = "leiden", min_community_size: int = 3) -> Dict:
        """
        Detect communities in the graph using specified algorithm
        
        Args:
            algorithm: Algorithm to use ("leiden", "louvain", "label_propagation")
            min_community_size: Minimum nodes in a community
        
        Returns:
            Dictionary with community information
        """
        # Try Aura Graph Analytics first (if available)
        if self.aura_gds:
            try:
                print(f"🚀 Using Aura Graph Analytics for {algorithm} algorithm...")
                result = self.aura_gds.detect_communities(
                    algorithm=algorithm,
                    min_community_size=min_community_size
                )
                
                # Results already written back by AuraGraphAnalytics
                return {
                    "algorithm": result["algorithm"],
                    "total_communities": result["total_communities"],
                    "communities": result["communities"],
                    "method": result.get("method", "aura_graph_analytics")
                }
            except Exception as e:
                print(f"⚠️  Aura Graph Analytics failed: {e}")
                print("   Falling back to simple community detection...")
                # Fall through to simple detection
        
        # Fallback: Use simple community detection or try direct GDS
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
        try:
            # First check if GDS procedures are available
            try:
                gds_check = session.run("CALL dbms.procedures() YIELD name WHERE name STARTS WITH 'gds.' RETURN count(*) as count")
                gds_count = gds_check.single()["count"] if gds_check.single() else 0
                if gds_count == 0:
                    raise Exception("GDS library not installed")
            except Exception as e:
                # Can't check GDS availability - assume it's not available
                raise Exception("GDS library not available")
            
            # Drop existing graph if it exists (check first to avoid warnings)
            try:
                graph_exists = session.run("""
                    CALL gds.graph.exists('entity-graph') 
                    YIELD exists
                    RETURN exists
                """)
                exists_record = graph_exists.single()
                if exists_record and exists_record.get("exists"):
                    session.run("CALL gds.graph.drop('entity-graph') YIELD graphName")
            except Exception:
                # Graph doesn't exist or can't check - that's fine, continue
                pass
            
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
            # Only store filtered communities (size >= min_size) to match the return value
            self._store_communities(session, filtered_communities)
            
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
            # First check if GDS procedures are available
            try:
                gds_check = session.run("CALL dbms.procedures() YIELD name WHERE name STARTS WITH 'gds.' RETURN count(*) as count")
                gds_count = gds_check.single()["count"] if gds_check.single() else 0
                if gds_count == 0:
                    raise Exception("GDS library not installed")
            except Exception as e:
                # Can't check GDS availability - assume it's not available
                raise Exception("GDS library not available")
            
            # Drop existing graph if it exists (check first to avoid warnings)
            try:
                graph_exists = session.run("""
                    CALL gds.graph.exists('entity-graph') 
                    YIELD exists
                    RETURN exists
                """)
                exists_record = graph_exists.single()
                if exists_record and exists_record.get("exists"):
                    session.run("CALL gds.graph.drop('entity-graph') YIELD graphName")
            except Exception:
                # Graph doesn't exist or can't check - that's fine, continue
                pass
            
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
            
            # Only store filtered communities (size >= min_size) to match the return value
            self._store_communities(session, filtered_communities)
            
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
            # First check if GDS procedures are available
            try:
                gds_check = session.run("CALL dbms.procedures() YIELD name WHERE name STARTS WITH 'gds.' RETURN count(*) as count")
                gds_count = gds_check.single()["count"] if gds_check.single() else 0
                if gds_count == 0:
                    raise Exception("GDS library not installed")
            except Exception as e:
                # Can't check GDS availability - assume it's not available
                raise Exception("GDS library not available")
            
            # Drop existing graph if it exists (check first to avoid warnings)
            try:
                graph_exists = session.run("""
                    CALL gds.graph.exists('entity-graph') 
                    YIELD exists
                    RETURN exists
                """)
                exists_record = graph_exists.single()
                if exists_record and exists_record.get("exists"):
                    session.run("CALL gds.graph.drop('entity-graph') YIELD graphName")
            except Exception:
                # Graph doesn't exist or can't check - that's fine, continue
                pass
            
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
            
            # Only store filtered communities (size >= min_size) to match the return value
            self._store_communities(session, filtered_communities)
            
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
        
        # Store community IDs on nodes so downstream queries can use n.community_id
        # Only store filtered communities (size >= min_size) to match the return value
        self._store_communities(session, filtered_communities)

        return {
            "algorithm": "connected_components",
            "total_communities": len(filtered_communities),
            "communities": filtered_communities
        }
    
    def _store_communities(self, session, communities: Dict):
        """Store community IDs on nodes"""
        # Use the original community_id from the dict (not enumerate index)
        for community_id, entities in communities.items():
            for entity_name in entities:
                # Store the original community_id from the algorithm
                session.run("""
                    MATCH (e {name: $name})
                    WHERE NOT e:Article
                    SET e.community_id = $community_id
                """, name=entity_name, community_id=community_id)
    
    def _write_communities_to_db(self, communities: Dict):
        """
        Write community IDs back to database from Aura Graph Analytics results
        
        Args:
            communities: Dictionary mapping community_id to list of node IDs
        """
        # For Aura Graph Analytics, we get node IDs, not names
        # We need to map node IDs back to entity names
        # This is a simplified version - in practice, you'd need to get node names from the GDS Session
        # For now, we'll use the simple community detection to map IDs to names
        
        print("   Note: Community IDs computed via Aura Graph Analytics")
        print("   Using simple mapping to write back to database...")
        
        # Actually, we'll let the simple detection handle the write-back
        # The Aura Graph Analytics result can be used for analysis, but we need
        # to write back using entity names, which requires mapping node IDs to names
        # For now, this is a placeholder - the simple detection will handle it
        pass
    
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

