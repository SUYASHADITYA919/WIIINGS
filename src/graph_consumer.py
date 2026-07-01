import json
import random
from kafka import KafkaConsumer
from neo4j import GraphDatabase

KAFKA_TOPIC = "air-traffic-telemetry"
KAFKA_SERVER = "localhost:9092"

# Neo4j Connection Credentials
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password123"

class IntelligenceGraphEngine:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self.bootstrap_mock_intelligence_network()

    def close(self):
        self.driver.close()

    def bootstrap_mock_intelligence_network(self):
        """Seeds the graph database with standard corporate nodes to link planes against."""
        with self.driver.session() as session:
            # Create Mock Shell Companies and Risk Profiles
            seed_query = """
            MERGE (c1:Company {name: "Apex Logistics Ltd", registration: "Cayman Islands", risk_score: 15})
            MERGE (c2:Company {name: "Horizon Charters", registration: "Panama", risk_score: 75})
            MERGE (c3:Company {name: "Global Freight Corp", registration: "Delaware", risk_score: 40})
            
            MERGE (p1:ParentConglomerate {name: "AeroVanguard Group", headquarters: "London"})
            MERGE (p2:ParentConglomerate {name: "Vortex Holdings", headquarters: "Zurich"})
            
            MERGE (c1)-[:SUBSIDIARY_OF]->(p1)
            MERGE (c2)-[:SUBSIDIARY_OF]->(p2)
            MERGE (c3)-[:SUBSIDIARY_OF]->(p1)
            """
            session.run(seed_query)
            print("[GRAPH INTEL] Pre-mapped intelligence infrastructure active.")

    def link_flight_to_network(self, icao24, callsign, origin_country):
        """Ingests live telemetry frames and weaves them directly into corporate graphs."""
        mock_owners = ["Apex Logistics Ltd", "Horizon Charters", "Global Freight Corp"]
        assigned_owner = random.choice(mock_owners)

        # High-performance inline execution function to utilize session transactional pooling
        def _upsert_transaction(tx, i24, cs, country, owner):
            cypher_query = """
            MERGE (a:Aircraft {icao24: $icao24})
            SET a.callsign = $callsign, a.origin_country = $origin_country, a.last_seen = timestamp()
            
            WITH a
            MATCH (c:Company {name: $owner_name})
            MERGE (a)-[r:OPERATED_BY]->(c)
            
            RETURN a.callsign AS asset, c.name AS owner, c.risk_score AS risk
            """
            result = tx.run(cypher_query, icao24=i24, callsign=cs, 
                            origin_country=country, owner_name=owner)
            return result.single()

        try:
            # Using execute_write keeps the socket alive and eliminates the Windows connection lag
            with self.driver.session() as session:
                record = session.execute_write(_upsert_transaction, icao24, callsign, origin_country, assigned_owner)
                
                if record:
                    if record["risk"] > 50:
                        print(f"⚠️  [RISK ALERT] Live Asset [{record['asset']}] linked to high-risk shell corp [{record['owner']}] (Risk Score: {record['risk']})!")
                    else:
                        print(f"[GRAPH] Successfully linked asset {record['asset']} -> {record['owner']}")
        except Exception as e:
            print(f"[GRAPH ERROR] Transaction failed to commit: {e}")

def start_graph_consumer():
    graph_engine = IntelligenceGraphEngine()
    
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=['127.0.0.1:9092'], # Direct loopback explicitly avoids DNS delays
        auto_offset_reset='latest',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        api_version=(0, 10, 2),
        request_timeout_ms=30000,
        session_timeout_ms=10000,
    )
    
    print("[GRAPH CONSUMER ACTIVE] Processing live flight streams into graph entity networks...")
    
    for message in consumer:
        data = message.value
        graph_engine.link_flight_to_network(
            icao24=data["icao24"],
            callsign=data["callsign"],
            origin_country=data["origin_country"]
        )

if __name__ == "__main__":
    try:
        start_graph_consumer()
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Graph processor deactivated cleanly.")
        