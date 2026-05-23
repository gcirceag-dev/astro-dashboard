#!/usr/bin/env python3
"""
app.py - Dashboard Astro cu Streamlit
"""

import os
import math
import swisseph as swe
from skyfield.api import load, wgs84
from skyfield import almanac
from skyfield.searchlib import find_maxima
from datetime import datetime, timedelta
import pytz
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from importlib.resources import read_binary

# ═══════════════════════════════════════════════════════════════
# CONFIGURARE GLOBALĂ
# ═══════════════════════════════════════════════════════════════

EPHE_PATH = os.path.join(os.path.dirname(__file__), 'ephe')
swe.set_ephe_path(EPHE_PATH)

t0_jd = 2435555.5
ayan_t0 = 23.25
swe.set_sid_mode(swe.SIDM_USER, t0_jd, ayan_t0)

LAT, LON, ELEVATION = 44.42, 26.12, 70
TZ = pytz.timezone('Europe/Bucharest')

AU_TO_KM = 149597870.7
SYNODIC_MONTH = 29.530588853

# ═══════════════════════════════════════════════════════════════
# DATE STATICE
# ═══════════════════════════════════════════════════════════════

MANSIONS_LIST = [
    (1, "Al-Sharatain", "TBD", 0.0, 12.85),
    (2, "Al-Butain", "TBD", 12.85, 25.7),
    (3, "Al-Thuraiya", "TBD", 25.7, 38.57),
    (4, "Al-Dabaran", "TBD", 38.57, 51.42),
    (5, "Al-Haqa", "TBD", 51.42, 64.28),
    (6, "Al-Hana", "TBD", 64.28, 77.13),
    (7, "Al-Dhira", "TBD", 77.13, 90.0),
    (8, "Al-Nathrah", "TBD", 90.0, 102.85),
    (9, "Al-Tarf", "Privirea", 102.85, 115.7),
    (10, "Al-Jabhah", "TBD", 115.7, 128.57),
    (11, "Al-Zubrah", "TBD", 128.57, 141.42),
    (12, "Al-Sarfah", "TBD", 141.42, 154.28),
    (13, "Al-Awwa", "TBD", 154.28, 167.13),
    (14, "Al-Simak", "TBD", 167.13, 180.0),
    (15, "Al-Ghafr", "TBD", 180.0, 192.85),
    (16, "Al-Zubana", "TBD", 192.85, 205.7),
    (17, "Al-Iklil", "TBD", 205.7, 218.57),
    (18, "Al-Qalb", "TBD", 218.57, 231.42),
    (19, "Al-Shaulah", "TBD", 231.42, 244.28),
    (20, "Al-Naaim", "TBD", 244.28, 257.13),
    (21, "Al-Baldah", "TBD", 257.13, 270.0),
    (22, "Sa'd al-Dhabih", "TBD", 270.0, 282.85),
    (23, "Sa'd Bula", "TBD", 282.85, 295.7),
    (24, "Sa'd al-Suud", "TBD", 295.7, 308.57),
    (25, "Sa'd al-Akhbiyah", "TBD", 308.57, 321.42),
    (26, "Al-Fargh al-Awwal", "TBD", 321.42, 334.28),
    (27, "Al-Fargh al-Thani", "TBD", 334.28, 347.13),
    (28, "Batn al-Hut", "TBD", 347.13, 360.0),
]

NAKSHATRA_LIST = [
    (1, "Ashwini", 0.0, 13.3333),
    (2, "Bharani", 13.3333, 26.6667),
    (3, "Krittika", 26.6667, 40.0),
    (4, "Rohini", 40.0, 53.3333),
    (5, "Mrigashira", 53.3333, 66.6667),
    (6, "Ardra", 66.6667, 80.0),
    (7, "Punarvasu", 80.0, 93.3333),
    (8, "Pushya", 93.3333, 106.6667),
    (9, "Ashlesha", 106.6667, 120.0),
    (10, "Magha", 120.0, 133.3333),
    (11, "Purva Phalguni", 133.3333, 146.6667),
    (12, "Uttara Phalguni", 146.6667, 160.0),
    (13, "Hasta", 160.0, 173.3333),
    (14, "Chitra", 173.3333, 186.6667),
    (15, "Swati", 186.6667, 200.0),
    (16, "Vishakha", 200.0, 213.3333),
    (17, "Anuradha", 213.3333, 226.6667),
    (18, "Jyeshtha", 226.6667, 240.0),
    (19, "Mula", 240.0, 253.3333),
    (20, "Purva Ashadha", 253.3333, 266.6667),
    (21, "Uttara Ashadha", 266.6667, 280.0),
    (22, "Shravana", 280.0, 293.3333),
    (23, "Dhanishta", 293.3333, 306.6667),
    (24, "Shatabhisha", 306.6667, 320.0),
    (25, "Purva Bhadrapada", 320.0, 333.3333),
    (26, "Uttara Bhadrapada", 333.3333, 346.6667),
    (27, "Revati", 346.6667, 360.0),
]


IAU_CONSTELLATION_NAMES = {
    'And': 'Andromeda', 'Ant': 'Antlia', 'Aps': 'Apus', 'Aqr': 'Aquarius',
    'Aql': 'Aquila', 'Ara': 'Ara', 'Ari': 'Aries', 'Aur': 'Auriga',
    'Boo': 'Bootes', 'Cae': 'Caelum', 'Cam': 'Camelopardalis', 'Cnc': 'Cancer',
    'CVn': 'Canes Venatici', 'CMa': 'Canis Major', 'CMi': 'Canis Minor',
    'Cap': 'Capricornus', 'Car': 'Carina', 'Cas': 'Cassiopeia', 'Cen': 'Centaurus',
    'Cep': 'Cepheus', 'Cet': 'Cetus', 'Cha': 'Chamaeleon', 'Cir': 'Circinus',
    'Col': 'Columba', 'Com': 'Coma Berenices', 'CrA': 'Corona Australis',
    'CrB': 'Corona Borealis', 'Crv': 'Corvus', 'Crt': 'Crater', 'Cru': 'Crux',
    'Cyg': 'Cygnus', 'Del': 'Delphinus', 'Dor': 'Dorado', 'Dra': 'Draco',
    'Equ': 'Equuleus', 'Eri': 'Eridanus', 'For': 'Fornax', 'Gem': 'Gemini',
    'Gru': 'Grus', 'Her': 'Hercules', 'Hor': 'Horologium', 'Hya': 'Hydra',
    'Hyi': 'Hydrus', 'Ind': 'Indus', 'Lac': 'Lacerta', 'Leo': 'Leo',
    'LMi': 'Leo Minor', 'Lep': 'Lepus', 'Lib': 'Libra', 'Lup': 'Lupus',
    'Lyn': 'Lynx', 'Lyr': 'Lyra', 'Men': 'Mensa', 'Mic': 'Microscopium',
    'Mon': 'Monoceros', 'Mus': 'Musca', 'Nor': 'Norma', 'Oct': 'Octans',
    'Oph': 'Ophiuchus', 'Ori': 'Orion', 'Pav': 'Pavo', 'Peg': 'Pegasus',
    'Per': 'Perseus', 'Phe': 'Phoenix', 'Pic': 'Pictor', 'Psc': 'Pisces',
    'PsA': 'Piscis Austrinus', 'Pup': 'Puppis', 'Pyx': 'Pyxis', 'Ret': 'Reticulum',
    'Sge': 'Sagitta', 'Sgr': 'Sagittarius', 'Sco': 'Scorpius', 'Scl': 'Sculptor',
    'Sct': 'Scutum', 'Ser': 'Serpens', 'Sex': 'Sextans', 'Tau': 'Taurus',
    'Tel': 'Telescopium', 'Tri': 'Triangulum', 'TrA': 'Triangulum Australe',
    'Tuc': 'Tucana', 'UMa': 'Ursa Major', 'UMi': 'Ursa Minor', 'Vel': 'Vela',
    'Vir': 'Virgo', 'Vol': 'Volans', 'Vul': 'Vulpecula',
}


PLANET_IDS = {
    'Soare': swe.SUN, 'Luna': swe.MOON, 'Mercur': swe.MERCURY,
    'Venus': swe.VENUS, 'Marte': swe.MARS, 'Jupiter': swe.JUPITER,
    'Saturn': swe.SATURN, 'Uranus': swe.URANUS, 'Neptun': swe.NEPTUNE,
    'Pluto': swe.PLUTO,
}

ASTEROID_IDS = {
    'Chiron': swe.CHIRON, 'Ceres': swe.CERES, 'Pallas': swe.PALLAS,
    'Juno': swe.JUNO, 'Vesta': swe.VESTA,
}

SKYFIELD_NAMES = {
    'Soare': 'SUN', 'Luna': 'MOON', 'Mercur': 'MERCURY', 'Venus': 'VENUS',
    'Marte': 'MARS', 'Jupiter': 'JUPITER BARYCENTER', 'Saturn': 'SATURN BARYCENTER',
    'Uranus': 'URANUS BARYCENTER', 'Neptun': 'NEPTUNE BARYCENTER', 'Pluto': 'PLUTO BARYCENTER',
}

FIXED_STARS_LIST = [
    'Aldebaran', 'Regulus', 'Antares', 'Fomalhaut',
    'Spica', 'Sirius', 'Vega', 'Pollux', 'Castor',
    'Procyon', 'Betelgeuse', 'Rigel', 'Capella',
    'Deneb', 'Altair', 'Arcturus'
]

DIGNITIES = {
    'Soare': {'dom': 'Leo', 'ex': 'Ari', 'exil': 'Aqu', 'cad': 'Lib'},
    'Luna': {'dom': 'Can', 'ex': 'Tau', 'exil': 'Cap', 'cad': 'Sco'},
    'Mercur': {'dom': 'Gem/Vir', 'ex': 'Vir', 'exil': 'Sag/Pis', 'cad': 'Pis'},
    'Venus': {'dom': 'Tau/Lib', 'ex': 'Pis', 'exil': 'Sco/Ari', 'cad': 'Vir'},
    'Marte': {'dom': 'Ari/Sco', 'ex': 'Cap', 'exil': 'Lib/Tau', 'cad': 'Can'},
    'Jupiter': {'dom': 'Sag/Pis', 'ex': 'Can', 'exil': 'Gem/Vir', 'cad': 'Cap'},
    'Saturn': {'dom': 'Cap/Aqu', 'ex': 'Lib', 'exil': 'Can/Leo', 'cad': 'Ari'},
    'Uranus': {'dom': 'Aqu', 'ex': 'Sco', 'exil': 'Leo', 'cad': 'Tau'},
    'Neptun': {'dom': 'Pis', 'ex': 'Leo', 'exil': 'Vir', 'cad': 'Aqu'},
    'Pluto': {'dom': 'Sco', 'ex': 'Aqu', 'exil': 'Tau', 'cad': 'Leo'},
}

# ═══════════════════════════════════════════════════════════════
# ÎNCĂRCARE RESURSE
# ═══════════════════════════════════════════════════════════════

@st.cache_resource
def load_resources():
    """Încarcă toate resursele grele o singură dată"""
    ts = load.timescale()
    eph = load('de440s.bsp')
    earth = eph['earth']
    sun = eph['sun']
    moon = eph['moon']
    observer = earth + wgs84.latlon(LAT, LON, ELEVATION)
    
    return {
        'ts': ts,
        'eph': eph,
        'earth': earth,
        'sun': sun,
        'moon': moon,
        'observer': observer
    }

# ═══════════════════════════════════════════════════════════════
# FUNCȚII UTILITARE
# ═══════════════════════════════════════════════════════════════

def format_dms(decimal_degrees, is_latitude=False):
    sign = "-" if decimal_degrees < 0 else ""
    decimal_degrees = abs(decimal_degrees)
    d = int(decimal_degrees)
    m = int((decimal_degrees - d) * 60)
    s = round((decimal_degrees - d - m/60) * 3600, 2)
    if s >= 60:
        s -= 60
        m += 1
    if m >= 60:
        m -= 60
        d += 1
    return f"{sign}{d}° {m:02d}' {s:05.2f}\""

