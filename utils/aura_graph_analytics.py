"""
Aura Graph Analytics Integration
Use Aura Graph Analytics (serverless GDS) for advanced graph algorithms
"""

import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Try to import graphdatascience - if not available, class will handle it gracefully
try:
    from graphdatascience.session import GdsSessions, AuraAPICredentials, SessionMemory, DbmsConnectionInfo
    GDS_AVAILABLE = True
except ImportError:
    GDS_AVAILABLE = False


class AuraGraphAnalytics:
    """Wrapper for Aura Graph Analytics (GDS Sessions)"""
    
    def __init__(self):
        """Initialize Aura Graph Analytics connection"""
        if not GDS_AVAILABLE:
            raise ImportError(
                "graphdatascience package is not installed. "
                "Install with: pip install graphdatascience"
            )
        
        load_dotenv()
        
        # Get Aura API credentials
        client_id = os.getenv("AURA_API_CLIENT_ID")
        client_secret = os.getenv("AURA_API_CLIENT_SECRET")
        project_id = os.getenv("AURA_PROJECT_ID")
        
        if not client_id or not client_secret:
            raise ValueError(
                "Aura API credentials not found. "
                "Set AURA_API_CLIENT_ID and AURA_API_CLIENT_SECRET in .env file. "
                "Get credentials from: https://console.neo4j.io/api-credentials"
            )
        
        # Get AuraDB connection info for attaching session
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USER")
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        
        if not neo4j_uri or not neo4j_user or not neo4j_password:
            raise ValueError(
                "Neo4j AuraDB connection info not found. "
                "Set NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD in .env file."
            )
        
        # Store credentials
        self.client_id = client_id
        self.client_secret = client_secret
        self.project_id = project_id if project_id else None
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        
        # Initialize GDS Sessions
        api_credentials = AuraAPICredentials(client_id, client_secret, project_id)
        self.sessions = GdsSessions(api_credentials=api_credentials)
        
        # Will be set when session is created
        self.gds = None
        self.session_name = None
    
    def create_session(
        self, 
        session_name: str = "graphrag-community-detection",
        memory: SessionMemory = SessionMemory.m_4GB,
        ttl_hours: int = 1
    ):
        """
        Create or get an existing GDS Session
        
        Args:
            session_name: Name for the GDS session
            memory: Session memory size (default: 4GB)
            ttl_hours: Time to live in hours (default: 1 hour)
        """
        from datetime import timedelta
        
        # Create database connection info
        db_connection = DbmsConnectionInfo(
            self.neo4j_uri,
            self.neo4j_user,
            self.neo4j_password
        )
        
        # Create or get session
        self.gds = self.sessions.get_or_create(
            session_name=session_name,
            memory=memory,
            db_connection=db_connection,
            ttl=timedelta(hours=ttl_hours)
        )
        
        self.session_name = session_name
        print(f"✅ Created/connected to GDS Session: {session_name}")
        
        return self.gds
    
    def detect_communities(
        self,
        algorithm: str = "leiden",
        min_community_size: int = 3,
        graph_name: str = "entity-graph"
    ) -> Dict:
        """
        Detect communities using Aura Graph Analytics
        
        Args:
            algorithm: Algorithm to use ("leiden", "louvain", "label_propagation")
            min_community_size: Minimum nodes in a community
            graph_name: Name for the projected graph in GDS Session
        
        Returns:
            Dictionary with community information
        """
        if not self.gds:
            # Create session if not already created
            self.create_session()
        
        print(f"\n🔄 Running {algorithm} algorithm via Aura Graph Analytics...")
        
        # Project graph from AuraDB to GDS Session
        print(f"   Projecting graph '{graph_name}' from AuraDB to GDS Session...")
        
        try:
            # Remote projection: project graph from AuraDB to GDS Session
            # We need to include id and name properties so we can map back
            # NOTE: Exclude relationship properties with String values (like 'description')
            #       Community detection algorithms only need graph structure, not relationship properties
            G, result = self.gds.graph.project(
                graph_name=graph_name,
                query=f"""
                MATCH (source)
                WHERE NOT source:Article
                OPTIONAL MATCH (source)-[rel]->(target)
                WHERE NOT target:Article AND type(rel) IN [
                    'FUNDED_BY', 'FOUNDED_BY', 'WORKS_AT', 'PARTNERS_WITH',
                    'COMPETES_WITH', 'USES_TECHNOLOGY', 'LOCATED_IN', 'ACQUIRED'
                ]
                RETURN gds.graph.project.remote(
                    source,
                    target,
                    {{
                        sourceNodeProperties: {{id: source.id, name: source.name}},
                        targetNodeProperties: {{id: target.id, name: target.name}},
                        sourceNodeLabels: labels(source),
                        targetNodeLabels: labels(target),
                        relationshipType: type(rel),
                        relationshipProperties: {{}}
                    }}
                )
                """
            )
            
            print(f"   ✅ Projected graph: {result.nodeCount} nodes, {result.relationshipCount} relationships")
            
        except Exception as e:
            print(f"   ⚠️  Error projecting graph: {e}")
            raise
        
            # Run community detection algorithm
        print(f"   Running {algorithm} algorithm...")
        
        try:
            if algorithm == "leiden":
                algo_result = self.gds.leiden.stream(G)
            elif algorithm == "louvain":
                algo_result = self.gds.louvain.stream(G)
            elif algorithm == "label_propagation":
                algo_result = self.gds.labelPropagation.stream(G)
            else:
                raise ValueError(f"Unknown algorithm: {algorithm}")
            
            # Get node properties including names for mapping
            print(f"   Getting node names from database...")
            node_props = self.gds.graph.nodeProperties.stream(
                G, 
                db_node_properties=["id", "name"]
            )
            
            # Build mapping from node ID to entity name
            node_id_to_name = {}
            
            # Process node properties (result is iterable)
            for record in node_props:
                node_id = record.get("nodeId")
                entity_name = record.get("name")
                if node_id is not None and entity_name:
                    node_id_to_name[node_id] = entity_name
            
            print(f"   ✅ Mapped {len(node_id_to_name)} nodes to entity names")
            
            # Process algorithm results
            communities = {}
            for record in algo_result:
                node_id = record.get("nodeId")
                community_id = record.get("communityId")
                
                # Map node ID to entity name
                entity_name = node_id_to_name.get(node_id)
                if not entity_name:
                    continue  # Skip if we can't map
                
                if community_id not in communities:
                    communities[community_id] = []
                communities[community_id].append(entity_name)
            
            # Filter by minimum size
            filtered_communities = {
                cid: entities for cid, entities in communities.items()
                if len(entities) >= min_community_size
            }
            
            print(f"   ✅ Found {len(filtered_communities)} communities (min size: {min_community_size})")
            
            # Write results back to AuraDB
            print(f"   Writing community IDs back to AuraDB...")
            
            try:
                # Write community IDs back to database
                self._write_communities_to_aura_db(filtered_communities)
                print(f"   ✅ Wrote {sum(len(e) for e in filtered_communities.values())} community IDs to database")
                
                return {
                    "algorithm": algorithm,
                    "total_communities": len(filtered_communities),
                    "communities": filtered_communities,
                    "node_count": result.nodeCount,
                    "relationship_count": result.relationshipCount,
                    "method": "aura_graph_analytics"
                }
            
            except Exception as e:
                print(f"   ⚠️  Error writing back results: {e}")
                print(f"   Results computed but not written to database")
                return {
                    "algorithm": algorithm,
                    "total_communities": len(filtered_communities),
                    "communities": filtered_communities,
                    "node_count": result.nodeCount,
                    "relationship_count": result.relationshipCount,
                    "method": "aura_graph_analytics",
                    "write_back_failed": True
                }
        
        except Exception as e:
            print(f"   ❌ Error running algorithm: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _write_communities_to_aura_db(self, communities: Dict):
        """
        Write community IDs back to AuraDB nodes
        
        Args:
            communities: Dictionary mapping community_id to list of entity names
        """
        from neo4j import GraphDatabase
        
        # Connect to AuraDB
        driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )
        
        try:
            with driver.session() as session:
                # Write community IDs in batch
                for community_id, entity_names in communities.items():
                    # Update all entities in this community
                    query = """
                    UNWIND $entity_names AS entity_name
                    MATCH (e {name: entity_name})
                    WHERE NOT e:Article
                    SET e.community_id = $community_id
                    """
                    session.run(query, entity_names=entity_names, community_id=community_id)
        finally:
            driver.close()
    
    def cleanup(self):
        """Clean up GDS Session (optional - sessions auto-expire)"""
        if self.session_name:
            try:
                self.sessions.delete(self.session_name)
                print(f"✅ Deleted GDS Session: {self.session_name}")
            except Exception as e:
                print(f"⚠️  Could not delete session: {e}")

