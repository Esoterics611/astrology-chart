import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for servers

from flask import Flask, render_template, request, jsonify
from skyfield.api import load, Topos
import matplotlib.pyplot as plt
import io
import base64
import numpy as np
from datetime import datetime, timezone

app = Flask(__name__)

# Load planetary ephemeris data
planets = load('de421.bsp')
earth, sun, moon = planets['earth'], planets['sun'], planets['moon']
mercury, venus, mars, jupiter, saturn, uranus, neptune, pluto = (
    planets['mercury'], planets['venus'], planets['mars'], planets['jupiter barycenter'],
    planets['saturn barycenter'], planets['uranus barycenter'], planets['neptune barycenter'], planets['pluto barycenter']
)

# Default location: Tel Aviv
DEFAULT_LATITUDE = 32.0853
DEFAULT_LONGITUDE = 34.7818
location = earth + Topos(latitude_degrees=DEFAULT_LATITUDE, longitude_degrees=DEFAULT_LONGITUDE)


def get_planet_positions(year=None, month=None, day=None, hour=None, minute=None):
    ts = load.timescale()
    
    # Default to current UTC time if no date/time is provided
    if None in (year, month, day, hour, minute):
        now = datetime.now(timezone.utc)
        year, month, day, hour, minute = now.year, now.month, now.day, now.hour, now.minute
    
    dt = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    observation_time = ts.utc(dt)

    planet_objects = {
        'Sun': sun,
        'Moon': moon,
        'Mercury': mercury,
        'Venus': venus,
        'Mars': mars,
        'Jupiter': jupiter,
        'Saturn': saturn,
        'Uranus': uranus,
        'Neptune': neptune,
        'Pluto': pluto
    }

    positions = []
    for planet, obj in planet_objects.items():
        astrometric = (location.at(observation_time).observe(obj)).apparent()
        ra, dec, distance = astrometric.radec()
        positions.append((planet, ra.hours, dec.degrees))
    return positions


def aspect_within_orb(angle1, angle2, aspect_angle, orb=4):
    """Check if two angles are within a specific orb of an aspect."""
    diff = abs(np.degrees(angle1) - np.degrees(angle2)) % 360
    return abs(diff - aspect_angle) <= orb


def generate_chart(positions):
    zodiac_signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    planet_icons = {
        'Sun': '☉', 'Moon': '☽', 'Mercury': '☿', 'Venus': '♀',
        'Mars': '♂', 'Jupiter': '♃', 'Saturn': '♄', 'Uranus': '♅',
        'Neptune': '♆', 'Pluto': '♇'
    }

    fig, ax = plt.subplots(figsize=(14, 14), subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location('W')
    ax.set_theta_direction(1)
    ax.set_facecolor('black')
    ax.spines['polar'].set_visible(False)

    # Add a darker central circle
    ax.fill_between(np.linspace(0, 2 * np.pi, 100), 0, 0.5, color='#1a1a1a')

    # Draw 12 Houses (30° each) with gray radial lines
    for i in range(12):
        theta = i * (360 / 12) * (np.pi / 180)
        ax.plot([theta, theta], [0, 1], color='gray', linestyle='--', lw=1)

    # Plot zodiac signs at the outer edge
    for i, sign in enumerate(zodiac_signs):
        theta = (i * 30) * (np.pi / 180)
        ax.text(theta + (np.pi / 12), 1.05, sign,
                ha='center', va='center', fontsize=14, color='white', fontweight='bold')

    # Plot planets with their icons and names
    planet_angles = []
    for planet, ra, dec in positions:
        theta = (ra / 24) * 360 * (np.pi / 180)
        icon = planet_icons.get(planet, '?')
        
        # Display Planet Icon
        ax.text(theta, 0.95, icon,
                fontsize=32, ha='center', va='center', fontweight='bold', color='gold')
        
        # Display Planet Name Below Icon
        ax.text(theta, 0.88, planet,
                fontsize=12, ha='center', va='center', fontweight='bold', color='white')
        
        planet_angles.append((planet, theta))

    # Draw aspects (squares, trines, sextiles)
    for i, (planet1, angle1) in enumerate(planet_angles):
        for j, (planet2, angle2) in enumerate(planet_angles):
            if i >= j:
                continue
            if aspect_within_orb(angle1, angle2, 90):
                ax.plot([angle1, angle2], [0.9, 0.9], color='red', lw=1.5)
            elif aspect_within_orb(angle1, angle2, 120):
                ax.plot([angle1, angle2], [0.9, 0.9], color='blue', lw=1.5)
            elif aspect_within_orb(angle1, angle2, 60):
                ax.plot([angle1, angle2], [0.9, 0.9], color='green', lw=1.5)

    ax.plot(np.linspace(0, 2 * np.pi, 100), np.ones(100), color='gold', lw=1.5)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor='black')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chart', methods=['POST'])
def chart():
    try:
        data = request.json
        year = data.get('year')
        month = data.get('month')
        day = data.get('day')
        hour = data.get('hour')
        minute = data.get('minute')

        positions = get_planet_positions(year, month, day, hour, minute)
        chart_image = generate_chart(positions)
        return jsonify({"chart": chart_image})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