def format_zodiac(longitude):
    signs = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir',
             'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis']
    sign_idx = int(longitude // 30) % 12
    return f"{signs[sign_idx]} {format_dms(longitude % 30)}"

def get_dignity(name, lon):
    if name not in DIGNITIES:
        return ""
    signs = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis']
    current_sign = signs[int(lon // 30)]
    d = DIGNITIES[name]
    if current_sign in d['dom'].split('/'):
        return "D"
    elif current_sign == d['ex']:
        return "X"
    elif current_sign in d['exil'].split('/'):
        return "E"
    elif current_sign == d['cad']:
        return "C"
    return ""

def get_lunar_mansion(lon):
    for number, name, trans, start, end in MANSIONS_LIST:
        if start <= lon < end:
            return number, name, trans
    return None, None, None
    
def get_nakshatra(lon_sidereal):
    """Găsește Nakshatra și Pada pentru o longitudine siderală"""
    for number, name, start, end in NAKSHATRA_LIST:
        if start <= lon_sidereal < end:
            # Calculează Pada (1-4)
            pos_in_nakshatra = lon_sidereal - start
            pada = int(pos_in_nakshatra // 3.3333) + 1
            return number, name, pada
    return None, None, None

def get_real_constellation(ra_hours, dec_degrees):
    """Determină constelația IAU reală din coordonate ecuatoriale"""
    import numpy as np
    from importlib.resources import read_binary
    import io
    
    # Cache pentru grila de constelații (se încarcă o singură dată)
    if not hasattr(get_real_constellation, 'grid'):
        data = read_binary('skyfield.data', 'constellations.npz')
        npz = np.load(io.BytesIO(data))
        get_real_constellation.grid = {
            'sorted_ra': npz['sorted_ra'],
            'sorted_dec': npz['sorted_dec'],
            'radec_to_index': npz['radec_to_index'],
            'indexed_abbreviations': npz['indexed_abbreviations'],
        }
    
    grid = get_real_constellation.grid
    ra_idx = np.searchsorted(grid['sorted_ra'], ra_hours, side='right') - 1
    dec_idx = np.searchsorted(grid['sorted_dec'], dec_degrees, side='right') - 1
    
    ra_idx = max(0, min(ra_idx, grid['radec_to_index'].shape[0] - 2))
    dec_idx = max(0, min(dec_idx, grid['radec_to_index'].shape[1] - 2))
    
    const_idx = grid['radec_to_index'][ra_idx, dec_idx]
    abbrev = grid['indexed_abbreviations'][const_idx]
    
    return IAU_CONSTELLATION_NAMES.get(abbrev, abbrev)

def find_lunar_nodes_optimized(jd_start, jd_end):
    crossings = []
    step = 0.1
    jd_curr = jd_start
    prev_lat = swe.calc_ut(jd_curr, swe.MOON, swe.FLG_SWIEPH)[0][1]
    while jd_curr < jd_end:
        jd_curr += step
        curr_lat = swe.calc_ut(jd_curr, swe.MOON, swe.FLG_SWIEPH)[0][1]
        if prev_lat * curr_lat < 0:
            jd_left = jd_curr - step
            jd_right = jd_curr
            for _ in range(10):
                jd_mid = (jd_left + jd_right) / 2
                lat_mid = swe.calc_ut(jd_mid, swe.MOON, swe.FLG_SWIEPH)[0][1]
                if prev_lat * lat_mid < 0:
                    jd_right = jd_mid
                else:
                    jd_left = jd_mid
            crossings.append((jd_left + jd_right) / 2)
        prev_lat = curr_lat
    return crossings

def find_lunar_apsides_optimized(jd_start, jd_end):
    apsides = []
    step = 0.15
    jd_curr = jd_start
    prev_dist = swe.calc_ut(jd_curr, swe.MOON, swe.FLG_SWIEPH)[0][2]
    prev_diff = 1
    while jd_curr < jd_end:
        jd_curr += step
        curr_dist = swe.calc_ut(jd_curr, swe.MOON, swe.FLG_SWIEPH)[0][2]
        curr_diff = curr_dist - prev_dist
        if prev_diff * curr_diff < 0:
            jd_left = jd_curr - step
            jd_right = jd_curr
            for _ in range(10):
                jd_mid = (jd_left + jd_right) / 2
                dist_mid = swe.calc_ut(jd_mid, swe.MOON, swe.FLG_SWIEPH)[0][2]
                dist_left = swe.calc_ut(jd_left, swe.MOON, swe.FLG_SWIEPH)[0][2]
                if (dist_mid - dist_left) * prev_diff > 0:
                    jd_left = jd_mid
                else:
                    jd_right = jd_mid
            jd_exact = (jd_left + jd_right) / 2
            dist_exact = swe.calc_ut(jd_exact, swe.MOON, swe.FLG_SWIEPH)[0][2]
            apsides.append((jd_exact, dist_exact, prev_diff < 0))
        prev_dist = curr_dist
        prev_diff = curr_diff
    return apsides

def calculate_twilights_optimized(observer, sun, ts, midnight, now_local):
    twilights = []
    targets = [(-18, "Amurg astronomic"), (-12, "Amurg nautic"), (-6, "Amurg civil")]
    step_minutes = 4
    total_steps = int(24 * 60 / step_minutes)
    times_array = []
    alts_array = []
    for i in range(total_steps + 1):
        dt = midnight + timedelta(minutes=i * step_minutes)
        t = ts.from_datetime(dt.astimezone(pytz.UTC))
        alt, _, _ = observer.at(t).observe(sun).apparent().altaz()
        times_array.append(dt)
        alts_array.append(alt.degrees)
    
    twilight_times = []
    for target_alt, name in targets:
        for i in range(len(alts_array) - 1):
            if alts_array[i] < target_alt <= alts_array[i + 1]:
                fraction = (target_alt - alts_array[i]) / (alts_array[i + 1] - alts_array[i])
                exact_time = times_array[i] + timedelta(minutes=step_minutes * fraction)
                twilight_times.append((exact_time, f"{name} (dim)", exact_time.strftime('%H:%M:%S')))
                break
        for i in range(len(alts_array) - 1):
            if alts_array[i] > target_alt >= alts_array[i + 1]:
                fraction = (alts_array[i] - target_alt) / (alts_array[i] - alts_array[i + 1])
                exact_time = times_array[i] + timedelta(minutes=step_minutes * fraction)
                twilight_times.append((exact_time, f"{name} (seară)", exact_time.strftime('%H:%M:%S')))
                break
    
    twilight_times.sort(key=lambda x: x[0])
    return [(name, time_str) for _, name, time_str in twilight_times]

def find_next_mansion(jd, moon_lon, ts, tz):
    current_num, current_name, current_trans = get_lunar_mansion(moon_lon)
    if not current_num:
        return None
    next_num = current_num + 1 if current_num < 28 else 1
    next_start = MANSIONS_LIST[next_num - 1][3]
    moon_speed = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][3]
    distance_to_go = (next_start - moon_lon) % 360
    days_to_next = distance_to_go / moon_speed if moon_speed > 0 else 0
    jd_next = jd + days_to_next
    t_next = ts.tt_jd(jd_next)
    return {
        'current': f"{current_num}. {current_name} — {current_trans}" if current_trans != "TBD" else f"{current_num}. {current_name}",
        'next': f"{next_num}. {MANSIONS_LIST[next_num - 1][1]}",
        'next_date': t_next.astimezone(tz).strftime('%d %b %Y %H:%M')
    }

def get_planetary_hours(sunrise, sunset, sunrise_next, now_dt):
    """Calculează orele planetare"""
    if not all([sunrise, sunset, sunrise_next]):
        return [], None, 0, 0
    
    chaldean = ['Saturn', 'Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury', 'Moon']
    day_rulers = {0: 'Moon', 1: 'Mars', 2: 'Mercury', 3: 'Jupiter', 4: 'Venus', 5: 'Saturn', 6: 'Sun'}
    
    durata_zi = sunset - sunrise
    durata_noapte = sunrise_next - sunset
    lungime_ora_zi = durata_zi.total_seconds() / 12
    lungime_ora_noapte = durata_noapte.total_seconds() / 12
    
    if now_dt < sunrise:
        weekday = (sunrise.weekday() - 1) % 7
    else:
        weekday = sunrise.weekday()
    
    stapan_pornire = day_rulers[weekday]
    index_curent = chaldean.index(stapan_pornire)
    
    ore_zi = []
    timp_cursor = sunrise
    for i in range(12):
        planeta = chaldean[index_curent]
        start_ora = timp_cursor
        timp_cursor += timedelta(seconds=lungime_ora_zi)
        ore_zi.append((i + 1, planeta, start_ora, timp_cursor, 'zi'))
        index_curent = (index_curent + 1) % 7
    
    ore_noapte = []
    timp_cursor = sunset
    for i in range(12):
        planeta = chaldean[index_curent]
        start_ora = timp_cursor
        timp_cursor += timedelta(seconds=lungime_ora_noapte)
        ore_noapte.append((i + 1, planeta, start_ora, timp_cursor, 'noapte'))
        index_curent = (index_curent + 1) % 7

    
    current_hour = None
    for ore in [ore_zi, ore_noapte]:
        for num, planet, start, end, tip in ore:
            if start <= now_dt < end:
                current_hour = (num, planet, start, end, tip)
                break
        if current_hour:
            break
    
    return ore_zi + ore_noapte, current_hour, lungime_ora_zi, lungime_ora_noapte

# ═══════════════════════════════════════════════════════════════
# CACHE PENTRU CALCULE
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def get_positions_data(jd):
    data = {}
    data['ayanamsa'] = swe.get_ayanamsa_ut(jd)
    ecl_nut = swe.calc_ut(jd, swe.ECL_NUT)
    data['obliquity'] = ecl_nut[0][0]
    data['sidereal_time'] = (swe.sidtime(jd) + LON/15.0) % 24
    
    sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
    data['sun_lon'] = sun_pos[0]
    data['sun_lat'] = sun_pos[1]
    data['sun_dist'] = sun_pos[2]
    data['sun_speed'] = sun_pos[3]
    data['sun_equ'] = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)[0]
    data['sun_xyz'] = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_XYZ)[0]
    
    moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
    data['moon_lon'] = moon_pos[0]
    data['moon_lat'] = moon_pos[1]
    data['moon_dist'] = moon_pos[2]
    data['moon_speed'] = moon_pos[3]
    data['moon_equ'] = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)[0]
    data['moon_xyz'] = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_XYZ)[0]
    
    data['arc_sl'] = (data['moon_lon'] - data['sun_lon']) % 360
    
    planet_data = {}
    for name, pid in PLANET_IDS.items():
        pos = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
        planet_data[name] = {'lon': pos[0], 'lat': pos[1], 'dist': pos[2], 'speed': pos[3], 'retro': pos[3] < 0}
    
    nn_pos = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SWIEPH)[0]
    planet_data['Nod Nord (Mean)'] = {'lon': nn_pos[0], 'lat': nn_pos[1], 'dist': nn_pos[2], 'speed': nn_pos[3], 'retro': False}
    planet_data['Nod Sud (Mean)'] = {'lon': (nn_pos[0] + 180) % 360, 'lat': -nn_pos[1], 'dist': nn_pos[2], 'speed': nn_pos[3], 'retro': False}
    lilith_pos = swe.calc_ut(jd, swe.MEAN_APOG, swe.FLG_SWIEPH)[0]
    planet_data['Lilith (Mean)'] = {'lon': lilith_pos[0], 'lat': lilith_pos[1], 'dist': lilith_pos[2], 'speed': lilith_pos[3], 'retro': False}
    
    for name, aid in ASTEROID_IDS.items():
        pos = swe.calc_ut(jd, aid, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
        planet_data[name] = {'lon': pos[0], 'lat': pos[1], 'dist': pos[2], 'speed': pos[3], 'retro': pos[3] < 0}
    
    fixed_stars_names = []
    for star_name in FIXED_STARS_LIST:
        try:
            star_data, star_name_ret, _ = swe.fixstar_ut(star_name, jd, swe.FLG_SWIEPH)
            if star_name_ret not in planet_data:
                planet_data[star_name_ret] = {'lon': star_data[0], 'lat': star_data[1], 'dist': 0, 'speed': 0, 'retro': False}
                fixed_stars_names.append(star_name_ret)
        except:
            pass
    
    data['planet_data'] = planet_data
    data['fixed_stars_names'] = fixed_stars_names
    
    cusps, ascmc = swe.houses_ex(jd, LAT, LON, b'P')
    data['ascendant'] = ascmc[0]
    data['mc'] = ascmc[1]
    
    seasons = {(0, 90): "Primăvară", (90, 180): "Vară", (180, 270): "Toamnă", (270, 360): "Iarnă"}
    data['current_season'] = next((name for (s, e), name in seasons.items() if s <= data['sun_lon'] < e), None)
    
    mansion_num, mansion_name, mansion_trans = get_lunar_mansion(data['moon_lon'])
    data['mansion_num'] = mansion_num
    data['mansion_name'] = mansion_name
    data['mansion_trans'] = mansion_trans
    
    return data

@st.cache_data(ttl=60)
def get_observational_data(now_utc):
    resources = load_resources()
    ts = resources['ts']
    eph = resources['eph']
    observer = resources['observer']
    sun = resources['sun']
    moon = resources['moon']
    
    now_local = now_utc.astimezone(TZ)
    t_now = ts.from_datetime(now_utc)
    jd = swe.julday(now_utc.year, now_utc.month, now_utc.day,
                    now_utc.hour + now_utc.minute/60.0 + now_utc.second/3600.0)
    
    data = {'jd': jd}
    
    sun_app = observer.at(t_now).observe(sun).apparent()
    sun_alt, sun_az, _ = sun_app.altaz()
    data['sun_alt'] = sun_alt.degrees
    data['sun_az'] = sun_az.degrees
    
    moon_app = observer.at(t_now).observe(moon).apparent()
    moon_alt, moon_az, _ = moon_app.altaz()
    data['moon_alt'] = moon_alt.degrees
    data['moon_az'] = moon_az.degrees
    
    data['moon_illum'] = almanac.fraction_illuminated(eph, 'moon', t_now)
    
    t0 = ts.from_datetime(now_utc.replace(hour=0, minute=0, second=0))
    t1 = ts.from_datetime((now_utc + timedelta(days=1)).replace(hour=0, minute=0, second=0))
    f_rs = almanac.sunrise_sunset(eph, wgs84.latlon(LAT, LON))
    times_rs, events_rs = almanac.find_discrete(t0, t1, f_rs)
    
    sunrise_today = None
    sunset_today = None
    for t, ev in zip(times_rs, events_rs):
        if ev == 1:
            sunrise_today = t.astimezone(TZ)
        else:
            sunset_today = t.astimezone(TZ)
    data['sunrise_today'] = sunrise_today
    data['sunset_today'] = sunset_today
    
    t0_tom = ts.from_datetime((now_utc + timedelta(days=1)).replace(hour=0, minute=0, second=0))
    t1_tom = ts.from_datetime((now_utc + timedelta(days=2)).replace(hour=0, minute=0, second=0))
    times_rs_tom, events_rs_tom = almanac.find_discrete(t0_tom, t1_tom, f_rs)
    sunrise_next = None
    for t, ev in zip(times_rs_tom, events_rs_tom):
        if ev == 1:
            sunrise_next = t.astimezone(TZ)
            break
    data['sunrise_next'] = sunrise_next

    # CALCULĂM APUSUL DE IERI (necesar pentru orele planetare înainte de răsărit)
    yesterday = now_utc - timedelta(days=1)
    t0_yest = ts.from_datetime(yesterday.replace(hour=0, minute=0, second=0))
    t1_yest = ts.from_datetime((yesterday + timedelta(days=1)).replace(hour=0, minute=0, second=0))
    times_rs_yest, events_rs_yest = almanac.find_discrete(t0_yest, t1_yest, f_rs)
    sunset_yesterday = None
    for t, ev in zip(times_rs_yest, events_rs_yest):
        if ev == 0:
            sunset_yesterday = t.astimezone(TZ)
    
    data['sunrise_az'] = None
    data['sunset_az'] = None
    if sunrise_today is not None:
        t_sr = ts.from_datetime(sunrise_today.astimezone(pytz.UTC))
        _, az_sr, _ = observer.at(t_sr).observe(sun).apparent().altaz()
        data['sunrise_az'] = az_sr.degrees
    if sunset_today is not None:
        t_ss = ts.from_datetime(sunset_today.astimezone(pytz.UTC))
        _, az_ss, _ = observer.at(t_ss).observe(sun).apparent().altaz()
        data['sunset_az'] = az_ss.degrees
    
    f_mt = almanac.meridian_transits(eph, sun, wgs84.latlon(LAT, LON))
    times_mt, events_mt = almanac.find_discrete(t0, t1, f_mt)
    data['culm_sup'] = None
    data['culm_inf'] = None
    data['alt_culm_sup'] = None
    data['alt_culm_inf'] = None
    for t, ev in zip(times_mt, events_mt):
        alt_mt, _, _ = observer.at(t).observe(sun).apparent().altaz()
        if ev == 1:
            data['culm_sup'] = t.astimezone(TZ)
            data['alt_culm_sup'] = alt_mt.degrees
        else:
            data['culm_inf'] = t.astimezone(TZ)
            data['alt_culm_inf'] = alt_mt.degrees
    
    midnight_today_utc = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    t0_moon = ts.from_datetime(midnight_today_utc)
    t1_moon = ts.from_datetime(midnight_today_utc + timedelta(days=1))
    f_mr = almanac.risings_and_settings(eph, moon, wgs84.latlon(LAT, LON))
    times_mr, events_mr = almanac.find_discrete(t0_moon, t1_moon, f_mr)
    data['moonrise_next'] = None
    data['moonset_next'] = None
    for t, ev in zip(times_mr, events_mr):
        if ev == 1:
            data['moonrise_next'] = t.astimezone(TZ)
        else:
            data['moonset_next'] = t.astimezone(TZ)
    
    f_mc = almanac.meridian_transits(eph, moon, wgs84.latlon(LAT, LON))
    times_mc, events_mc = almanac.find_discrete(t0_moon, t1_moon, f_mc)
    data['moon_culm_sup'] = None
    data['moon_culm_inf'] = None
    data['moon_alt_culm_sup'] = None
    data['moon_alt_culm_inf'] = None
    for t, ev in zip(times_mc, events_mc):
        alt_mc, _, _ = observer.at(t).observe(moon).apparent().altaz()
        if ev == 1:
            data['moon_culm_sup'] = t.astimezone(TZ)
            data['moon_alt_culm_sup'] = alt_mc.degrees
        else:
            data['moon_culm_inf'] = t.astimezone(TZ)
            data['moon_alt_culm_inf'] = alt_mc.degrees
    
    midnight_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    data['twilights'] = calculate_twilights_optimized(observer, sun, ts, midnight_local, now_local)
    
    # Determinăm sunset-ul corect pentru orele planetare
    # Dacă suntem înainte de răsărit, noaptea a început ieri, deci folosim sunset-ul de ieri
    if now_local < sunrise_today:
        # Calculăm apusul de ieri
        yesterday = now_utc - timedelta(days=1)
        t0_yest = ts.from_datetime(yesterday.replace(hour=0, minute=0, second=0))
        t1_yest = ts.from_datetime((yesterday + timedelta(days=1)).replace(hour=0, minute=0, second=0))
        times_rs_yest, events_rs_yest = almanac.find_discrete(t0_yest, t1_yest, f_rs)
        sunset_yesterday = None
        for t, ev in zip(times_rs_yest, events_rs_yest):
            if ev == 0:  # apus
                sunset_yesterday = t.astimezone(TZ)
        sunset_for_hours = sunset_yesterday
    else:
        sunset_for_hours = sunset_today
    
    # Determinăm sunset-ul și sunrise_next corecte pentru orele planetare
    if now_local < sunrise_today:
        sunset_for_hours = sunset_yesterday
        sunrise_next_for_hours = sunrise_today
    else:
        sunset_for_hours = sunset_today
        sunrise_next_for_hours = sunrise_next
    
    data['hours_plan'], data['current_hour'], data['day_h'], data['night_h'] = get_planetary_hours(
        sunrise_today, sunset_for_hours, sunrise_next_for_hours, now_local
    )
    
    moon_lon = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)[0][0]
    sun_lon = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)[0][0]
    data['arc_sl'] = (moon_lon - sun_lon) % 360
    data['moon_age'] = data['arc_sl'] / 360 * SYNODIC_MONTH
    
    illum = data['moon_illum']
    if illum < 0.01:
        data['moon_phase_name'] = "Lună Nouă"
    elif illum < 0.499:
        data['moon_phase_name'] = "Crescătoare" if data['arc_sl'] < 180 else "Descrescătoare"
    elif illum < 0.501:
        data['moon_phase_name'] = "Lună Plină"
    else:
        data['moon_phase_name'] = "Crescătoare" if data['arc_sl'] < 180 else "Descrescătoare"
    
    return data

