import os
from flask import Flask, jsonify, render_template_string
import psycopg as psycopg2

app = Flask(__name__)

# Fallback setup: Uses cloud host connection strings if live on Render, otherwise uses local parameters
DATABASE_URL = os.environ.get(
    'DATABASE_URL', 
    'postgresql://defense_analyst:password123@127.0.0.1:5432/national_security_db'
)

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WIIINGS</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>✈️</text></svg>">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        :root {
            --amber-glow: #ffb000;
            --amber-bg: rgba(25, 18, 5, 0.85);
            --amber-border: rgba(255, 176, 0, 0.3);
            --dark-bg: #080b11;
        }

        body, html { 
            margin: 0; 
            padding: 0; 
            width: 100%; 
            height: 100%; 
            font-family: 'Courier New', Courier, monospace; 
            background: var(--dark-bg); 
            color: #fff; 
            overflow: hidden;
        }

        /* INTRO LANDING SCREEN */
        #landing-screen {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle inside, #111726 0%, var(--dark-bg) 100%);
            background-color: var(--dark-bg);
            z-index: 2000;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            transition: opacity 0.8s ease, transform 0.8s ease;
        }

        #landing-screen.hidden {
            opacity: 0;
            transform: scale(1.05);
            pointer-events: none;
        }

        .title-container {
            text-align: center;
            margin-bottom: 40px;
        }

        .main-title {
            font-size: 3.5rem;
            font-weight: 900;
            letter-spacing: 15px;
            color: #ffffff;
            margin: 0;
            text-shadow: 0 0 20px rgba(255, 255, 255, 0.2);
        }

        .subtitle {
            font-size: 0.9rem;
            letter-spacing: 5px;
            color: var(--amber-glow);
            margin-top: 15px;
            text-transform: uppercase;
            opacity: 0.8;
        }

        /* Tactical Terminal Button */
        .fly-btn {
            background: transparent;
            color: var(--amber-glow);
            border: 2px solid var(--amber-glow);
            padding: 15px 40px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 1.2rem;
            font-weight: bold;
            letter-spacing: 4px;
            text-transform: uppercase;
            cursor: pointer;
            border-radius: 4px;
            box-shadow: 0 0 10px rgba(255, 176, 0, 0.2);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .fly-btn:hover {
            background: var(--amber-glow);
            color: var(--dark-bg);
            box-shadow: 0 0 25px var(--amber-glow);
            transform: translateY(-2px);
        }

        .fly-btn:active {
            transform: translateY(1px);
        }

        /* MAIN APP INTERFACE CONTAINER */
        #app-container { 
            position: relative; 
            width: 100%; 
            height: 100%; 
            opacity: 0;
            transition: opacity 1s ease 0.3s;
        }
        
        #app-container.visible {
            opacity: 1;
        }

        #map { 
            width: 100%; 
            height: 100%; 
            background: #0d1117; 
        }

        #hud-header {
            position: absolute;
            top: 15px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            background: rgba(8, 11, 17, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 8px 20px;
            border-radius: 4px;
            pointer-events: none;
            text-align: center;
        }
        #hud-header h1 {
            margin: 0;
            font-size: 1rem;
            letter-spacing: 3px;
            color: rgba(255, 255, 255, 0.7);
        }

        #intel-overlay {
            position: absolute;
            bottom: 30px;
            right: 30px;
            width: 360px;
            max-width: calc(100vw - 60px);
            z-index: 1000;
            background: var(--amber-bg);
            border: 1px solid var(--amber-border);
            border-radius: 6px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5), 0 0 15px var(--amber-border);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            padding: 20px;
            box-sizing: border-box;
            opacity: 0;
            transform: translateY(20px) scale(0.98);
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
            pointer-events: none;
        }

        #intel-overlay.active {
            opacity: 1;
            transform: translateY(0) scale(1);
            pointer-events: auto;
        }

        .close-btn {
            position: absolute;
            top: 12px;
            right: 15px;
            color: var(--amber-glow);
            cursor: pointer;
            font-weight: bold;
            font-size: 1.1rem;
        }

        h2 { 
            margin: 0 0 15px 0; 
            color: var(--amber-glow); 
            border-bottom: 1px solid var(--amber-border); 
            padding-bottom: 8px; 
            font-size: 1.1rem; 
            letter-spacing: 1px; 
        }

        .meta-box { margin-bottom: 15px; }

        .stat-line { 
            margin: 10px 0; 
            font-size: 0.85rem; 
            display: flex;
            justify-content: space-between;
            border-bottom: 1px dashed rgba(255, 176, 0, 0.15);
            padding-bottom: 4px;
        }

        .label { color: rgba(255, 176, 0, 0.6); font-weight: bold; }
        .value { color: #ffffff; text-shadow: 0 0 4px rgba(255, 255, 255, 0.3); }

        @media (max-width: 480px) {
            .main-title { font-size: 2.2rem; letter-spacing: 8px; }
            #intel-overlay { bottom: 15px; right: 15px; left: 15px; width: auto; max-width: none; padding: 15px; }
            #hud-header { width: 80%; font-size: 0.8rem; }
        }
    </style>
</head>
<body>

<div id="landing-screen">
    <div class="title-container">
        <div class="main-title">WIIINGS</div>
        <div class="subtitle">Real-Time Air Traffic Stream Matrix</div>
    </div>
    <button class="fly-btn" onclick="initiateConsoleLaunch()">Let's Fly</button>
</div>

<div id="app-container">
    <div id="hud-header">
        <h1>WIIINGS ✈️</h1>
    </div>

    <div id="map"></div>
    
    <div id="intel-overlay">
        <span class="close-btn" onclick="closeIntelOverlay()">&times;</span>
        <div id="intel-content"></div>
    </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
    // System Transition Logic
    function initiateConsoleLaunch() {
        document.getElementById('landing-screen').classList.add('hidden');
        document.getElementById('app-container').classList.add('visible');
        
        // Trigger map layout validation once display area opacity kicks in
        setTimeout(() => {
            map.invalidateSize();
        }, 400);
    }

    const map = L.map('map', {
        zoomControl: false 
    }).setView([22.0, 78.0], 5);

    L.control.zoom({ position: 'topright' }).addTo(map);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO'
    }).addTo(map);

    let markers = {};

    const planeIcon = L.divIcon({
        className: 'custom-plane-icon',
        html: `<div style="transform: rotate(45deg); font-size: 22px; color: #00e5ff;">✈</div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });

    function closeIntelOverlay() {
        document.getElementById('intel-overlay').classList.remove('active');
    }

    async function updateFlightPositions() {
        try {
            const response = await fetch('/api/flights');
            const flights = await response.json();

            flights.forEach(flight => {
                const { icao24, callsign, origin_country, lat, lon, altitude, velocity } = flight;

                if (markers[icao24]) {
                    markers[icao24].setLatLng([lat, lon]);
                } else {
                    const marker = L.marker([lat, lon], { icon: planeIcon }).addTo(map);
                    
                    marker.on('click', () => {
                        const overlay = document.getElementById('intel-overlay');
                        
                        document.getElementById('intel-content').innerHTML = `
                            <h2>TARGET FIELD UPDATE</h2>
                            <div class="meta-box">
                                <div class="stat-line"><span class="label">CALLSIGN:</span> <span class="value" style="color:var(--amber-glow); font-weight:bold;">${callsign || 'UNKNOWN'}</span></div>
                                <div class="stat-line"><span class="label">HEX ADDR:</span> <span class="value">${icao24.toUpperCase()}</span></div>
                                <div class="stat-line"><span class="label">COUNTRY:</span> <span class="value">${origin_country}</span></div>
                            </div>
                            <h2>TELEMETRY MATRIX</h2>
                            <div class="meta-box" style="margin-bottom: 0;">
                                <div class="stat-line"><span class="label">ALTITUDE:</span> <span class="value">${altitude} m</span></div>
                                <div class="stat-line"><span class="label">VELOCITY:</span> <span class="value">${velocity} m/s</span></div>
                                <div class="stat-line"><span class="label">COORDINATES:</span> <span class="value">${lat.toFixed(4)}°, ${lon.toFixed(4)}°</span></div>
                            </div>
                        `;
                        
                        overlay.classList.add('active');
                    });

                    markers[icao24] = marker;
                }
            });
        } catch (err) {
            console.error("Telemetry streaming link interrupted:", err);
        }
    }

    setInterval(updateFlightPositions, 1500);
    updateFlightPositions();
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/flights')
def get_flights():
    """Queries PostGIS for the latest positional tracking frames of all aircraft."""
    try:
        # Dynamically leverages cloud or local configurations smoothly
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT icao24, callsign, origin_country, altitude_meters, velocity_mps,
                   ST_X(geom) as lon, ST_Y(geom) as lat 
            FROM live_aircraft_tracks;
        """)
        
        rows = cursor.fetchall()
        flights = []
        for r in rows:
            flights.append({
                "icao24": r[0],
                "callsign": r[1].strip() if r[1] else "UNKNOWN",
                "origin_country": r[2],
                "altitude": r[3],
                "velocity": r[4],
                "lon": r[5],
                "lat": r[6]
            })
        
        cursor.close()
        conn.close()
        return jsonify(flights)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Render binds ports via environment arrays; falls back to 5000 locally
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)