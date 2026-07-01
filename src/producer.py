import time
import json
import requests
from kafka import KafkaProducer

# Spatial Bounding Box for Indian Airspace Framework
INDIA_BOUNDING_BOX = {
    "lamin": 8.4,   # Latitude Min (South)
    "lamax": 37.6,  # Latitude Max (North)
    "lomin": 68.7,  # Longitude Min (West)
    "lomax": 97.25  # Longitude Max (East)
}

OPENSKY_URL = "https://opensky-network.org/api/states/all"
KAFKA_TOPIC = "air-traffic-telemetry"
KAFKA_SERVER = "localhost:9092"

def initialize_kafka_producer():
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_SERVER],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=5
        )
        print(f"[INFO] Ingestion engine linked to Kafka Broker at {KAFKA_SERVER}")
        return producer
    except Exception as e:
        print(f"[ERROR] Failed to establish connection to Kafka: {e}")
        exit(1)

def fetch_live_aircraft_data():
    try:
        response = requests.get(OPENSKY_URL, params=INDIA_BOUNDING_BOX, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("states", [])
        else:
            print(f"[WARNING] API handshake failed. HTTP Code: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network error contacting endpoint: {e}")
        return []

def process_and_stream():
    producer = initialize_kafka_producer()
    print("[SYSTEM READY] Commencing Real-Time Aerial Ingestion. Press Ctrl+C to terminate.")
    
    while True:
        start_time = time.time()
        raw_states = fetch_live_aircraft_data()
        
        if raw_states:
            active_count = 0
            for state in raw_states:
                # Discard telemetry points lacking raw geospatial coordinates
                if state[5] is None or state[6] is None:
                    continue
                
                telemetry_payload = {
                    "icao24": state[0].strip() if state[0] else "UNKNOWN",
                    "callsign": state[1].strip() if state[1] else "UNKN_CS",
                    "origin_country": state[2].strip() if state[2] else "UNKNOWN",
                    "longitude": state[5],
                    "latitude": state[6],
                    "altitude_meters": state[7] if state[7] else 0.0,
                    "velocity_mps": state[9] if state[9] else 0.0,
                    "timestamp": int(time.time())
                }
                
                producer.send(KAFKA_TOPIC, value=telemetry_payload)
                active_count += 1
            
            print(f"[SUCCESS] Broadcasted {active_count} telemetry payloads to topic '{KAFKA_TOPIC}'")
        else:
            print("[INFO] No tracking changes detected inside geographic bounds.")
        
        # OpenSky public server cooling window enforcement
        elapsed = time.time() - start_time
        time.sleep(max(10.0 - elapsed, 1.0))

if __name__ == "__main__":
    try:
        process_and_stream()
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Ingestion process halted by operator.")
        