@st.cache_data(ttl=300)
def get_long_term_events(now_utc):
    resources = load_resources()
    ts = resources['ts']
    eph = resources['eph']
    earth = resources['earth']
    sun = resources['sun']
    moon = resources['moon']
    
    now_local = now_utc.astimezone(TZ)
    jd = swe.julday(now_utc.year, now_utc.month, now_utc.day,
                    now_utc.hour + now_utc.minute/60.0 + now_utc.second/3600.0)
    
    data = {}
    
    t_ph_start = ts.from_datetime(datetime(now_utc.year, 1, 1, tzinfo=pytz.UTC))
    t_ph_end = ts.from_datetime(datetime(now_utc.year + 1, 1, 1, tzinfo=pytz.UTC))
    step_days = 0.5
    times_ph = []
    distances_ph = []
    t = t_ph_start
    while t.tt < t_ph_end.tt:
        jd_t = swe.julday(t.utc.year, t.utc.month, t.utc.day, t.utc.hour + t.utc.minute/60.0)
        dist = swe.calc_ut(jd_t, swe.SUN, swe.FLG_SWIEPH)[0][2]
        times_ph.append(t)
        distances_ph.append(dist)
        t = ts.tt_jd(t.tt + step_days)
    
    if distances_ph:
        min_idx = distances_ph.index(min(distances_ph))
        max_idx = distances_ph.index(max(distances_ph))
        data['perihelion_t'] = times_ph[min_idx]
        data['perihelion_d'] = distances_ph[min_idx] * AU_TO_KM
        data['aphelion_t'] = times_ph[max_idx]
        data['aphelion_d'] = distances_ph[max_idx] * AU_TO_KM
    else:
        data['perihelion_t'] = None
        data['perihelion_d'] = 0
        data['aphelion_t'] = None
        data['aphelion_d'] = 0
    
    t_start_eq = ts.from_datetime(now_utc)
    t_end_eq = ts.from_datetime(datetime(now_utc.year + 2, 1, 1, tzinfo=pytz.UTC))
    f_seasons = almanac.seasons(eph)
    times_s, events_s = almanac.find_discrete(t_start_eq, t_end_eq, f_seasons)
    s_names = {0: 'Echinocțiul de primăvară', 1: 'Solstițiul de vară', 2: 'Echinocțiul de toamnă', 3: 'Solstițiul de iarnă'}
    data['next_seasons'] = []
    for t, ev in zip(times_s, events_s):
        if len(data['next_seasons']) >= 4:
            break
        data['next_seasons'].append((s_names[ev], t.astimezone(TZ).strftime('%Y-%m-%d %H:%M:%S')))
    
    t_faze_start = ts.from_datetime(now_utc - timedelta(days=20))
    t_faze_end = ts.from_datetime(now_utc + timedelta(days=35))
    f_moon_phases = almanac.moon_phases(eph)
    times_faze, events_faze = almanac.find_discrete(t_faze_start, t_faze_end, f_moon_phases)
    faze_names = {0: "Lună Nouă 🌑", 1: "Primul Pătrar 🌓", 2: "Lună Plină 🌕", 3: "Ultimul Pătrar 🌗"}
    data['moon_phases'] = []
    data['moon_phases_all'] = []
    for t_f, ev_f in zip(times_faze, events_faze):
        if ev_f in faze_names:
            phase_info = (faze_names[ev_f], t_f.astimezone(TZ).strftime('%d %b %Y %H:%M'))
            data['moon_phases_all'].append(phase_info)
            if t_f.astimezone(TZ) >= now_local:
                data['moon_phases'].append(phase_info)
    
    jd_start_nodes = jd - 25
    jd_end_nodes = jd + 35
    node_jds = find_lunar_nodes_optimized(jd_start_nodes, jd_end_nodes)
    data['moon_nodes_all'] = []
    data['moon_nodes_all_time'] = []
    for jd_node in node_jds[:6]:
        t_node = ts.tt_jd(jd_node)
        moon_lat_before = swe.calc_ut(jd_node - 0.05, swe.MOON, swe.FLG_SWIEPH)[0][1]
        moon_lat_after = swe.calc_ut(jd_node + 0.05, swe.MOON, swe.FLG_SWIEPH)[0][1]
        label = "Nod Ascendent (☊)" if moon_lat_after > moon_lat_before else "Nod Descendent (☋)"
        data['moon_nodes_all_time'].append((label, t_node))
        data['moon_nodes_all'].append((label, t_node.astimezone(TZ).strftime('%d %b %Y %H:%M')))
    
    # NOUA METODĂ: Skyfield find_maxima (mai precisă)
    def moon_distance_km(t):
        return earth.at(t).observe(moon).distance().km
    moon_distance_km.rough_period = 27.5
    
    def neg_moon_distance_km(t):
        return -earth.at(t).observe(moon).distance().km
    neg_moon_distance_km.rough_period = 27.5
    
    t_pg_start = ts.from_datetime(now_utc - timedelta(days=30))
    t_pg_end = ts.from_datetime(now_utc + timedelta(days=30))
    
    apogee_times, apogee_distances = find_maxima(t_pg_start, t_pg_end, moon_distance_km)
    perigee_times, perigee_distances_neg = find_maxima(t_pg_start, t_pg_end, neg_moon_distance_km)
    perigee_distances = [-d for d in perigee_distances_neg]
    
    all_apogees = [(t, d) for t, d in zip(apogee_times, apogee_distances)]
    all_perigees = [(t, d) for t, d in zip(perigee_times, perigee_distances)]
    data['next_perigee'] = next(((t, d) for t, d in all_perigees if t.astimezone(TZ) > now_local), None)
    data['next_apogee'] = next(((t, d) for t, d in all_apogees if t.astimezone(TZ) > now_local), None)
    
    all_events = []
    for t, dist in all_perigees:
        all_events.append(('P', t, dist))
    for t, dist in all_apogees:
        all_events.append(('A', t, dist))
    all_events.sort(key=lambda x: x[1].tt)
    
    prev_event = None
    next_event = None
    for label, t_exact, d_exact in all_events:
        if t_exact.astimezone(TZ) <= now_local:
            prev_event = (label, t_exact, d_exact)
        elif next_event is None:
            next_event = (label, t_exact, d_exact)
            break
    data['prev_ap_event'] = prev_event
    data['next_ap_event'] = next_event
    
    data['all_lunar_events'] = get_unified_lunar_events(now_utc, ts, eph, earth, moon)
    moon_lon = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)[0][0]
    data['next_mansion'] = find_next_mansion(jd, moon_lon, ts, TZ)
    
    return data

