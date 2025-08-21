"""
ERPNext AI Agent - Phase 1: Knowledge Graph Setup
NetworkX and Neo4j integration for business relationships
"""

import networkx as nx
from neo4j import GraphDatabase
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import time

class ERPNextKnowledgeGraph:
    """Setup and manage knowledge graph for ERPNext relationships"""
    
    def __init__(self, neo4j_uri: str = "bolt://localhost:7687", 
                 neo4j_user: str = "neo4j", neo4j_password: str = "erpnext123"):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.driver = None
        self.nx_graph = nx.MultiDiGraph()
        
    def connect_to_neo4j(self) -> bool:
        """Connect to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                if test_value == 1:
                    print("✅ Connected to Neo4j successfully")
                    return True
                    
        except Exception as e:
            print(f"❌ Failed to connect to Neo4j: {e}")
            print("Make sure Neo4j is running and credentials are correct")
            return False
    
    def create_constraints(self) -> bool:
        """Create constraints and indexes for better performance"""
        constraints = [
            "CREATE CONSTRAINT customer_name IF NOT EXISTS FOR (c:Customer) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT item_name IF NOT EXISTS FOR (i:Item) REQUIRE i.name IS UNIQUE", 
            "CREATE CONSTRAINT supplier_name IF NOT EXISTS FOR (s:Supplier) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT sales_order_name IF NOT EXISTS FOR (so:SalesOrder) REQUIRE so.name IS UNIQUE"
        ]        
        try:
            with self.driver.session() as session:
                for constraint in constraints:
                    try:
                        session.run(constraint)
                    except Exception:
                        pass  # Constraint may already exist
            
            print("✅ Neo4j constraints created")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create constraints: {e}")
            return False
    
    def create_sample_business_graph(self) -> bool:
        """Create sample business relationship graph"""
        # Sample data representing ERPNext business relationships
        entities = {
            "customers": [
                {"name": "ABC Corp", "type": "Large Enterprise", "credit_limit": 100000},
                {"name": "XYZ Ltd", "type": "SME", "credit_limit": 50000},
                {"name": "Tech Solutions", "type": "Startup", "credit_limit": 25000}
            ],
            "items": [
                {"name": "Laptop", "item_group": "Electronics", "rate": 1500},
                {"name": "Office Chair", "item_group": "Furniture", "rate": 300},
                {"name": "Software License", "item_group": "Services", "rate": 1000}
            ],
            "suppliers": [
                {"name": "TechCorp Supplies", "type": "Electronics"},
                {"name": "Office Furniture Co", "type": "Furniture"}
            ]
        }
        
        # Create nodes in NetworkX
        for customer in entities["customers"]:
            self.nx_graph.add_node(f"customer_{customer['name']}", 
                                 label="Customer", **customer)
        
        for item in entities["items"]:
            self.nx_graph.add_node(f"item_{item['name']}", 
                                 label="Item", **item)
        
        for supplier in entities["suppliers"]:
            self.nx_graph.add_node(f"supplier_{supplier['name']}", 
                                 label="Supplier", **supplier)        
        # Create relationships
        relationships = [
            ("customer_ABC Corp", "item_Laptop", "PURCHASED", {"quantity": 10, "date": "2024-01-15"}),
            ("customer_XYZ Ltd", "item_Office Chair", "PURCHASED", {"quantity": 25, "date": "2024-02-01"}),
            ("supplier_TechCorp Supplies", "item_Laptop", "SUPPLIES", {"lead_time": 7}),
            ("supplier_Office Furniture Co", "item_Office Chair", "SUPPLIES", {"lead_time": 14}),
            ("customer_ABC Corp", "customer_Tech Solutions", "REFERRED", {"date": "2024-01-20"})
        ]
        
        for source, target, rel_type, props in relationships:
            self.nx_graph.add_edge(source, target, relationship=rel_type, **props)
        
        print(f"✅ Created NetworkX graph with {len(self.nx_graph.nodes)} nodes and {len(self.nx_graph.edges)} edges")
        return True
    
    def sync_to_neo4j(self) -> bool:
        """Sync NetworkX graph to Neo4j database"""
        if not self.driver:
            print("❌ No Neo4j connection available")
            return False
        
        try:
            with self.driver.session() as session:
                # Clear existing data
                session.run("MATCH (n) DETACH DELETE n")
                
                # Create nodes
                for node_id, data in self.nx_graph.nodes(data=True):
                    label = data.get('label', 'Node')
                    props = {k: v for k, v in data.items() if k != 'label'}
                    
                    query = f"CREATE (n:{label} {{id: $id"
                    for key in props.keys():
                        query += f", {key}: ${key}"
                    query += "})"
                    
                    session.run(query, id=node_id, **props)
                
                # Create relationships
                for source, target, data in self.nx_graph.edges(data=True):
                    rel_type = data.get('relationship', 'RELATED')
                    props = {k: v for k, v in data.items() if k != 'relationship'}
                    
                    query = f"""
                    MATCH (a {{id: $source}}), (b {{id: $target}})
                    CREATE (a)-[r:{rel_type}]->(b)
                    """
                    if props:
                        query += "SET r += $props"
                    
                    session.run(query, source=source, target=target, props=props)
            
            print("✅ Synced graph to Neo4j")
            return True
            
        except Exception as e:
            print(f"❌ Failed to sync to Neo4j: {e}")
            return False    
    def query_graph(self, query_type: str = "customer_items") -> List[Dict[str, Any]]:
        """Execute sample queries on the knowledge graph"""
        queries = {
            "customer_items": """
                MATCH (c:Customer)-[r:PURCHASED]->(i:Item)
                RETURN c.name as customer, i.name as item, r.quantity as quantity, r.date as date
            """,
            "supplier_items": """
                MATCH (s:Supplier)-[r:SUPPLIES]->(i:Item)
                RETURN s.name as supplier, i.name as item, r.lead_time as lead_time
            """,
            "customer_network": """
                MATCH (c1:Customer)-[r:REFERRED]->(c2:Customer)
                RETURN c1.name as referrer, c2.name as referred, r.date as date
            """
        }
        
        if query_type not in queries:
            print(f"❌ Unknown query type: {query_type}")
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run(queries[query_type])
                records = [record.data() for record in result]
                
                print(f"🔍 Query '{query_type}' results:")
                for i, record in enumerate(records):
                    print(f"  {i+1}. {record}")
                
                return records
                
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return []
    
    def export_graph_analysis(self) -> Dict[str, Any]:
        """Export graph analysis and metrics"""
        analysis = {
            "nodes": len(self.nx_graph.nodes),
            "edges": len(self.nx_graph.edges),
            "density": nx.density(self.nx_graph),
            "node_types": {},
            "relationship_types": {}
        }
        
        # Count node types
        for _, data in self.nx_graph.nodes(data=True):
            label = data.get('label', 'Unknown')
            analysis["node_types"][label] = analysis["node_types"].get(label, 0) + 1
        
        # Count relationship types
        for _, _, data in self.nx_graph.edges(data=True):
            rel_type = data.get('relationship', 'Unknown')
            analysis["relationship_types"][rel_type] = analysis["relationship_types"].get(rel_type, 0) + 1
        
        # Save analysis
        with open("graph_analysis.json", "w") as f:
            json.dump(analysis, f, indent=2)
        
        print("📊 Graph Analysis:")
        print(f"  Nodes: {analysis['nodes']}")
        print(f"  Edges: {analysis['edges']}")
        print(f"  Density: {analysis['density']:.3f}")
        print(f"  Node types: {analysis['node_types']}")
        print(f"  Relationship types: {analysis['relationship_types']}")
        
        return analysis    
    def setup_knowledge_graph(self) -> bool:
        """Complete knowledge graph setup"""
        print("🚀 Setting up ERPNext Knowledge Graph...")
        
        # Step 1: Connect to Neo4j
        if not self.connect_to_neo4j():
            print("⚠️  Continuing with NetworkX only (Neo4j unavailable)")
        
        # Step 2: Create constraints (if Neo4j available)
        if self.driver:
            self.create_constraints()
        
        # Step 3: Create sample business graph
        if not self.create_sample_business_graph():
            return False
        
        # Step 4: Sync to Neo4j (if available)
        if self.driver:
            self.sync_to_neo4j()
            
            # Step 5: Test queries
            self.query_graph("customer_items")
            self.query_graph("supplier_items")
        
        # Step 6: Export analysis
        self.export_graph_analysis()
        
        print("✅ Knowledge graph setup complete!")
        return True
    
    def close(self):
        """Close database connections"""
        if self.driver:
            self.driver.close()

class ERPNextHypergraphBuilder:
    """Build hypergraph structures for complex business relationships"""
    
    def __init__(self):
        self.hypergraph = {}  # Simple hypergraph representation
        
    def create_business_hyperedges(self) -> Dict[str, Any]:
        """Create hyperedges representing complex business relationships"""
        # Sales cycle hyperedge: Customer -> Quotation -> Sales Order -> Delivery -> Invoice -> Payment
        sales_cycle = {
            "nodes": ["Customer:ABC Corp", "Quotation:QTN-001", "Sales Order:SO-001", 
                     "Delivery Note:DN-001", "Sales Invoice:SI-001", "Payment Entry:PE-001"],
            "type": "sales_cycle",
            "properties": {"total_value": 75000, "duration_days": 45}
        }
        
        # Purchase cycle hyperedge: Supplier -> RFQ -> Purchase Order -> Receipt -> Invoice -> Payment
        purchase_cycle = {
            "nodes": ["Supplier:TechCorp", "RFQ:RFQ-001", "Purchase Order:PO-001",
                     "Purchase Receipt:PR-001", "Purchase Invoice:PI-001", "Payment Entry:PE-002"],
            "type": "purchase_cycle", 
            "properties": {"total_value": 50000, "duration_days": 30}
        }
        
        # Inventory flow hyperedge: Items across multiple warehouses and transactions
        inventory_flow = {
            "nodes": ["Item:Laptop", "Warehouse:Main", "Warehouse:Branch", 
                     "Stock Entry:SE-001", "Stock Entry:SE-002"],
            "type": "inventory_flow",
            "properties": {"total_qty": 100, "movement_type": "transfer"}
        }
        
        self.hypergraph = {
            "sales_cycle_001": sales_cycle,
            "purchase_cycle_001": purchase_cycle,
            "inventory_flow_001": inventory_flow
        }
        
        print("✅ Created business hypergraph with complex relationships")
        return self.hypergraph
    
    def export_hypergraph(self) -> bool:
        """Export hypergraph structure"""
        try:
            with open("business_hypergraph.json", "w") as f:
                json.dump(self.hypergraph, f, indent=2)
            
            print("📄 Hypergraph exported to business_hypergraph.json")
            return True
            
        except Exception as e:
            print(f"❌ Failed to export hypergraph: {e}")
            return False

def main():
    """Main setup function"""
    # Setup basic knowledge graph
    kg = ERPNextKnowledgeGraph()
    success = kg.setup_knowledge_graph()
    
    if success:
        print("\n" + "="*50)
        
        # Setup hypergraph
        hg_builder = ERPNextHypergraphBuilder()
        hg_builder.create_business_hyperedges()
        hg_builder.export_hypergraph()
        
        print("\n🎉 Knowledge graph setup complete!")
        print("\nNext steps:")
        print("1. Integrate with real ERPNext data")
        print("2. Implement graph-based queries")
        print("3. Add semantic similarity for nodes")
        print("4. Build recommendation system")
    
    # Cleanup
    kg.close()

if __name__ == "__main__":
    main()
