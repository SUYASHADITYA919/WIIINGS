import json
import psycopg2
from kafka import KafkaConsumer

KAFKA_TOPIC = "air-traffic-telemetry"
KAFKA_SERVER = "localhost:9092"

# Database Link Configurations
DB_CONFIG = {
    "dbname": "national_security_db",
    "user": "defense_analyst",
    "password": "password123",
    "host": "localhost",
    "port": "5432"
}

# Simple geometric bounding polygon representing simulated restricted airspace over central India
MOCK_RESTRICTED_ZONE = "POLYGON((75.0 20.0, 80.0 20.0, 80.0 25.0, 75.0 25.0, 75.0 20.0))"

def initialize_database():
    """Connects to Postgres, activates PostGIS extensions, and maps tactical schemas."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Initialize the engine spatial features extension
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        
        # Create core spatial vector table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS live_aircraft_tracks (
                icao24 VARCHAR(50) PRIMARY KEY,
                callsign VARCHAR(50),
                origin_country VARCHAR(100),
                altitude_meters NUMERIC,
                velocity_mps NUMERIC,
                last_updated TIMESTAMP,
                geom GEOMETRY(Point, 4326)
            );
        """)
        print("[DATABASE] PostGIS spatial environment validated and active.")
        return conn
    except Exception as e:
        print(f"[DATABASE ERROR] Initialization sequence aborted: {e}")
        exit(1)

def run_geofence_audit(cursor, lon, lat, callsign):
    """Executes spatial analysis queries to audit if vector intersections occur."""
    query = """
        SELECT ST_Contains(
            ST_GeomFromText(%s, 4326),
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)
        );
    """
    cursor.execute(query, (MOCK_RESTRICTED_ZONE, lon, lat))
    is_breached = cursor.fetchone()[0]
    if is_breached:
        print(f"!!! [TACTICAL ALERT] Aircraft {callsign} breached Restricted Border Checkpoint Alpha !!! Coordinates: ({lat}, {lon})")

def start_consumer():
    db_connection = initialize_database()
    db_cursor = db_connection.cursor()
    
    print("[INFO] Establishing operational link with Kafka Broker...")
    
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=['127.0.0.1:9092'],
        auto_offset_reset='earliest',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        api_version=(0, 10, 2),
        request_timeout_ms=30000,      
        session_timeout_ms=10000,
        metadata_max_age_ms=30000,
    )
    
    print("[CONSUMER ENGINE ACTIVE] Listening for streaming telemetry payloads...")
    
    for message in consumer:
        data = message.value
        
        lon = data["longitude"]
        lat = data["latitude"]
        callsign = data["callsign"]
        
        run_geofence_audit(db_cursor, lon, lat, callsign)
        
        upsert_query = """
            INSERT INTO live_aircraft_tracks (icao24, callsign, origin_country, altitude_meters, velocity_mps, last_updated, geom)
            VALUES (%s, %s, %s, %s, %s, TO_TIMESTAMP(%s), ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            ON CONFLICT (icao24) DO UPDATE SET
                callsign = EXCLUDED.callsign,
                altitude_meters = EXCLUDED.altitude_meters,
                velocity_mps = EXCLUDED.velocity_mps,
                last_updated = EXCLUDED.last_updated,
                geom = EXCLUDED.geom;
        """
        db_cursor.execute(upsert_query, (
            data["icao24"], callsign, data["origin_country"],
            data["altitude_meters"], data["velocity_mps"], data["timestamp"],
            lon, lat
        ))

if __name__ == "__main__":
    try:
        start_consumer()
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Processing cluster deactivated cleanly.")