def get_unified_lunar_events(now_utc, ts, eph, earth, moon):
    events = []
    t_start = ts.from_datetime(now_utc)
    t_end = ts.from_datetime(now_utc + timedelta(days=35))
    f_phases = almanac.moon_phases(eph)
    phases_times, phases_events = almanac.find_discrete(t_start, t_end, f_phases)
    phase_names = {0: "Lună Nouă 🌑", 1: "Primul Pătrar 🌓", 2: "Lună Plină 🌕", 3: "Ultimul Pătrar 🌗"}
    for t, ev in zip(phases_times, phases_events):
        if ev in phase_names:
            events.append((t, phase_names[ev], 'phase'))
    
    jd_now = swe.julday(now_utc.year, now_utc.month, now_utc.day,
                        now_utc.hour + now_utc.minute/60.0 + now_utc.second/3600.0)
    jd_end = jd_now + 35
    node_jds = find_lunar_nodes_optimized(jd_now, jd_end)
    for jd_node in node_jds:
        t_node = ts.tt_jd(jd_node)
        moon_lat_before = swe.calc_ut(jd_node - 0.05, swe.MOON, swe.FLG_SWIEPH)[0][1]
        moon_lat_after = swe.calc_ut(jd_node + 0.05, swe.MOON, swe.FLG_SWIEPH)[0][1]
        label = "Nod Ascendent (☊)" if moon_lat_after > moon_lat_before else "Nod Descendent (☋)"
        events.append((t_node, label, 'node'))
    
    # Perigeu/Apogeu - metoda Skyfield nativă
    def moon_distance_km(t):
        return earth.at(t).observe(moon).distance().km
    moon_distance_km.rough_period = 27.5
    
    def neg_moon_distance_km(t):
        return -earth.at(t).observe(moon).distance().km
    neg_moon_distance_km.rough_period = 27.5
    
    t_apsides_start = ts.from_datetime(now_utc)
    t_apsides_end = ts.from_datetime(now_utc + timedelta(days=45))
    
    apogee_times, apogee_distances = find_maxima(t_apsides_start, t_apsides_end, moon_distance_km)
    perigee_times, perigee_distances_neg = find_maxima(t_apsides_start, t_apsides_end, neg_moon_distance_km)
    perigee_distances = [-d for d in perigee_distances_neg]
    
    for t, d in zip(apogee_times, apogee_distances):
        events.append((t, f"Apogeu ⬆ {d:,.0f} km", 'apogee'))
    
    for t, d in zip(perigee_times, perigee_distances):
        events.append((t, f"Perigeu ⬇ {d:,.0f} km", 'perigee'))
    
    events.sort(key=lambda x: x[0].tt)
    return events
    

def find_ingresses(jd_now, planet_data, max_days=3):
    """Găsește intrări în zodie nouă în următoarele max_days zile"""
    signs = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis']
    ingresses = []
    
    for name in ['Soare', 'Luna', 'Mercur', 'Venus', 'Marte', 'Jupiter', 'Saturn']:
        if name not in planet_data:
            continue
        
        current_lon = planet_data[name]['lon']
        speed = planet_data[name]['speed']
        current_sign_idx = int(current_lon // 30)
        next_sign_idx = (current_sign_idx + 1) % 12
        next_sign_start = next_sign_idx * 30
        
        distance = (next_sign_start - current_lon) % 360
        if speed > 0:
            days_to_ingress = distance / speed
        else:
            continue
        
        if 0 < days_to_ingress <= max_days:
            jd_ingress = jd_now + days_to_ingress
            dt_ingress = jd_to_datetime(jd_ingress)
            ingresses.append((name, signs[next_sign_idx], dt_ingress, days_to_ingress))
    
    ingresses.sort(key=lambda x: x[3])
    return ingresses


def jd_to_datetime(jd):
    """Convert JD to datetime in local timezone"""
    from datetime import datetime as dt
    year, month, day, hour_f = swe.revjul(jd, swe.GREG_CAL)
    hour = int(hour_f)
    minute = int((hour_f - hour) * 60)
    second = int(((hour_f - hour) * 60 - minute) * 60)
    return datetime(year, month, day, hour, minute, second, tzinfo=TZ)


def get_summary_events(now_local, positions, observational, long_term):
    """Colectează toate evenimentele pentru Sumar"""
    events = {'soare': [], 'luna': [], 'retrograde': [], 'ingress': [], 'aspecte': []}
    now_utc = now_local.astimezone(pytz.UTC)
    
    # ☀️ SOARE
    perihelion_t = long_term.get('perihelion_t')
    aphelion_t = long_term.get('aphelion_t')
    for event_t, label, km in [
        (perihelion_t, '☀️ Periheliu', long_term.get('perihelion_d', 0)),
        (aphelion_t, '☀️ Afeliu', long_term.get('aphelion_d', 0))
    ]:
        if event_t is not None:
            dt = event_t.astimezone(TZ) if hasattr(event_t, 'astimezone') else event_t
            days = (dt - now_local).total_seconds() / 86400
            if 0 <= days <= 3:
                events['soare'].append(f"{label} în {int(days)}z ({dt.strftime('%d %b %H:%M')}, {km:,.0f} km)")
    
    for name, date_str in long_term.get('next_seasons', []):
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            dt = TZ.localize(dt)
            days = (dt - now_local).total_seconds() / 86400
            if 0 <= days <= 3:
                events['soare'].append(f"🌱 {name} în {int(days)}z ({dt.strftime('%d %b %H:%M')})")
        except:
            pass
    
    # LUNA
    for label, date_str in long_term.get('moon_phases_all', []):
        try:
            dt = TZ.localize(datetime.strptime(date_str, '%d %b %Y %H:%M'))
            days = (dt - now_local).total_seconds() / 86400
            if 0 <= days <= 2:
                events['luna'].append(f"{label} în {int(days)}z {int((days%1)*24)}h ({date_str})")
        except:
            pass
    
    for label, t_node in long_term.get('moon_nodes_all_time', []):
        dt = t_node.astimezone(TZ)
        days = (dt - now_local).total_seconds() / 86400
        if 0 <= days <= 2:
            events['luna'].append(f"{label} în {int(days)}z {int((days%1)*24)}h ({dt.strftime('%d %b %H:%M')})")
    
    for prefix, event_data in [('⬇', long_term.get('next_perigee')), ('⬆', long_term.get('next_apogee'))]:
        if event_data is not None:
            t, d = event_data
            dt = t.astimezone(TZ) if hasattr(t, 'astimezone') else t
            days = (dt - now_local).total_seconds() / 86400
            if 0 <= days <= 2:
                events['luna'].append(f"{prefix} {'Perigeu' if prefix=='⬇' else 'Apogeu'} în {int(days)}z {int((days%1)*24)}h ({dt.strftime('%d %b %H:%M')}, {d:,.0f} km)")
    
    mansion_info = long_term.get('next_mansion')
    if mansion_info is not None:
        events['luna'].append(f"**Conacul {mansion_info['current']}**")
        events['luna'].append(f"→ **{mansion_info['next']}** ({mansion_info['next_date']})")
    
    # RETROGRADE
    retro_list = []
    planet_data = positions.get('planet_data', {})
    for name in ['Mercur', 'Venus', 'Marte', 'Jupiter', 'Saturn', 'Uranus', 'Neptun', 'Pluto']:
        if name in planet_data and planet_data[name].get('retro'):
            retro_list.append(name)
    if retro_list:
        events['retrograde'] = [f" {', '.join(retro_list)} retrograd"]
    
    # INGRESSURI
    jd_now = observational.get('jd', swe.julday(now_local.year, now_local.month, now_local.day,
                                                 now_local.hour + now_local.minute/60))
    ingresses = find_ingresses(jd_now, planet_data, max_days=3)
    for name, sign, dt, days in ingresses:
        events['ingress'].append(f"{name} intră în {sign} în {int(days)}z {int((days%1)*24)}h ({dt.strftime('%d %b %H:%M')})")
    
    # ASPECTE (doar planete cu planete lente, sau planete cu stele fixe)
    planet_data_full = positions.get('planet_data', {})
    aspect_types = {'Conjuncție ☌': 0, 'Sextil ⚹': 60, 'Careu □': 90, 'Trigon △': 120, 'Opoziție ☍': 180}
    
    # Planete rapide (nu le combinăm între ele)
    fast_planets = ['Soare', 'Luna', 'Mercur', 'Venus', 'Marte']
    # Planete lente
    slow_planets = ['Jupiter', 'Saturn', 'Uranus', 'Neptun', 'Pluto']
    # Toate planetele
    all_planets = fast_planets + slow_planets
    # Stele fixe
    fixed_stars = positions.get('fixed_stars_names', [])
    
    # Lista de corpuri de comparat: planete + stele fixe
    bodies_to_check = all_planets + fixed_stars
    
    for i, body1 in enumerate(bodies_to_check):
        if body1 not in planet_data_full:
            continue
        lon1 = planet_data_full[body1]['lon']
        
        for j, body2 in enumerate(bodies_to_check):
            if j <= i or body2 not in planet_data_full:
                continue
            
            # Sărim combinațiile Soare-Luna, rapid-rapid, stea-stea
            if body1 in fast_planets and body2 in fast_planets:
                continue  # fără rapid-rapid
            if body1 in fixed_stars and body2 in fixed_stars:
                continue  # fără stea-stea
            
            lon2 = planet_data_full[body2]['lon']
            diff = abs(lon2 - lon1)
            if diff > 180:
                diff = 360 - diff
            
            for aspect_name, aspect_angle in aspect_types.items():
                angle_diff = abs(diff - aspect_angle)
                if angle_diff <= 2.0:
                    # Pentru stele fixe, arată doar conjuncțiile
                    if (body1 in fixed_stars or body2 in fixed_stars) and aspect_angle != 0:
                        continue
                    events['aspecte'].append(f"{body1} – {body2}: {aspect_name} ({format_dms(angle_diff)})")
                    
    # Sortează aspectele după orb (diferența în grade, extrasă din paranteză)
    import re
    def extract_orb(aspect_str):
        match = re.search(r'\((.*?)\)', aspect_str)
        if match:
            dms = match.group(1)
            parts = dms.replace('°', '').replace("'", '').replace('"', '').split()
            if len(parts) == 3:
                return float(parts[0]) + float(parts[1])/60 + float(parts[2])/3600
            elif len(parts) == 2:
                return float(parts[0]) + float(parts[1])/60
            else:
                return float(parts[0])
        return 999
    
    events['aspecte'].sort(key=extract_orb)
    
    return events

# ═══════════════════════════════════════════════════════════════
# COMPONENTE GRAFICE
# ═══════════════════════════════════════════════════════════════

def create_moon_phase_plotly(moon_illum, is_waning):
    """
    Faza Lunii - CERC (nu oval), cu terminator eliptic
    Replică fidelă a codului Matplotlib original
    """
    import numpy as np
    
    iluminare_procent = moon_illum * 100
    
    c_lumina = '#fefeec'
    c_umbra = '#2c2c2c'
    
    if not is_waning:
        stanga_color = c_umbra
        dreapta_color = c_lumina
        elipsa_color = c_umbra if iluminare_procent < 50 else c_lumina
    else:
        stanga_color = c_lumina
        dreapta_color = c_umbra
        elipsa_color = c_lumina if iluminare_procent < 50 else c_umbra
    
    fig = go.Figure()
    
    # SEMICERCUL STÂNG (90° la 270°)
    theta_left = np.linspace(np.pi/2, 3*np.pi/2, 150)
    x_left = np.cos(theta_left)
    y_left = np.sin(theta_left)
    # Închidem forma: adăugăm punctul (0,0) la final
    x_left_closed = np.append(x_left, 0)
    y_left_closed = np.append(y_left, 0)
    
    fig.add_trace(go.Scatter(
        x=x_left_closed, y=y_left_closed,
        fill='toself',
        fillcolor=stanga_color,
        line=dict(width=0),
        showlegend=False,
        hoverinfo='none'
    ))
    
    # SEMICERCUL DREPT (-90° la 90°)
    theta_right = np.linspace(-np.pi/2, np.pi/2, 150)
    x_right = np.cos(theta_right)
    y_right = np.sin(theta_right)
    x_right_closed = np.append(x_right, 0)
    y_right_closed = np.append(y_right, 0)
    
    fig.add_trace(go.Scatter(
        x=x_right_closed, y=y_right_closed,
        fill='toself',
        fillcolor=dreapta_color,
        line=dict(width=0),
        showlegend=False,
        hoverinfo='none'
    ))
    
    # ELIPSA TERMINATORULUI (doar arcul din mijloc)
    latime_elipsa = abs(2.0 * (iluminare_procent / 100.0) - 1.0)
    if latime_elipsa > 0.001:
        # Generăm puncte de-a lungul elipsei de la -90° la 90° (partea din față)
        theta_el = np.linspace(-np.pi/2, np.pi/2, 150)
        x_el = latime_elipsa * np.cos(theta_el)
        y_el = np.sin(theta_el)
        
        # Închidem forma adăugând punctul (0,0)
        x_el_closed = np.append(x_el, 0)
        y_el_closed = np.append(y_el, 0)
        
        fig.add_trace(go.Scatter(
            x=x_el_closed, y=y_el_closed,
            fill='toself',
            fillcolor=elipsa_color,
            line=dict(width=0),
            showlegend=False,
            hoverinfo='none'
        ))
    
    # CONTURUL CERCULUI
    theta_cerc = np.linspace(0, 2*np.pi, 300)
    x_cerc = np.cos(theta_cerc)
    y_cerc = np.sin(theta_cerc)
    
    fig.add_trace(go.Scatter(
        x=x_cerc, y=y_cerc,
        mode='lines',
        line=dict(color='black', width=1.5),
        showlegend=False,
        hoverinfo='none'
    ))
    
    fig.update_layout(
        width=300, height=300,
        xaxis=dict(range=[-1.15, 1.15], showgrid=False, zeroline=False, visible=False, constrain='domain'),
        yaxis=dict(range=[-1.15, 1.15], showgrid=False, zeroline=False, visible=False, constrain='domain', scaleanchor='x', scaleratio=1),
        template="plotly_white",
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )
    
    return fig

def create_altitude_sinusoid(times, alts, events_dict, is_night, body_name):
    bg_color = "#1a1a2e" if is_night else "white"
    text_color = "white" if is_night else "black"
    line_color = "#f0c040" if body_name == "Soare" else "#c0c0c0"
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(len(times))), y=alts, mode='lines',
                             line=dict(color=line_color, width=1.5), showlegend=False))
    fig.add_hline(y=0, line_dash="dash", line_color="gray" if is_night else "lightgray", opacity=0.6)
    
    if 'now' in events_dict:
        fig.add_trace(go.Scatter(x=[events_dict['now']['idx']], y=[events_dict['now']['alt']],
                                 mode='markers', marker=dict(color='gold', size=10, symbol='circle',
                                 line=dict(color='orange', width=1)), showlegend=False))
    
    for event_key, marker_config in [
        ('sunrise', dict(color='red', symbol='triangle-up', text='R')),
        ('sunset', dict(color='red', symbol='triangle-down', text='A')),
        ('culmination', dict(color='red', symbol='arrow-down', text='C'))
    ]:
        if event_key in events_dict:
            fig.add_trace(go.Scatter(x=[events_dict[event_key]['idx']], y=[events_dict[event_key]['alt']],
                                     mode='markers+text',
                                     marker=dict(color=marker_config['color'], size=8, symbol=marker_config['symbol']),
                                     text=[marker_config['text']], textposition='top center', showlegend=False))
    
    total_points = len(times)
    step = max(1, total_points // 6)
    tick_indices = list(range(0, total_points, step))
    tick_labels = [times[i] for i in tick_indices]
    
    fig.update_layout(
        xaxis=dict(tickmode='array', tickvals=tick_indices, ticktext=tick_labels, showgrid=False, tickfont=dict(color=text_color)),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=200, margin=dict(l=0, r=0, t=0, b=20),
        template="plotly_white", paper_bgcolor=bg_color, plot_bgcolor=bg_color
    )
    return fig

# ═══════════════════════════════════════════════════════════════
# INTERFAȚA
# ═══════════════════════════════════════════════════════════════

st.set_page_config(page_title="Dashboard Astro", layout="wide")

st.markdown("""
<style>
    .stApp, .stMarkdown, .stCaption, .stText, p, div, span, label, 
    .streamlit-expanderHeader p, .streamlit-expanderContent p {
        font-size: 18px !important;
        color: #000000 !important;
        font-weight: 600 !important;
    }
    h2, h3, .stSubheader {
        font-size: 18px !important;
        color: #000000 !important;
        font-weight: bold;
    }
    .main > div {
        overflow-y: auto !important;
        height: 100vh !important;
    }
</style>
""", unsafe_allow_html=True)

now = datetime.now(TZ)
now_utc = now.astimezone(pytz.UTC)

resources = load_resources()
ts = resources['ts']
eph = resources['eph']
observer = resources['observer']
sun = resources['sun']
moon = resources['moon']
earth = resources['earth']
t_now = ts.from_datetime(now_utc)

jd = swe.julday(now_utc.year, now_utc.month, now_utc.day,
                now_utc.hour + now_utc.minute/60.0 + now_utc.second/3600.0)

positions = get_positions_data(jd)
observational = get_observational_data(now_utc)
long_term = get_long_term_events(now_utc)

day_of_year = now.timetuple().tm_yday
week_number = now.isocalendar()[1]
day_name_ro = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri', 'Sâmbătă', 'Duminică'][now.weekday()]
day_rulers = {0: 'Luna', 1: 'Marte', 2: 'Mercury', 3: 'Jupiter', 4: 'Venus', 5: 'Saturn', 6: 'Soare'}
day_ruler = day_rulers[now.weekday()]
current_hour_data = observational.get('current_hour')
hour_ruler = current_hour_data[1] if current_hour_data else ""

st.subheader("Astro")
st.markdown(f"""
**{day_name_ro}, {now.strftime('%d %B %Y, %H:%M:%S %Z')}**  
(UTC: {now_utc.strftime('%d-%m-%Y %H:%M:%S')}) · JD: {jd:.4f}  
**București, Romania** ({LAT}° N, {LON}° E)  
Ziua **{day_of_year}** din an · Săptămâna **{week_number}**  
Guvernator zi: **{day_ruler}** · Guvernator oră: **{hour_ruler}**
""")
st.divider()

tab0, tab1, tab2, tab3, tab4 = st.tabs(["Sumar", "Soare", "Lună", "Planete", "Aspecte"])

# ═══════════ TAB 0: SUMAR ═══════════
with tab0:
    st.subheader("Sumar evenimente (1-3 zile)")
    
    # Scor elemente
    elements_count = {'Foc': 0, 'Pamant': 0, 'Aer': 0, 'Apa': 0}
    fire = ['Ari', 'Leo', 'Sag']
    earth_signs = ['Tau', 'Vir', 'Cap']
    air = ['Gem', 'Lib', 'Aqu']
    water = ['Can', 'Sco', 'Pis']
    
    for name in ['Soare', 'Luna', 'Mercur', 'Venus', 'Marte', 'Jupiter', 'Saturn', 'Uranus', 'Neptun', 'Pluto']:
        if name in positions.get('planet_data', {}):
            lon = positions['planet_data'][name]['lon']
            sign = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis'][int(lon // 30)]
            if sign in fire: elements_count['Foc'] += 1
            elif sign in earth_signs: elements_count['Pamant'] += 1
            elif sign in air: elements_count['Aer'] += 1
            elif sign in water: elements_count['Apa'] += 1
    
    parts = [f"{v} {k}" for k, v in elements_count.items() if v > 0]
    st.caption("**Elemente**: " + ", ".join(parts))
    
    summary = get_summary_events(now, positions, observational, long_term)
    
    if summary['soare']:
        st.caption("**☀️ Soare**")
        for e in summary['soare']:
            st.caption(e)
    
    if summary['luna']:
        st.caption("**Evenimentele Lunii**")
        for e in summary['luna']:
            st.caption(e)
    
    if summary['retrograde']:
        st.caption("**Planete Retrograde**")
        for e in summary['retrograde']:
            st.caption(e)
    
    if summary['ingress']:
        st.caption("**Ingressuri**")
        for e in summary['ingress']:
            st.caption(e)
    
        # NAKSHATRA
    sun_lon_sid = (positions['sun_lon'] - positions['ayanamsa']) % 360
    moon_lon_sid = (positions['moon_lon'] - positions['ayanamsa']) % 360
    
    sun_nak, sun_nak_name, sun_pada = get_nakshatra(sun_lon_sid)
    moon_nak, moon_nak_name, moon_pada = get_nakshatra(moon_lon_sid)
    
    if sun_nak_name and moon_nak_name:
        st.caption("**Nakshatra**")
        
        # Soarele
        sun_current_end = NAKSHATRA_LIST[sun_nak - 1][3]
        sun_dist = (sun_current_end - sun_lon_sid) % 360
        sun_speed = positions['sun_speed']
        if sun_speed > 0:
            sun_days = sun_dist / sun_speed
            sun_exit = now + timedelta(days=sun_days)
            sun_next = sun_nak + 1 if sun_nak < 27 else 1
            st.caption(f"**Soare**: {sun_nak_name} (Pada {sun_pada}) — {format_zodiac(sun_lon_sid)} (sid)")
            st.caption(f"→ {NAKSHATRA_LIST[sun_next-1][1]} ({sun_exit.strftime('%d %b %H:%M')})")
        
        # Luna
        moon_current_end = NAKSHATRA_LIST[moon_nak - 1][3]
        moon_dist = (moon_current_end - moon_lon_sid) % 360
        moon_speed = positions['moon_speed']
        if moon_speed > 0:
            moon_days = moon_dist / moon_speed
            moon_exit = now + timedelta(days=moon_days)
            moon_next = moon_nak + 1 if moon_nak < 27 else 1
            st.caption(f"**Luna**: {moon_nak_name} (Pada {moon_pada}) — {format_zodiac(moon_lon_sid)} (sid)")
            st.caption(f"→ {NAKSHATRA_LIST[moon_next-1][1]} ({moon_exit.strftime('%d %b %H:%M')})")
    
    if summary['aspecte']:
        st.caption("**Aspecte majore (<2°)**")
        for e in summary['aspecte']:
            st.caption(e)
    
    if not any(summary.values()):
        st.caption("Niciun eveniment major în următoarele 3 zile.")



# ═══════════ TAB 1: SOARE ═══════════
with tab1:
    st.subheader("Soare")
    sun_lon = positions['sun_lon']
    sun_alt = observational.get('sun_alt', 0)
    sun_az = observational.get('sun_az', 0)
    sunrise_today = observational.get('sunrise_today')
    sunset_today = observational.get('sunset_today')
    culm_sup = observational.get('culm_sup')
    culm_inf = observational.get('culm_inf')
    alt_culm_sup = observational.get('alt_culm_sup')
    alt_culm_inf = observational.get('alt_culm_inf')
    
    st.caption(f"Poziție: {format_zodiac(sun_lon)}")
    st.caption(f"Răsărit: {sunrise_today.strftime('%H:%M:%S') if sunrise_today is not None else '-'}")
    st.caption(f"Culminație superioară: {culm_sup.strftime('%H:%M:%S')} ({alt_culm_sup:.1f}°)" if culm_sup is not None and alt_culm_sup is not None else "Culminație superioară: -")
    st.caption(f"Apus: {sunset_today.strftime('%H:%M:%S') if sunset_today is not None else '-'}")
    st.caption(f"Culminație inferioară: {culm_inf.strftime('%H:%M:%S')} ({alt_culm_inf:.1f}°)" if culm_inf is not None and alt_culm_inf is not None else "Culminație inferioară: -")
    st.caption(f"Altitudine (acum): {sun_alt:.2f}°")
    st.caption(f"Azimut (acum): {sun_az:.2f}°")
    
    with st.expander("Amurguri"):
        for name, time_str in observational.get('twilights', []):
            st.caption(f"{name}: {time_str}")
    
    with st.expander("Date orbitale și coordonate"):
        st.caption(f"Longitudine ecliptică: {format_dms(sun_lon)}")
        st.caption(f"Latitudine ecliptică: {format_dms(positions['sun_lat'], True)}")
        st.caption(f"Distanță (AU): {positions['sun_dist']:.6f}")
        st.caption(f"Viteză longitudinală: {positions['sun_speed']:.6f} °/zi")
        st.caption(f"Ascensie dreaptă: {format_dms(positions['sun_equ'][0])}")
        st.caption(f"Declinație: {format_dms(positions['sun_equ'][1], True)}")
        st.caption(f"Coord. X (AU): {positions['sun_xyz'][0]:.6f}")
        st.caption(f"Coord. Y (AU): {positions['sun_xyz'][1]:.6f}")
        st.caption(f"Coord. Z (AU): {positions['sun_xyz'][2]:.6f}")
        sunrise_az = observational.get('sunrise_az')
        sunset_az = observational.get('sunset_az')
        st.caption(f"Azimut răsărit: {sunrise_az:.2f}°" if sunrise_az is not None else "Azimut răsărit: -")
        st.caption(f"Azimut apus: {sunset_az:.2f}°" if sunset_az is not None else "Azimut apus: -")
    
    with st.expander("Durata zilei și ore planetare"):
        if sunrise_today is not None and sunset_today is not None:
            day_dur = (sunset_today - sunrise_today).total_seconds()
            sunrise_next = observational.get('sunrise_next')
            night_dur = (sunrise_next - sunset_today).total_seconds() if sunrise_next is not None else (86400 - day_dur)
            st.caption(f"Durata zilei: {int(day_dur//3600)}h {int(day_dur//60)%60:02d}m {int(day_dur%60):02d}s")
            st.caption(f"Durata nopții: {int(night_dur//3600)}h {int(night_dur//60)%60:02d}m {int(night_dur%60):02d}s")
            st.caption(f"Proporție: {day_dur/864:.1f}% zi / {night_dur/864:.1f}% noapte")
            day_h = observational.get('day_h', 0)
            night_h = observational.get('night_h', 0)
            st.caption(f"Oră planetară (zi): {int(day_h//60)}m {int(day_h%60):02.0f}s")
            st.caption(f"Oră planetară (noapte): {int(night_h//60)}m {int(night_h%60):02.0f}s")
            current_hour_data = observational.get('current_hour')
            if current_hour_data:
                num, planet, start, end, tip = current_hour_data
                st.caption(f"Ora planetară curentă: {planet} (ora {num}, {tip}) {start.strftime('%H:%M')} – {end.strftime('%H:%M')}")
            with st.expander("Toate cele 24 de ore planetare"):
                for num, planet, start, end, tip in observational.get('hours_plan', []):
                    line = f"Ora {num:02d} ({tip}): {planet} {start.strftime('%H:%M')} – {end.strftime('%H:%M')}"
                    if current_hour_data and num == current_hour_data[0] and tip == current_hour_data[4]:
                        st.caption(f"**{line}**")
                    else:
                        st.caption(line)
    
    with st.expander("Anotimpuri"):
        st.caption(f"Anotimp curent: {positions.get('current_season', '-')}")
        with st.expander("Echinocții și Solstiții"):
            for name, date_str in long_term.get('next_seasons', []):
                st.caption(f"{name}: {date_str}")
    
    with st.expander("Periheliu și Afeliu"):
        perihelion_t = long_term.get('perihelion_t')
        aphelion_t = long_term.get('aphelion_t')
        if perihelion_t is not None and aphelion_t is not None:
            perihelion_d = long_term['perihelion_d']
            aphelion_d = long_term['aphelion_d']
            current_dist = resources['earth'].at(t_now).observe(resources['sun']).distance().km
            if aphelion_d != perihelion_d:
                progress = (current_dist - perihelion_d) / (aphelion_d - perihelion_d)
            else:
                progress = 0.5
            st.caption(f"Periheliu: {perihelion_d:,.0f} km ({perihelion_t.astimezone(TZ).strftime('%d %b %Y %H:%M')})")
            st.progress(float(max(0, min(1, progress))))
            st.caption(f"Afeliu: {aphelion_d:,.0f} km ({aphelion_t.astimezone(TZ).strftime('%d %b %Y %H:%M')})")
            st.caption(f"Acum: {current_dist:,.0f} km")
        else:
            st.caption("Datele despre periheliu/afeliu nu sunt disponibile momentan.")
    
    with st.expander("Sinusoida altitudinii Soarelui (24h)"):
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        times_sin = []
        alts_sin = []
        for minutes in range(0, 24*60, 5):
            dt = midnight + timedelta(minutes=minutes)
            t = ts.from_datetime(dt.astimezone(pytz.UTC))
            alt, _, _ = observer.at(t).observe(sun).apparent().altaz()
            times_sin.append(dt.strftime('%H:%M'))
            alts_sin.append(alt.degrees)
        
        events = {}
        alt_now = observational.get('sun_alt', 0)
        idx_now = round((now.hour * 60 + now.minute) / 5)
        events['now'] = {'idx': idx_now, 'alt': alt_now}
        if sunrise_today is not None:
            idx_sr = round((sunrise_today.hour * 60 + sunrise_today.minute) / 5)
            events['sunrise'] = {'idx': idx_sr, 'alt': 0}
        if sunset_today is not None:
            idx_ss = round((sunset_today.hour * 60 + sunset_today.minute) / 5)
            events['sunset'] = {'idx': idx_ss, 'alt': 0}
        if culm_sup is not None and alt_culm_sup is not None:
            idx_culm = round((culm_sup.hour * 60 + culm_sup.minute) / 5)
            events['culmination'] = {'idx': idx_culm, 'alt': alt_culm_sup}
        
        fig = create_altitude_sinusoid(times_sin, alts_sin, events, sun_alt < 0, "Soare")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with st.expander("Proporția zi/noapte"):
        if sunrise_today is not None and sunset_today is not None:
            day_sec = (sunset_today - sunrise_today).total_seconds()
            night_sec = 86400 - day_sec
            day_hours = day_sec / 3600
            
            day_angle = (day_sec / 86400) * 360
            # Amiaza (mijlocul zilei) la 0° = ora 12 (sus)
            rotation = (360 - day_angle / 2) % 360
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=['Zi', 'Noapte'],
                values=[day_sec, night_sec],
                marker=dict(colors=['#f0c040', '#1a1a2e']),
                hole=0.1,
                textinfo='label+percent',
                textfont=dict(size=14, color=['black', 'white']),
                rotation=rotation,
                direction='clockwise',
                sort=False
            )])
            
            midday = sunrise_today + timedelta(seconds=day_sec / 2)
            
            fig_pie.update_layout(
                title=f"Zi: {int(day_hours)}h {int((day_hours%1)*60):02d}m | Noapte: {int(24-day_hours)}h {int(((24-day_hours)%1)*60):02d}m",
                height=450, margin=dict(l=20, r=20, t=60, b=20), template="plotly_white"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            st.caption(f"Răsărit: {sunrise_today.strftime('%H:%M:%S')} | Apus: {sunset_today.strftime('%H:%M:%S')} | Amiaza: {midday.strftime('%H:%M:%S')}")

# ═══════════ TAB 2: LUNĂ ═══════════
with tab2:
    st.subheader("Lună")
    
    moon_lon = positions['moon_lon']
    moon_alt = observational.get('moon_alt', 0)
    moon_az = observational.get('moon_az', 0)
    moon_illum = observational.get('moon_illum', 0)
    moon_age = observational.get('moon_age', 0)
    moon_phase_name = observational.get('moon_phase_name', '')
    arc_sl = observational.get('arc_sl', 0)
    
    moonrise_next = observational.get('moonrise_next')
    moonset_next = observational.get('moonset_next')
    moon_culm_sup = observational.get('moon_culm_sup')
    moon_alt_culm_sup = observational.get('moon_alt_culm_sup')
    moon_culm_inf = observational.get('moon_culm_inf')
    moon_alt_culm_inf = observational.get('moon_alt_culm_inf')
    
    st.caption(f"Poziție: {format_zodiac(moon_lon)}")
    st.caption(f"Răsărit: {moonrise_next.strftime('%d %b %H:%M') if moonrise_next is not None else '-'}")
    st.caption(f"Culminație superioară: {moon_culm_sup.strftime('%d %b %H:%M')} ({moon_alt_culm_sup:.1f}°)" if moon_culm_sup is not None and moon_alt_culm_sup is not None else "Culminație superioară: -")
    st.caption(f"Apus: {moonset_next.strftime('%d %b %H:%M') if moonset_next is not None else '-'}")
    st.caption(f"Culminație inferioară: {moon_culm_inf.strftime('%d %b %H:%M')} ({moon_alt_culm_inf:.1f}°)" if moon_culm_inf is not None and moon_alt_culm_inf is not None else "Culminație inferioară: -")
    st.caption(f"Altitudine (acum): {moon_alt:.2f}°")
    st.caption(f"Azimut (acum): {moon_az:.2f}°")
    st.caption(f"Arc solar-lunar: {format_dms(arc_sl)}")
    st.caption(f"Iluminare: {moon_illum*100:.2f}%")
    st.caption(f"Vârsta Lunii: {moon_age:.2f} zile")
    st.caption(f"Fază: {moon_phase_name}")
    
    mansion_info = long_term.get('next_mansion')
    if mansion_info is not None:
        st.caption(f"Conac Arabesc: {mansion_info['current']}")
        st.caption(f"→ {mansion_info['next']} ({mansion_info['next_date']})")
    elif positions.get('mansion_num') is not None:
        num = positions['mansion_num']
        name = positions['mansion_name']
        trans = positions['mansion_trans']
        display = f"{name} — {trans}" if trans != "TBD" else name
        st.caption(f"Conac Arabesc: {num}. {display}")
    
    with st.expander("Conacele Arabești"):
        for num, name, trans, start, end in MANSIONS_LIST:
            display = f"{name} — {trans}" if trans != "TBD" else name
            if positions.get('mansion_num') == num:
                st.caption(f"**{num}. {display}** ({format_dms(start)} – {format_dms(end)})")
            else:
                st.caption(f"{num}. {display} ({format_dms(start)} – {format_dms(end)})")
    with st.expander("Nakshatra (27 de constelații siderale)"):
        sun_lon_sid = (positions['sun_lon'] - positions['ayanamsa']) % 360
        moon_lon_sid = (positions['moon_lon'] - positions['ayanamsa']) % 360
        
        sun_nak, sun_nak_name, sun_pada = get_nakshatra(sun_lon_sid)
        moon_nak, moon_nak_name, moon_pada = get_nakshatra(moon_lon_sid)
        
        st.caption(f"Soarele în **{sun_nak_name}** (Pada {sun_pada}) — {format_zodiac(sun_lon_sid)} (sid)")
        st.caption(f"Luna în **{moon_nak_name}** (Pada {moon_pada}) — {format_zodiac(moon_lon_sid)} (sid)")
        st.caption("")
        st.caption("Toate cele 27 de Nakshatra:")
        
        for num, name, start, end in NAKSHATRA_LIST:
            pada_size = 3.3333
            if (moon_nak == num):
                st.caption(f"**{num}. {name}** ({format_dms(start)} – {format_dms(end)}) ⬅ Luna aici")
            elif (sun_nak == num):
                st.caption(f"**{num}. {name}** ({format_dms(start)} – {format_dms(end)}) ⬅ Soarele aici")
            else:
                st.caption(f"{num}. {name} ({format_dms(start)} – {format_dms(end)})")
    
    with st.expander("Date orbitale și coordonate"):
        st.caption(f"Longitudine ecliptică: {format_dms(moon_lon)}")
        st.caption(f"Latitudine ecliptică: {format_dms(positions['moon_lat'], True)}")
        st.caption(f"Distanță (AU): {positions['moon_dist']:.6f}")
        st.caption(f"Distanță (km): {positions['moon_dist'] * AU_TO_KM:,.0f}")
        st.caption(f"Viteză longitudinală: {positions['moon_speed']:.6f} °/zi")
        st.caption(f"Ascensie dreaptă: {format_dms(positions['moon_equ'][0])}")
        st.caption(f"Declinație: {format_dms(positions['moon_equ'][1], True)}")
        st.caption(f"Coord. X (AU): {positions['moon_xyz'][0]:.6f}")
        st.caption(f"Coord. Y (AU): {positions['moon_xyz'][1]:.6f}")
        st.caption(f"Coord. Z (AU): {positions['moon_xyz'][2]:.6f}")
    
    with st.expander("Evenimente Lunare (următoarele 8)"):
        all_events = long_term.get('all_lunar_events', [])
        future_events = [(t.astimezone(TZ), label, etype) for t, label, etype in all_events if t.astimezone(TZ) >= now][:8]
        if future_events:
            for dt_event, label, event_type in future_events:
                st.caption(f"{label}: {dt_event.strftime('%d %b %Y %H:%M')}")
        else:
            st.caption("Nu s-au găsit evenimente")
    
    with st.expander("Progres Lună (faze, noduri, distanță)"):
        # Bară faze
        moon_phases_all = long_term.get('moon_phases_all', [])
        if len(moon_phases_all) >= 2:
            sorted_phases = []
            for label, date_str in moon_phases_all:
                try:
                    dt = TZ.localize(datetime.strptime(date_str, '%d %b %Y %H:%M'))
                    sorted_phases.append((label, dt, date_str))
                except:
                    continue
            sorted_phases.sort(key=lambda x: x[1])
            prev_phase = None
            next_phase = None
            for i, (label, dt, date_str) in enumerate(sorted_phases):
                if dt <= now:
                    prev_phase = (label, dt, date_str)
                elif dt > now and next_phase is None:
                    next_phase = (label, dt, date_str)
                    break
            if prev_phase is not None and next_phase is not None:
                total_sec = (next_phase[1] - prev_phase[1]).total_seconds()
                elapsed_sec = (now - prev_phase[1]).total_seconds()
                progress = max(0, min(1, elapsed_sec / total_sec if total_sec > 0 else 0))
                remaining = total_sec - elapsed_sec
                st.progress(float(progress))
                st.caption(f"{prev_phase[0]} → {next_phase[0]} ({int(remaining//86400)}z {int((remaining%86400)//3600)}h {int((remaining%3600)//60)}m)")
        
        # Bară noduri
        moon_nodes_all_time = long_term.get('moon_nodes_all_time', [])
        if len(moon_nodes_all_time) >= 2:
            prev_node = None
            next_node = None
            for label, t_node in moon_nodes_all_time:
                dt_node = t_node.astimezone(TZ)
                if dt_node <= now:
                    prev_node = (label, dt_node)
                elif dt_node > now and next_node is None:
                    next_node = (label, dt_node)
                    break
            if prev_node is not None and next_node is not None:
                total_sec_n = (next_node[1] - prev_node[1]).total_seconds()
                elapsed_sec_n = (now - prev_node[1]).total_seconds()
                progress_node = max(0, min(1, elapsed_sec_n / total_sec_n if total_sec_n > 0 else 0))
                remaining_n = total_sec_n - elapsed_sec_n
                st.caption("")
                st.progress(float(progress_node))
                st.caption(f"{prev_node[0]} → {next_node[0]} ({int(remaining_n//86400)}z {int((remaining_n%86400)//3600)}h {int((remaining_n%3600)//60)}m)")
        
        # Bară perigeu/apogeu (acum cu km!)
        prev_event = long_term.get('prev_ap_event')
        next_event = long_term.get('next_ap_event')
        if prev_event is not None and next_event is not None:
            label_prev, t_prev, dist_prev = prev_event
            label_next, t_next, dist_next = next_event
            dt_prev = t_prev.astimezone(TZ)
            dt_next = t_next.astimezone(TZ)
            total_sec = (dt_next - dt_prev).total_seconds()
            elapsed_sec = (now - dt_prev).total_seconds()
            progress = max(0, min(1, elapsed_sec / total_sec if total_sec > 0 else 0))
            remaining = total_sec - elapsed_sec
            st.caption("")
            st.progress(float(progress))
            # Etichetă cu km
            label_prev_full = f"{label_prev} ({dist_prev:,.0f} km)"
            label_next_full = f"{label_next} ({dist_next:,.0f} km)"
            st.caption(f"{label_prev_full} → {label_next_full} ({int(remaining//86400)}z {int((remaining%86400)//3600)}h {int((remaining%3600)//60)}m)")
    
    with st.expander("Sinusoida altitudinii Lunii"):
        all_times_list = [now]
        if moonrise_next is not None:
            all_times_list.append(moonrise_next)
        if moonset_next is not None:
            all_times_list.append(moonset_next)
        if moon_culm_sup is not None:
            all_times_list.append(moon_culm_sup)
        start_time = min(all_times_list) - timedelta(hours=2)
        end_time = max(all_times_list) + timedelta(hours=2)
        times_sin_moon = []
        alts_sin_moon = []
        time_labels = []
        current = start_time
        while current <= end_time:
            t = ts.from_datetime(current.astimezone(pytz.UTC))
            alt, _, _ = observer.at(t).observe(moon).apparent().altaz()
            times_sin_moon.append(current)
            time_labels.append(current.strftime('%H:%M'))
            alts_sin_moon.append(alt.degrees)
            current += timedelta(minutes=5)
        
        events = {}
        idx_now = min(range(len(times_sin_moon)), key=lambda i: abs((times_sin_moon[i] - now).total_seconds()))
        events['now'] = {'idx': idx_now, 'alt': moon_alt}
        if moonrise_next is not None:
            idx_mr = min(range(len(times_sin_moon)), key=lambda i: abs((times_sin_moon[i] - moonrise_next).total_seconds()))
            events['sunrise'] = {'idx': idx_mr, 'alt': 0}
        if moonset_next is not None:
            idx_ms = min(range(len(times_sin_moon)), key=lambda i: abs((times_sin_moon[i] - moonset_next).total_seconds()))
            events['sunset'] = {'idx': idx_ms, 'alt': 0}
        if moon_culm_sup is not None and moon_alt_culm_sup is not None:
            idx_mc = min(range(len(times_sin_moon)), key=lambda i: abs((times_sin_moon[i] - moon_culm_sup).total_seconds()))
            events['culmination'] = {'idx': idx_mc, 'alt': moon_alt_culm_sup}
        
        fig_moon = create_altitude_sinusoid(time_labels, alts_sin_moon, events, moon_alt < 0, "Luna")
        st.plotly_chart(fig_moon, use_container_width=True, config={'displayModeBar': False})
    
    with st.expander("Faza Lunii (vizual)"):
        col1, col2 = st.columns([1, 2])
        with col1:
            is_waning = arc_sl > 180
            fig_luna = create_moon_phase_plotly(moon_illum, is_waning)
            st.plotly_chart(fig_luna, use_container_width=True, config={'displayModeBar': False})
            st.caption(f"Iluminare: {moon_illum*100:.1f}% | {moon_phase_name}")
        with col2:
            st.caption(f"Vârsta Lunii: {moon_age:.2f} zile")
            st.caption(f"Arc solar-lunar: {format_dms(arc_sl)}")
            st.caption("Iluminare:")
            st.progress(float(moon_illum))
            st.caption(f"{moon_illum*100:.1f}%")
            st.caption("")
            st.caption("Fazele următoare:")
            for label, date_str in long_term.get('moon_phases', [])[:4]:
                st.caption(f"{label}: {date_str}")
    
    with st.expander("Cercuri concentrice (faze, noduri, perigeu/apogeu)"):
        total_synodic_days = 29.53
        all_events_list = long_term.get('all_lunar_events', [])
        
        selected_events = []
        seen_types = set()
        for t_event, label, event_type in all_events_list:
            dt_event = t_event.astimezone(TZ)
            if dt_event >= now:
                if event_type == 'phase':
                    if "Lună Nouă" in label and 'new_moon' not in seen_types:
                        selected_events.append((dt_event, label, event_type))
                        seen_types.add('new_moon')
                    elif "Primul Pătrar" in label and 'first_quarter' not in seen_types:
                        selected_events.append((dt_event, label, event_type))
                        seen_types.add('first_quarter')
                    elif "Lună Plină" in label and 'full_moon' not in seen_types:
                        selected_events.append((dt_event, label, event_type))
                        seen_types.add('full_moon')
                    elif "Ultimul Pătrar" in label and 'last_quarter' not in seen_types:
                        selected_events.append((dt_event, label, event_type))
                        seen_types.add('last_quarter')
                elif event_type == 'node':
                    if "Ascendent" in label and 'asc_node' not in seen_types:
                        selected_events.append((dt_event, label, event_type))
                        seen_types.add('asc_node')
                    elif "Descendent" in label and 'desc_node' not in seen_types:
                        selected_events.append((dt_event, label, event_type))
                        seen_types.add('desc_node')
                elif event_type == 'perigee' and 'perigee' not in seen_types:
                    selected_events.append((dt_event, label, event_type))
                    seen_types.add('perigee')
                elif event_type == 'apogee' and 'apogee' not in seen_types:
                    selected_events.append((dt_event, label, event_type))
                    seen_types.add('apogee')
                if len(selected_events) == 8:
                    break
        
        if len(selected_events) >= 2:
            selected_events.sort(key=lambda x: x[0])
            last_date = selected_events[-1][0]
            total_days = (last_date - now).total_seconds() / 86400 + 2
            
            full_moon_date = None
            for dt, label, et in selected_events:
                if et == 'phase' and "Lună Plină" in label:
                    full_moon_date = dt
                    break
            
            if full_moon_date is not None:
                events_with_angles = []
                for dt, label, et in selected_events:
                    days_diff = (dt - full_moon_date).total_seconds() / 86400
                    angle = (days_diff / total_synodic_days) * 360
                    if angle < 0:
                        angle = 360 + angle
                    events_with_angles.append((angle, dt, label, et))
                
                days_diff_now = (now - full_moon_date).total_seconds() / 86400
                now_angle = (days_diff_now / total_synodic_days) * 360
                if now_angle < 0:
                    now_angle = 360 + now_angle
                
                r1, r2, r3 = 0.30, 0.55, 0.80
                
                fig = go.Figure()
                
                theta = np.linspace(0, 360, 100)
                for r, color in [(r1, '#cccccc'), (r2, '#cccccc'), (r3, '#cccccc')]:
                    fig.add_trace(go.Scatterpolar(
                        r=[r] * len(theta), theta=theta,
                        mode='lines', line=dict(color=color, width=1),
                        showlegend=False, hoverinfo='none'
                    ))
                
                    for angle, dt, label, et in events_with_angles:
                        if et == 'phase':
                            r = r1
                            if "🌑" in label: icon = "🌑"
                            elif "🌓" in label: icon = "🌓"
                            elif "🌕" in label: icon = "🌕"
                            elif "🌗" in label: icon = "🌗"
                            else: icon = "●"
                            color_icon = '#333333'
                            icon_size = 20
                            r_icon = r1 + 0.08
                        elif et == 'node':
                            r = r2
                            if "Ascendent" in label: icon = "☊"
                            else: icon = "☋"
                            color_icon = '#4299e1'
                            icon_size = 22
                            r_icon = r2 + 0.08
                        else:
                            r = r3
                            if "Perigeu" in label: icon = "⬇"
                            else: icon = "⬆"
                            color_icon = '#9b59b6'
                            icon_size = 18
                            r_icon = r3 + 0.08
                        
                        # Liniuța pe cerc (marker pe poziția exactă)
                        fig.add_trace(go.Scatterpolar(
                            r=[r - 0.02, r + 0.02], theta=[angle, angle],
                            mode='lines', line=dict(color=color_icon, width=2),
                            showlegend=False, hoverinfo='text',
                            hovertext=f"{label}<br>{dt.strftime('%d %b %H:%M')}"
                        ))
                        
                        # Iconița lângă liniuță (în exterior)
                        fig.add_trace(go.Scatterpolar(
                            r=[r_icon], theta=[angle],
                            mode='text', text=[icon],
                            textfont=dict(size=icon_size, color=color_icon, family='Arial'),
                            showlegend=False, hoverinfo='text',
                            hovertext=f"{label}<br>{dt.strftime('%d %b %H:%M')}"
                        ))
                
                fig.add_trace(go.Scatterpolar(
                    r=[0, r1 - 0.02], theta=[now_angle, now_angle],
                    mode='lines', line=dict(color='#e53e3e', width=3),
                    showlegend=False, hoverinfo='none'
                ))
                
                fig.add_trace(go.Scatterpolar(
                    r=[0], theta=[0],
                    mode='markers', marker=dict(size=10, color='#e53e3e', symbol='circle'),
                    showlegend=False, hoverinfo='text', hovertext='Acum'
                ))
                
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=False, range=[0, 1]),
                        angularaxis=dict(
                            tickmode='array',
                            tickvals=[0, 90, 180, 270],
                            ticktext=['Lună Plină', '7 z', '14 z', '21 z'],
                            direction='clockwise',
                            rotation=90
                        )
                    ),
                    height=550, margin=dict(l=20, r=20, t=20, b=20),
                    template="plotly_white", showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("""
                <div style="display: flex; gap: 20px; justify-content: center; margin-top: 10px; font-size: 18px;">
                    <span>🌑🌓🌕🌗 Faze Lunii</span>
                    <span style="color: #4299e1;">☊☋ Noduri</span>
                    <span style="color: #9b59b6;">P A Perigeu/Apogeu</span>
                    <span style="color: #e53e3e;">⬤ Acum</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.caption("Nu s-a găsit Luna Plină ca referință.")
        else:
            st.caption("Nu sunt suficiente evenimente pentru afișare.")

    with st.expander("Unghi Soare-Lună (🍕 felie de pizza)"):
        sun_lon = positions['sun_lon']
        moon_lon = positions['moon_lon']
        arc_sl = observational.get('arc_sl', 0)
        
        nn_lon = positions['planet_data']['Nod Nord (Mean)']['lon']
        ns_lon = positions['planet_data']['Nod Sud (Mean)']['lon']
        lilith_lon = positions['planet_data']['Lilith (Mean)']['lon']
        priap_lon = (lilith_lon + 180) % 360
        
        fig_pizza = go.Figure()
        
        # INELUL ZODIACAL
        r_inner = 0.65
        r_outer = 0.80
        
        theta_cerc = np.linspace(0, 360, 360)
        fig_pizza.add_trace(go.Scatterpolar(
            r=[r_inner] * len(theta_cerc), theta=theta_cerc,
            mode='lines', line=dict(color='#cccccc', width=1.5),
            showlegend=False, hoverinfo='none'
        ))
        fig_pizza.add_trace(go.Scatterpolar(
            r=[r_outer] * len(theta_cerc), theta=theta_cerc,
            mode='lines', line=dict(color='#cccccc', width=1.5),
            showlegend=False, hoverinfo='none'
        ))
        
        # Segmente zodiacale
        for i in range(12):
            angle = i * 30
            fig_pizza.add_trace(go.Scatterpolar(
                r=[r_inner, r_outer], theta=[angle, angle],
                mode='lines', line=dict(color='#dddddd', width=1),
                showlegend=False, hoverinfo='none'
            ))
        
        # Abrevieri zodii în engleză
        signs_abbr = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis']
        for i, sign in enumerate(signs_abbr):
            angle = i * 30 + 15
            fig_pizza.add_trace(go.Scatterpolar(
                r=[(r_inner + r_outer) / 2], theta=[angle],
                mode='text', text=[sign],
                textfont=dict(size=14, color='#666666'),
                showlegend=False, hoverinfo='none'
            ))
        
        # PUNCTELE ȘI LINIILE CĂTRE CENTRU
        r_points = r_inner - 0.12
        
        def add_body(fig, lon, symbol, color, size, name, r_points, text_color='white'):
            # Linia punctată către centru
            fig.add_trace(go.Scatterpolar(
                r=[0, r_points], theta=[lon, lon],
                mode='lines', line=dict(color=color, width=1, dash='dot'),
                showlegend=False, hoverinfo='none'
            ))
            # Punctul (fără background, doar text)
            fig.add_trace(go.Scatterpolar(
                r=[r_points], theta=[lon],
                mode='text',
                text=[symbol],
                textfont=dict(size=size, color=color),
                showlegend=False, hoverinfo='text',
                hovertext=f"{name}: {format_zodiac(lon)}"
            ))
        
        # Corpuri cerești (mărite, fără background)
        add_body(fig_pizza, sun_lon, '☉', '#f0c040', 36, 'Soare', r_points - 0.01)
        add_body(fig_pizza, moon_lon, '☽', '#f0c040', 28, 'Lună', r_points)
        add_body(fig_pizza, nn_lon, '☊', '#4299e1', 28, 'Nod Nord', r_points)
        add_body(fig_pizza, ns_lon, '☋', '#4299e1', 28, 'Nod Sud', r_points)
        add_body(fig_pizza, lilith_lon, '⚸', '#9b59b6', 28, 'Lilith', r_points)
        add_body(fig_pizza, priap_lon, 'P', '#9b59b6', 28, 'Priap', r_points)
        
        # FELIA DE PIZZA
        if moon_lon > sun_lon:
            theta_arc = np.linspace(sun_lon, moon_lon, 200)
        else:
            theta_arc = np.linspace(sun_lon, moon_lon + 360, 200) % 360
        
        r_arc = r_points
        poly_r = np.concatenate([[0], [r_arc] * len(theta_arc), [0]])
        poly_theta = np.concatenate([[theta_arc[0]], theta_arc, [theta_arc[-1]]])
        
        fig_pizza.add_trace(go.Scatterpolar(
            r=poly_r, theta=poly_theta,
            mode='lines', fill='toself',
            fillcolor='rgba(200, 200, 200, 0.3)',
            line=dict(color='#999999', width=1),
            showlegend=False, hoverinfo='text',
            hovertext=f"Arc solar-lunar: {format_dms(arc_sl)}<br>Iluminare: {observational.get('moon_illum', 0)*100:.1f}%"
        ))
        
        fig_pizza.update_layout(
            polar=dict(
                radialaxis=dict(visible=False, range=[0, 1]),
                angularaxis=dict(
                    tickmode='array',
                    tickvals=[0, 90, 180, 270],
                    ticktext=['0° (Ari)', '90° (Can)', '180° (Lib)', '270° (Cap)'],
                    direction='clockwise',
                    rotation=90
                )
            ),
            height=550, margin=dict(l=20, r=20, t=20, b=20),
            template="plotly_white", showlegend=False
        )
        
        st.plotly_chart(fig_pizza, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption(f"☉ Soare: {format_zodiac(sun_lon)}")
            st.caption(f"☽ Lună: {format_zodiac(moon_lon)}")
        with col2:
            st.caption(f"Arc: {format_dms(arc_sl)}")
            st.caption(f"Iluminare: {observational.get('moon_illum', 0)*100:.1f}%")
        with col3:
            st.caption(f"☊ NN: {format_zodiac(nn_lon)}")
            st.caption(f"☋ NS: {format_zodiac(ns_lon)}")
            st.caption(f"⚸ Lilith: {format_zodiac(lilith_lon)}")
            st.caption(f"P Priap: {format_zodiac(priap_lon)}")

# ═══════════ TAB 3: PLANETE ═══════════
with tab3:
    st.subheader("Planete")
    
    planet_data = positions['planet_data']
    all_bodies = list(PLANET_IDS.keys()) + ['Nod Nord (Mean)', 'Nod Sud (Mean)', 'Lilith (Mean)'] + list(ASTEROID_IDS.keys())
    
    for name in all_bodies:
        if name not in planet_data:
            continue
        pdata = planet_data[name]
        dign = get_dignity(name, pdata['lon'])
        retro_str = " R" if pdata['retro'] else ""
        dign_str = f" [{dign}]" if dign else ""
        st.caption(f"{name}: {format_zodiac(pdata['lon'])}{retro_str}{dign_str} | V: {pdata['speed']:.4f}°/zi")
    
    with st.expander("Date orbitale și coordonate"):
        for name in all_bodies:
            if name not in planet_data:
                continue
            pdata = planet_data[name]
            dec_str = ""
            if name in PLANET_IDS:
                equ_pos = swe.calc_ut(jd, PLANET_IDS[name], swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)[0]
                dec_str = f" | Decl {format_dms(equ_pos[1], True)}"
            st.caption(f"{name}: L {format_dms(pdata['lon'])} | B {format_dms(pdata['lat'], True)} | Dist {pdata['dist']:.6f} AU | V {pdata['speed']:.4f}°/zi{dec_str}")
    
    with st.expander("Altitudine (acum)"):
        altitudes = []
        
        # Soarele și Luna (cu sens)
        sun_alt = observational.get('sun_alt', 0)
        moon_alt = observational.get('moon_alt', 0)
        
        t_later = ts.from_datetime(now_utc + timedelta(minutes=5))
        sun2 = observer.at(t_later).observe(eph['sun']).apparent()
        moon2 = observer.at(t_later).observe(eph['moon']).apparent()
        sun_alt2, _, _ = sun2.altaz()
        moon_alt2, _, _ = moon2.altaz()
        
        altitudes.append(('☉ Soare', sun_alt, '↑' if sun_alt2.degrees > sun_alt else '↓'))
        altitudes.append(('☽ Lună', moon_alt, '↑' if moon_alt2.degrees > moon_alt else '↓'))
        
        # Planetele
        planet_sf_names = {
            'Mercur': 'MERCURY', 'Venus': 'VENUS', 'Marte': 'MARS BARYCENTER',
            'Jupiter': 'JUPITER BARYCENTER', 'Saturn': 'SATURN BARYCENTER',
            'Uranus': 'URANUS BARYCENTER', 'Neptun': 'NEPTUNE BARYCENTER',
            'Pluto': 'PLUTO BARYCENTER',
        }
        
        for name, sf_name in planet_sf_names.items():
            try:
                p = observer.at(t_now).observe(eph[sf_name]).apparent()
                alt, az, _ = p.altaz()
                
                # Verifică sensul mișcării (peste 5 minute)
                t_later = ts.from_datetime(now_utc + timedelta(minutes=5))
                p2 = observer.at(t_later).observe(eph[sf_name]).apparent()
                alt2, _, _ = p2.altaz()
                arrow = "↑" if alt2.degrees > alt.degrees else "↓"
                
                altitudes.append((name, alt.degrees, arrow))
            except:
                pass
        
        # Sortăm descrescător după altitudine
        altitudes.sort(key=lambda x: x[1], reverse=True)
        
        for name, alt, arrow in altitudes:
            if alt > 0:
                st.caption(f"{name}: +{alt:.1f}° {arrow}")
        
        st.caption("─── Orizont (0°) ───")
        
        for name, alt, arrow in altitudes:
            if alt <= 0:
                st.caption(f"{name}: {alt:.1f}° {arrow}")
        
    
    with st.expander("Fazele planetelor interioare"):
        col1, col2 = st.columns(2)
        for inner_name, inner_sname, col in [('Mercur', 'MERCURY', col1), ('Venus', 'VENUS', col2)]:
            with col:
                inner_pos = earth.at(t_now).observe(eph[inner_sname]).apparent()
                sun_pos_now = earth.at(t_now).observe(sun).apparent()
                phase_angle = sun_pos_now.separation_from(inner_pos)
                illum_pct = (1 + math.cos(phase_angle.radians)) / 2 * 100
                st.caption(f"{inner_name}: iluminare {illum_pct:.1f}%")
                st.progress(float(illum_pct / 100))
    
    with st.expander("Unghiuri (Ascendent și MC)"):
        st.caption(f"Ascendent: {format_zodiac(positions['ascendant'])}")
        st.caption(f"MC (Midheaven): {format_zodiac(positions['mc'])}")
    
    with st.expander("Stele Fixe Principale"):
        for star_name in positions.get('fixed_stars_names', []):
            if star_name in planet_data:
                st.caption(f"{star_name}: {format_zodiac(planet_data[star_name]['lon'])}")
    
    with st.expander("Constelații reale (IAU)"):
        from skyfield.api import load as skyfield_load
        resources = skyfield_load('de440s.bsp')
        earth_iau = resources['earth']
        ts_iau = load.timescale()
        t_iau = ts_iau.from_datetime(now_utc)
        
        # Dicționar de nume Skyfield pentru toate corpurile
        skyfield_bodies = {
            'Soare': 'SUN', 'Luna': 'MOON', 'Mercur': 'MERCURY', 'Venus': 'VENUS',
            'Marte': 'MARS BARYCENTER', 'Jupiter': 'JUPITER BARYCENTER',
            'Saturn': 'SATURN BARYCENTER', 'Uranus': 'URANUS BARYCENTER',
            'Neptun': 'NEPTUNE BARYCENTER', 'Pluto': 'PLUTO BARYCENTER',
        }
        
        st.caption("**Planete:**")
        for name, sf_name in skyfield_bodies.items():
            try:
                body = resources[sf_name]
                position = earth_iau.at(t_iau).observe(body).apparent()
                ra, dec, _ = position.radec()
                constellation = get_real_constellation(ra.hours, dec.degrees)
                st.caption(f"{name}: {constellation}")
            except:
                st.caption(f"{name}: n/a")
        
        # Pentru asteroizi, noduri, Lilith - folosim pozițiile ecliptice și convertim
        st.caption("")
        st.caption("**Asteroizi și puncte:**")
        
        obliquity = positions['obliquity']
        
        for name in list(ASTEROID_IDS.keys()) + ['Nod Nord (Mean)', 'Nod Sud (Mean)', 'Lilith (Mean)']:
            if name not in planet_data:
                continue
            lon = planet_data[name]['lon']
            lat = planet_data[name]['lat']
            
            # Conversie ecliptică → ecuatorială (aproximativă, dar suficientă)
            from math import sin, cos, tan, asin, atan2, radians, degrees
            lon_rad = radians(lon)
            lat_rad = radians(lat)
            eps_rad = radians(obliquity)
            
            dec_rad = asin(sin(lat_rad) * cos(eps_rad) + cos(lat_rad) * sin(eps_rad) * sin(lon_rad))
            ra_rad = atan2(sin(lon_rad) * cos(eps_rad) - tan(lat_rad) * sin(eps_rad), cos(lon_rad))
            
            ra_hours = (degrees(ra_rad) % 360) / 15.0
            dec_deg = degrees(dec_rad)
            
            constellation = get_real_constellation(ra_hours, dec_deg)
            st.caption(f"{name}: {constellation}")

# ═══════════ TAB 4: ASPECTE ═══════════
with tab4:
    st.subheader("Aspecte")
    orb = st.slider("Orb (grade)", min_value=1.0, max_value=8.0, value=0.5, step=0.5)
    
    planet_data = positions['planet_data']
    all_bodies_list = (list(PLANET_IDS.keys()) + ['Nod Nord (Mean)', 'Nod Sud (Mean)', 'Lilith (Mean)'] + 
                      list(ASTEROID_IDS.keys()) + positions.get('fixed_stars_names', []))
    
    aspect_types = {
        'Conjuncție': 0,
        'Sextil': 60,
        'Careu': 90,
        'Trigon': 120,
        'Opoziție': 180,
    }
    
    aspects = []
    for i, body1 in enumerate(all_bodies_list):
        if body1 not in planet_data:
            continue
        lon1 = planet_data[body1]['lon']
        speed1 = planet_data[body1]['speed']
        for j, body2 in enumerate(all_bodies_list):
            if j <= i or body2 not in planet_data:
                continue
            if body1 in positions.get('fixed_stars_names', []) and body2 in positions.get('fixed_stars_names', []):
                continue
            if body1 in ['Nod Nord (Mean)', 'Nod Sud (Mean)'] and body2 in ['Nod Nord (Mean)', 'Nod Sud (Mean)']:
                continue
            lon2 = planet_data[body2]['lon']
            speed2 = planet_data[body2]['speed']
            diff = abs(lon2 - lon1)
            if diff > 180:
                diff = 360 - diff
            for aspect_name, aspect_angle in aspect_types.items():
                angle_diff = abs(diff - aspect_angle)
                if angle_diff <= orb:
                    sign = "+" if speed1 > speed2 else "-" if speed2 > speed1 else ""
                    aspects.append((angle_diff, body1, body2, aspect_name, sign))
    
    aspects.sort(key=lambda x: x[0])
    
    if aspects:
        for diff, body1, body2, aspect_name, sign in aspects:
            st.caption(f"{body1} – {body2}: {aspect_name} ({format_dms(diff)}{sign})")
    else:
        st.caption("Niciun aspect cu orbul selectat.")

st.divider()
st.caption(f"Generat la {now.strftime('%Y-%m-%d %H:%M:%S')}")