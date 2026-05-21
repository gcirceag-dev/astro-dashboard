#!/usr/bin/env python3
"""
app_v2.py - Dashboard Astro cu Streamlit (optimizat cu cache)
"""

import os
import math
import swisseph as swe
from skyfield.api import load, wgs84
from skyfield import almanac
from datetime import datetime, timedelta
import pytz
import streamlit as st
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Ellipse

# ═══════════════════════════════════════════════════════════════
# CONFIGURARE
# ═══════════════════════════════════════════════════════════════

EPHE_PATH = os.path.join(os.path.dirname(__file__), 'ephe')
swe.set_ephe_path(EPHE_PATH)

t0_jd = 2435555.5
ayan_t0 = 23.25
swe.set_sid_mode(swe.SIDM_USER, t0_jd, ayan_t0)

LAT = 44.42
LON = 26.12
ELEVATION = 70
TZ = pytz.timezone('Europe/Bucharest')

# Lista completă a conacelor arabești (globală)
mansions_list = [
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

# ═══════════════════════════════════════════════════════════════
# CACHE PENTRU EFEMERIDE
# ═══════════════════════════════════════════════════════════════

@st.cache_resource
def load_ephemeris():
    """Încarcă efemeridele o singură dată"""
    ts = load.timescale()
    eph = load('de440s.bsp')
    return ts, eph

# ═══════════════════════════════════════════════════════════════
# FUNCȚII AJUTĂTOARE
# ═══════════════════════════════════════════════════════════════

def format_dms(decimal_degrees, is_latitude=False):
    sign = ""
    if decimal_degrees < 0:
        sign = "-"
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
    sign_idx = int(longitude // 30)
    pos_in_sign = longitude % 30
    sign = signs[sign_idx % 12]
    return f"{sign} {format_dms(pos_in_sign)}"
    


def refine_extremum(t_approx, is_min, earth, target, ts):
    t_left = ts.tt_jd(t_approx.tt - 1)
    t_right = ts.tt_jd(t_approx.tt + 1)
    for _ in range(30):
        t_mid = ts.tt_jd((t_left.tt + t_right.tt) / 2)
        t_test = ts.tt_jd(t_mid.tt + 0.0001)
        dist_mid = earth.at(t_mid).observe(target).distance().km
        dist_test = earth.at(t_test).observe(target).distance().km
        if is_min:
            if dist_test < dist_mid:
                t_left = t_mid
            else:
                t_right = t_test
        else:
            if dist_test > dist_mid:
                t_left = t_mid
            else:
                t_right = t_test
    t_exact = ts.tt_jd((t_left.tt + t_right.tt) / 2)
    dist_exact = earth.at(t_exact).observe(target).distance().km
    return t_exact, dist_exact

def get_planetary_hours(sunrise, sunset, sunrise_next, now_dt):
    chaldean = ['Saturn', 'Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury', 'Moon']
    day_rulers = {0: 'Moon', 1: 'Mars', 2: 'Mercury', 3: 'Jupiter', 4: 'Venus', 5: 'Saturn', 6: 'Sun'}
    
    durata_zi = (sunset - sunrise)
    durata_noapte = (sunrise_next - sunset)
    lungime_ora_zi = durata_zi / 12
    lungime_ora_noapte = durata_noapte / 12
    
    weekday = sunrise.weekday()
    stapan_pornire = day_rulers[weekday]
    index_curent = chaldean.index(stapan_pornire)
    
    ore_zi = []
    timp_cursor = sunrise
    for i in range(12):
        planeta = chaldean[index_curent]
        start_ora = timp_cursor
        timp_cursor += lungime_ora_zi
        ore_zi.append((i + 1, planeta, start_ora, timp_cursor))
        index_curent = (index_curent + 1) % 7
    
    ore_noapte = []
    timp_cursor = sunset
    for i in range(12):
        planeta = chaldean[index_curent]
        start_ora = timp_cursor
        timp_cursor += lungime_ora_noapte
        ore_noapte.append((i + 1, planeta, start_ora, timp_cursor))
        index_curent = (index_curent + 1) % 7
    
    # Determinăm ora curentă
    current_hour = None
    for num, planet, start, end in ore_zi:
        if start <= now_dt < end:
            current_hour = (num, planet, start, end, 'zi')
            break
    
    if current_hour is None:
        for num, planet, start, end in ore_noapte:
            if start <= now_dt < end:
                current_hour = (num, planet, start, end, 'noapte')
                break
    
    # Combiăm orele pentru afișare
    hours = []
    for num, planet, start, end in ore_zi:
        hours.append((num, planet, start, end, 'zi'))
    for num, planet, start, end in ore_noapte:
        hours.append((num, planet, start, end, 'noapte'))
    
    return hours, current_hour, lungime_ora_zi.total_seconds(), lungime_ora_noapte.total_seconds()

def get_lunar_mansion(lon):
    for number, name, trans, start, end in mansions_list:
        if start <= lon < end:
            return number, name, trans
    return None, None, None
    
def find_mean_node_crossings(jd_start, jd_end):
    crossings = []
    step = 0.05
    jd_curr = jd_start
    prev_diff = None
    
    while jd_curr < jd_end:
        moon_lon = swe.calc_ut(jd_curr, swe.MOON, swe.FLG_SWIEPH)[0][0]
        node_lon = swe.calc_ut(jd_curr, swe.MEAN_NODE, swe.FLG_SWIEPH)[0][0]
        
        diff = (moon_lon - node_lon + 180) % 360 - 180
        
        if prev_diff is not None and prev_diff * diff < 0:
            jd_left = jd_curr - step
            jd_right = jd_curr
            for _ in range(30):
                jd_mid = (jd_left + jd_right) / 2
                moon_mid = swe.calc_ut(jd_mid, swe.MOON, swe.FLG_SWIEPH)[0][0]
                node_mid = swe.calc_ut(jd_mid, swe.MEAN_NODE, swe.FLG_SWIEPH)[0][0]
                diff_mid = (moon_mid - node_mid + 180) % 360 - 180
                
                moon_left = swe.calc_ut(jd_left, swe.MOON, swe.FLG_SWIEPH)[0][0]
                node_left = swe.calc_ut(jd_left, swe.MEAN_NODE, swe.FLG_SWIEPH)[0][0]
                diff_left = (moon_left - node_left + 180) % 360 - 180
                
                if diff_left * diff_mid < 0:
                    jd_right = jd_mid
                else:
                    jd_left = jd_mid
            
            jd_exact = (jd_left + jd_right) / 2
            crossings.append(jd_exact)
        
        prev_diff = diff
        jd_curr += step
    
    return crossings
    
def find_all_lunar_events(start_utc, end_utc, ts, eph, earth, moon_eph):
    """Găsește toate evenimentele lunare importante într-un interval"""
    events = []
    
    t_start = ts.from_datetime(start_utc)
    t_end = ts.from_datetime(end_utc)
    
    # 1. Fazele Lunii
    from skyfield import almanac
    f_phases = almanac.moon_phases(eph)
    phases_times, phases_events = almanac.find_discrete(t_start, t_end, f_phases)
    phase_names = {0: "Lună Nouă 🌑", 1: "Primul Pătrar 🌓", 2: "Lună Plină 🌕", 3: "Ultimul Pătrar 🌗"}
    for t, ev in zip(phases_times, phases_events):
        if ev in phase_names:
            events.append((t, phase_names[ev], 'phase'))
    
    # 2. Noduri
    jd_start = swe.julday(start_utc.year, start_utc.month, start_utc.day,
                          start_utc.hour + start_utc.minute/60.0 + start_utc.second/3600.0)
    jd_end = swe.julday(end_utc.year, end_utc.month, end_utc.day,
                        end_utc.hour + end_utc.minute/60.0 + end_utc.second/3600.0)
    
    node_jds = find_mean_node_crossings(jd_start, jd_end)
    for jd_node in node_jds:
        t_node = ts.tt_jd(jd_node)
        # Determină tipul nodului din latitudine
        moon_lat_before = swe.calc_ut(jd_node - 0.05, swe.MOON, swe.FLG_SWIEPH)[0][1]
        moon_lat_after = swe.calc_ut(jd_node + 0.05, swe.MOON, swe.FLG_SWIEPH)[0][1]
        if moon_lat_after > moon_lat_before:
            label = "Nod Ascendent (☊)"
        else:
            label = "Nod Descendent (☋)"
        events.append((t_node, label, 'node'))
    
    # 3. Perigeu și Apogeu
    times_pg = []
    t_p = t_start
    while t_p.tt < t_end.tt:
        times_pg.append(t_p)
        t_p = ts.tt_jd(t_p.tt + 0.05)
    distances_pg = [earth.at(t).observe(moon_eph).distance().km for t in times_pg]
    
    for i in range(1, len(distances_pg) - 1):
        if distances_pg[i] < distances_pg[i-1] and distances_pg[i] < distances_pg[i+1]:
            t_exact, d_exact = refine_extremum(times_pg[i], True, earth, moon_eph, ts)
            events.append((t_exact, f"Perigeu ⬇ {d_exact:,.0f} km", 'perigee'))
        elif distances_pg[i] > distances_pg[i-1] and distances_pg[i] > distances_pg[i+1]:
            t_exact, d_exact = refine_extremum(times_pg[i], False, earth, moon_eph, ts)
            events.append((t_exact, f"Apogeu ⬆ {d_exact:,.0f} km", 'apogee'))
    
    # Sortează după timp (FĂRĂ a elimina evenimente apropiate)
    events.sort(key=lambda x: x[0])
    
    return events

# ═══════════════════════════════════════════════════════════════
# CACHE PENTRU CALCULE PRINCIPALE (1 minut)
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def calculate_all_data(_now_utc, _now_local):
    """Calculează toate datele și returnează un dicționar"""
    ts, eph = load_ephemeris()
    earth = eph['earth']
    sun = eph['sun']
    moon_eph = eph['moon']
    observer = earth + wgs84.latlon(LAT, LON, ELEVATION)
    t_now = ts.from_datetime(_now_utc)
    
    jd = swe.julday(_now_utc.year, _now_utc.month, _now_utc.day,
                    _now_utc.hour + _now_utc.minute/60.0 + _now_utc.second/3600.0)
    
    data = {'jd': jd}
    
    # Parametri de bază
    data['ayanamsa'] = swe.get_ayanamsa_ut(jd)
    ecl_nut = swe.calc_ut(jd, swe.ECL_NUT)
    data['obliquity'] = ecl_nut[0][0]
    data['nutation'] = ecl_nut[0][1:]
    gmst = swe.sidtime(jd)
    data['sidereal_time'] = (gmst + LON/15.0) % 24
    
    # Soare
    sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
    data['sun_lon'] = sun_pos[0]
    data['sun_lat'] = sun_pos[1]
    data['sun_dist'] = sun_pos[2]
    data['sun_speed'] = sun_pos[3]
    data['sun_equ'] = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)[0]
    data['sun_xyz'] = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_XYZ)[0]
    
    sun_app = observer.at(t_now).observe(sun).apparent()
    sun_alt, sun_az, _ = sun_app.altaz()
    data['sun_alt'] = sun_alt.degrees
    data['sun_az'] = sun_az.degrees
    
    # Răsărit/Apus Soare
    t0 = ts.from_datetime(_now_utc.replace(hour=0, minute=0, second=0))
    t1 = ts.from_datetime((_now_utc + timedelta(days=1)).replace(hour=0, minute=0, second=0))
    f_rs = almanac.sunrise_sunset(eph, wgs84.latlon(LAT, LON))
    times_rs, events_rs = almanac.find_discrete(t0, t1, f_rs)
    
    sunrise_today = sunset_today = None
    for t, ev in zip(times_rs, events_rs):
        if ev == 1:
            sunrise_today = t.astimezone(TZ)
        else:
            sunset_today = t.astimezone(TZ)
    data['sunrise_today'] = sunrise_today
    data['sunset_today'] = sunset_today
    
    # Răsărit mâine
    t0_tom = ts.from_datetime((_now_utc + timedelta(days=1)).replace(hour=0, minute=0, second=0))
    t1_tom = ts.from_datetime((_now_utc + timedelta(days=2)).replace(hour=0, minute=0, second=0))
    times_rs_tom, events_rs_tom = almanac.find_discrete(t0_tom, t1_tom, f_rs)
    sunrise_next = None
    for t, ev in zip(times_rs_tom, events_rs_tom):
        if ev == 1:
            sunrise_next = t.astimezone(TZ)
            break
    data['sunrise_next'] = sunrise_next
    
    # Azimut răsărit/apus
    sunrise_az = sunset_az = None
    if sunrise_today:
        t_sr = ts.from_datetime(sunrise_today.astimezone(pytz.UTC))
        _, sunrise_az, _ = observer.at(t_sr).observe(sun).apparent().altaz()
        sunrise_az = sunrise_az.degrees
    if sunset_today:
        t_ss = ts.from_datetime(sunset_today.astimezone(pytz.UTC))
        _, sunset_az, _ = observer.at(t_ss).observe(sun).apparent().altaz()
        sunset_az = sunset_az.degrees
    data['sunrise_az'] = sunrise_az
    data['sunset_az'] = sunset_az
    
    # Culminații Soare
    f_mt = almanac.meridian_transits(eph, sun, wgs84.latlon(LAT, LON))
    times_mt, events_mt = almanac.find_discrete(t0, t1, f_mt)
    culm_sup = culm_inf = None
    alt_culm_sup = alt_culm_inf = None
    for t, ev in zip(times_mt, events_mt):
        alt_mt, _, _ = observer.at(t).observe(sun).apparent().altaz()
        if ev == 1:
            culm_sup = t.astimezone(TZ)
            alt_culm_sup = alt_mt.degrees
        else:
            culm_inf = t.astimezone(TZ)
            alt_culm_inf = alt_mt.degrees
    data['culm_sup'] = culm_sup
    data['culm_inf'] = culm_inf
    data['alt_culm_sup'] = alt_culm_sup
    data['alt_culm_inf'] = alt_culm_inf
    
    # Amurguri (calculate din altitudinea Soarelui)
    twilights = []
    midnight = _now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    
    found_civil_dim = False
    found_nautic_dim = False
    found_astro_dim = False
    found_astro_seara = False
    found_nautic_seara = False
    found_civil_seara = False
    
    prev_alt = None
    for minutes in range(0, 24*60, 1):
        dt = midnight + timedelta(minutes=minutes)
        t = ts.from_datetime(dt.astimezone(pytz.UTC))
        alt, _, _ = observer.at(t).observe(sun).apparent().altaz()
        current_alt = alt.degrees
        
        if prev_alt is not None:
            # Dimineața (alt crește)
            if current_alt > prev_alt and current_alt < 0:
                if not found_astro_dim and prev_alt < -18 <= current_alt:
                    twilights.append(("Amurg astronomic (dim)", dt.strftime('%H:%M:%S')))
                    found_astro_dim = True
                if not found_nautic_dim and prev_alt < -12 <= current_alt:
                    twilights.append(("Amurg nautic (dim)", dt.strftime('%H:%M:%S')))
                    found_nautic_dim = True
                if not found_civil_dim and prev_alt < -6 <= current_alt:
                    twilights.append(("Amurg civil (dim)", dt.strftime('%H:%M:%S')))
                    found_civil_dim = True
            
            # Seara (alt scade)
            if current_alt < prev_alt and current_alt < 0:
                if not found_civil_seara and prev_alt > -6 >= current_alt:
                    twilights.append(("Amurg civil (seară)", dt.strftime('%H:%M:%S')))
                    found_civil_seara = True
                if not found_nautic_seara and prev_alt > -12 >= current_alt:
                    twilights.append(("Amurg nautic (seară)", dt.strftime('%H:%M:%S')))
                    found_nautic_seara = True
                if not found_astro_seara and prev_alt > -18 >= current_alt:
                    twilights.append(("Amurg astronomic (seară)", dt.strftime('%H:%M:%S')))
                    found_astro_seara = True
        
        prev_alt = current_alt
    
    data['twilights'] = twilights
    
    # Ore planetare
    hours_plan, current_hour, day_h, night_h = get_planetary_hours(
        sunrise_today, sunset_today, sunrise_next, _now_local
    )
    data['hours_plan'] = hours_plan
    data['current_hour'] = current_hour
    data['day_h'] = day_h
    data['night_h'] = night_h
    
    # Periheliu/Afeliu
    t_ph_start = ts.from_datetime(datetime(_now_utc.year, 1, 1, tzinfo=pytz.UTC))
    t_ph_end = ts.from_datetime(datetime(_now_utc.year + 1, 1, 1, tzinfo=pytz.UTC))
    times_ph = []
    t = t_ph_start
    while t.tt < t_ph_end.tt:
        times_ph.append(t)
        t = ts.tt_jd(t.tt + 0.25)
    distances_ph = [earth.at(t).observe(sun).distance().km for t in times_ph]
    min_idx = distances_ph.index(min(distances_ph))
    max_idx = distances_ph.index(max(distances_ph))
    data['perihelion_t'], data['perihelion_d'] = refine_extremum(times_ph[min_idx], True, earth, sun, ts)
    data['aphelion_t'], data['aphelion_d'] = refine_extremum(times_ph[max_idx], False, earth, sun, ts)
    
    # Anotimp
    seasons = {(0, 90): "Primăvară (N)", (90, 180): "Vară (N)", (180, 270): "Toamnă (N)", (270, 360): "Iarnă (N)"}
    data['current_season'] = None
    for (s, e), name in seasons.items():
        if s <= data['sun_lon'] < e:
            data['current_season'] = name
            break
    
    # Echinocții și Solstiții
    t_start_eq = ts.from_datetime(_now_utc)
    t_end_eq = ts.from_datetime(datetime(_now_utc.year + 2, 1, 1, tzinfo=pytz.UTC))
    f_seasons = almanac.seasons(eph)
    times_s, events_s = almanac.find_discrete(t_start_eq, t_end_eq, f_seasons)
    s_names = {0: 'Echinocțiul de primăvară', 1: 'Solstițiul de vară', 2: 'Echinocțiul de toamnă', 3: 'Solstițiul de iarnă'}
    data['next_seasons'] = []
    for t, ev in zip(times_s, events_s):
        if len(data['next_seasons']) >= 4:
            break
        data['next_seasons'].append((s_names[ev], t.astimezone(TZ).strftime('%Y-%m-%d %H:%M:%S')))
    
    # Lună
    moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
    data['moon_lon'] = moon_pos[0]
    data['moon_lat'] = moon_pos[1]
    data['moon_dist'] = moon_pos[2]
    data['moon_speed'] = moon_pos[3]
    data['moon_equ'] = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)[0]
    data['moon_xyz'] = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_XYZ)[0]
    
    moon_app = observer.at(t_now).observe(moon_eph).apparent()
    moon_alt, moon_az, _ = moon_app.altaz()
    data['moon_alt'] = moon_alt.degrees
    data['moon_az'] = moon_az.degrees
    
    # Arc solar-lunar și iluminare
    data['arc_sl'] = (data['moon_lon'] - data['sun_lon']) % 360
    data['moon_illum'] = almanac.fraction_illuminated(eph, 'moon', t_now)
    data['moon_age'] = data['arc_sl'] / 360 * 29.530588853
    
    # Faza calitativă
    if data['moon_illum'] < 0.01:
        data['moon_phase_name'] = "Lună Nouă"
    elif data['moon_illum'] < 0.499:
        data['moon_phase_name'] = "Crescătoare" if data['arc_sl'] < 180 else "Descrescătoare"
    elif data['moon_illum'] < 0.501:
        data['moon_phase_name'] = "Lună Plină"
    else:
        data['moon_phase_name'] = "Crescătoare" if data['arc_sl'] < 180 else "Descrescătoare"
    
    # Conac Arabesc
    data['mansion_num'], data['mansion_name'], data['mansion_trans'] = get_lunar_mansion(data['moon_lon'])
    
    # Răsărit/Apus Lună
    t0_moon = ts.from_datetime(_now_utc)
    t1_moon = ts.from_datetime(_now_utc + timedelta(days=2))
    f_mr = almanac.risings_and_settings(eph, moon_eph, wgs84.latlon(LAT, LON))
    times_mr, events_mr = almanac.find_discrete(t0_moon, t1_moon, f_mr)
    moonrise_next = moonset_next = None
    for t, ev in zip(times_mr, events_mr):
        if ev == 1 and moonrise_next is None:
            moonrise_next = t.astimezone(TZ)
        elif ev == 0 and moonset_next is None:
            moonset_next = t.astimezone(TZ)
    data['moonrise_next'] = moonrise_next
    data['moonset_next'] = moonset_next
    
    # Culminații Lună
    f_mc = almanac.meridian_transits(eph, moon_eph, wgs84.latlon(LAT, LON))
    times_mc, events_mc = almanac.find_discrete(t0_moon, t1_moon, f_mc)
    moon_culm_sup = moon_culm_inf = None
    moon_alt_culm_sup = moon_alt_culm_inf = None
    for t, ev in zip(times_mc, events_mc):
        alt_mc, _, _ = observer.at(t).observe(moon_eph).apparent().altaz()
        if ev == 1 and moon_culm_sup is None:
            moon_culm_sup = t.astimezone(TZ)
            moon_alt_culm_sup = alt_mc.degrees
        elif ev == 0 and moon_culm_inf is None:
            moon_culm_inf = t.astimezone(TZ)
            moon_alt_culm_inf = alt_mc.degrees
    data['moon_culm_sup'] = moon_culm_sup
    data['moon_culm_inf'] = moon_culm_inf
    data['moon_alt_culm_sup'] = moon_alt_culm_sup
    data['moon_alt_culm_inf'] = moon_alt_culm_inf
    
    # Noduri Lunare
    jd_start_nodes = jd
    jd_end_nodes = jd + 40
    node_jds = find_mean_node_crossings(jd_start_nodes, jd_end_nodes)
    node_labels = ["Nod Ascendent (☊)", "Nod Descendent (☋)"]

    # Noduri Lunare (inclusiv anterioare, ±25 zile)
    jd_start_nodes = jd - 25
    jd_end_nodes = jd + 35
    node_jds_all = find_mean_node_crossings(jd_start_nodes, jd_end_nodes)
    
    # Versiunea cu obiecte Time (pentru bara de progres)
    data['moon_nodes_all_time'] = []
    # Versiunea cu string-uri (pentru afișare)
    data['moon_nodes_all_str'] = []
    
    for jd_node in node_jds_all[:6]:
        t_node = ts.tt_jd(jd_node)
        
        # Determină dacă este Nod Ascendent sau Descendent
        # Calculăm longitudinea Lunii cu 0.1 zile înainte pentru a vedea direcția
        jd_test = jd_node + 0.1
        moon_lon_now = swe.calc_ut(jd_node, swe.MOON, swe.FLG_SWIEPH)[0][0]
        moon_lon_test = swe.calc_ut(jd_test, swe.MOON, swe.FLG_SWIEPH)[0][0]
        
        # La nodul ascendent, longitudinea Lunii crește trecând peste longitudinea nodului
        # La nodul descendent, longitudinea Lunii scade
        node_lon = swe.calc_ut(jd_node, swe.MEAN_NODE, swe.FLG_SWIEPH)[0][0]
        
        # Calculăm diferența
        diff_now = (moon_lon_now - node_lon + 360) % 360
        diff_test = (moon_lon_test - node_lon + 360) % 360
        
        # Dacă diff_test > diff_now, Luna se îndepărtează de nod (după trecere)
        # Determinarea corectă:
        if diff_test < 180 and diff_now < 180:
            # Crește sau scade?
            if diff_test > diff_now:
                label = "Nod Ascendent (☊)"  # Trecând de la < la > longitudine nod
            else:
                label = "Nod Descendent (☋)"
        else:
            # Caz particular când diferența trece prin 0
            if diff_test < diff_now and diff_test < 10:
                label = "Nod Ascendent (☊)"
            else:
                label = "Nod Descendent (☋)"
        
        # O metodă mai simplă și mai sigură: folosim latitudinea Lunii
        # La nodul ascendent, Luna trece de la latitudine negativă la pozitivă
        # La nodul descendent, invers
        moon_lat_now = swe.calc_ut(jd_node - 0.05, swe.MOON, swe.FLG_SWIEPH)[0][1]
        moon_lat_test = swe.calc_ut(jd_node + 0.05, swe.MOON, swe.FLG_SWIEPH)[0][1]
        
        if moon_lat_test > moon_lat_now:
            label = "Nod Ascendent (☊)"  # Latitudinea crește (trece de la - la +)
        else:
            label = "Nod Descendent (☋)"  # Latitudinea scade (trece de la + la -)
        
        data['moon_nodes_all_time'].append((label, t_node))
        data['moon_nodes_all_str'].append((label, t_node.astimezone(TZ).strftime('%d %b %Y %H:%M')))
    
    data['moon_nodes_all'] = data['moon_nodes_all_str']
    data['moon_nodes'] = data['moon_nodes_all'][:2]
    
    # Perigeu/Apogeu
    t_pg_start = ts.from_datetime(_now_utc)
    t_pg_end = ts.from_datetime(_now_utc + timedelta(days=35))
    times_pg = []
    t_p = t_pg_start
    while t_p.tt < t_pg_end.tt:
        times_pg.append(t_p)
        t_p = ts.tt_jd(t_p.tt + 0.05)
    distances_pg = [earth.at(t).observe(moon_eph).distance().km for t in times_pg]
    min_idx_pg = distances_pg.index(min(distances_pg))
    max_idx_pg = distances_pg.index(max(distances_pg))
    data['perigee_t'], data['perigee_d'] = refine_extremum(times_pg[min_idx_pg], True, earth, moon_eph, ts)
    data['apogee_t'], data['apogee_d'] = refine_extremum(times_pg[max_idx_pg], False, earth, moon_eph, ts)
    
    # Perigeu/Apogeu (inclusiv anterioare, ±25 zile) - găsește toate extremele locale
    t_pg_all_start = ts.from_datetime(_now_utc - timedelta(days=25))
    t_pg_all_end = ts.from_datetime(_now_utc + timedelta(days=25))
    times_pg_all = []
    t_p = t_pg_all_start
    while t_p.tt < t_pg_all_end.tt:
        times_pg_all.append(t_p)
        t_p = ts.tt_jd(t_p.tt + 0.05)
    distances_pg_all = [earth.at(t).observe(moon_eph).distance().km for t in times_pg_all]
    
    # Găsește toate perigeurile și apogeurile din interval
    all_perigees = []
    all_apogees = []
    
    for i in range(1, len(distances_pg_all) - 1):
        if distances_pg_all[i] < distances_pg_all[i-1] and distances_pg_all[i] < distances_pg_all[i+1]:
            # Minim local -> perigeu
            t_exact, d_exact = refine_extremum(times_pg_all[i], True, earth, moon_eph, ts)
            all_perigees.append((t_exact, d_exact))
        elif distances_pg_all[i] > distances_pg_all[i-1] and distances_pg_all[i] > distances_pg_all[i+1]:
            # Maxim local -> apogeu
            t_exact, d_exact = refine_extremum(times_pg_all[i], False, earth, moon_eph, ts)
            all_apogees.append((t_exact, d_exact))
    
    # Pentru secțiunea de evenimente (următoarele 35 zile) folosim primul din viitor
    next_perigee = None
    for t_exact, d_exact in all_perigees:
        if t_exact.astimezone(TZ) > _now_local:
            next_perigee = (t_exact, d_exact)
            break
    
    next_apogee = None
    for t_exact, d_exact in all_apogees:
        if t_exact.astimezone(TZ) > _now_local:
            next_apogee = (t_exact, d_exact)
            break
    
    # Pentru barele de progres, avem nevoie de ultimul și următorul eveniment
    # (indiferent dacă e perigeu sau apogeu)
    all_events = []
    for t_exact, d_exact in all_perigees:
        all_events.append(('P', t_exact, d_exact))
    for t_exact, d_exact in all_apogees:
        all_events.append(('A', t_exact, d_exact))
    all_events.sort(key=lambda x: x[1])
    
    # Găsește evenimentul anterior și următorul față de now
    prev_event = None
    next_event = None
    for label, t_exact, d_exact in all_events:
        if t_exact.astimezone(TZ) <= _now_local:
            prev_event = (label, t_exact, d_exact)
        else:
            if next_event is None:
                next_event = (label, t_exact, d_exact)
                break
    
    # Salvează în data pentru a fi folosite în interfață
    data['perigee_t_all'] = next_perigee[0] if next_perigee else None
    data['perigee_d_all'] = next_perigee[1] if next_perigee else None
    data['apogee_t_all'] = next_apogee[0] if next_apogee else None
    data['apogee_d_all'] = next_apogee[1] if next_apogee else None
    
    # Salvează evenimentele pentru bara de progres
    data['prev_ap_event'] = prev_event
    data['next_ap_event'] = next_event       
    
    # Fazele Lunii
    t_faze_start = ts.from_datetime(_now_utc)
    t_faze_end = ts.from_datetime(_now_utc + timedelta(days=35))
    f_moon_phases = almanac.moon_phases(eph)
    times_faze, events_faze = almanac.find_discrete(t_faze_start, t_faze_end, f_moon_phases)
    faze_names = {0: "Lună Nouă 🌑", 1: "Primul Pătrar 🌓", 2: "Lună Plină 🌕", 3: "Ultimul Pătrar 🌗"}
    data['moon_phases'] = []
    for t_f, ev_f in zip(times_faze, events_faze):
        if ev_f in faze_names:
            data['moon_phases'].append((faze_names[ev_f], t_f.astimezone(TZ).strftime('%d %b %Y %H:%M')))
    
    # Fazele Lunii (inclusiv anterioare, ±20 zile)
    t_faze_all_start = ts.from_datetime(_now_utc - timedelta(days=20))
    t_faze_all_end = ts.from_datetime(_now_utc + timedelta(days=35))
    times_faze_all, events_faze_all = almanac.find_discrete(t_faze_all_start, t_faze_all_end, f_moon_phases)
    data['moon_phases_all'] = []
    for t_f, ev_f in zip(times_faze_all, events_faze_all):
        if ev_f in faze_names:
            data['moon_phases_all'].append((faze_names[ev_f], t_f.astimezone(TZ).strftime('%d %b %Y %H:%M')))    
    
    
    # Planete
    planet_ids = {
        'Soare': swe.SUN, 'Luna': swe.MOON, 'Mercur': swe.MERCURY,
        'Venus': swe.VENUS, 'Marte': swe.MARS, 'Jupiter': swe.JUPITER,
        'Saturn': swe.SATURN, 'Uranus': swe.URANUS, 'Neptun': swe.NEPTUNE,
        'Pluto': swe.PLUTO,
    }
    
    data['planet_data'] = {}
    for name, pid in planet_ids.items():
        pos = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
        ret_flag = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SPEED)[1]
        data['planet_data'][name] = {
            'lon': pos[0], 'lat': pos[1], 'dist': pos[2],
            'speed': pos[3], 'retro': pos[3] < 0
        }
    
    # Noduri și Lilith
    nn_pos = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SWIEPH)[0]
    data['planet_data']['Nod Nord (Mean)'] = {'lon': nn_pos[0], 'lat': nn_pos[1], 'dist': nn_pos[2], 'speed': nn_pos[3], 'retro': False}
    data['planet_data']['Nod Sud (Mean)'] = {'lon': (nn_pos[0] + 180) % 360, 'lat': -nn_pos[1], 'dist': nn_pos[2], 'speed': nn_pos[3], 'retro': False}
    lilith_pos = swe.calc_ut(jd, swe.MEAN_APOG, swe.FLG_SWIEPH)[0]
    data['planet_data']['Lilith (Mean)'] = {'lon': lilith_pos[0], 'lat': lilith_pos[1], 'dist': lilith_pos[2], 'speed': lilith_pos[3], 'retro': False}
    
    # Asteroizi
    asteroid_ids = {
        'Chiron': swe.CHIRON, 'Ceres': swe.CERES, 'Pallas': swe.PALLAS,
        'Juno': swe.JUNO, 'Vesta': swe.VESTA,
    }
    for name, aid in asteroid_ids.items():
        pos = swe.calc_ut(jd, aid, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
        data['planet_data'][name] = {'lon': pos[0], 'lat': pos[1], 'dist': pos[2], 'speed': pos[3], 'retro': pos[3] < 0}
    
    # Stele fixe
    fixed_stars_list = [
        'Aldebaran', 'Regulus', 'Antares', 'Fomalhaut',
        'Spica', 'Sirius', 'Vega', 'Pollux', 'Castor',
        'Procyon', 'Betelgeuse', 'Rigel', 'Capella',
        'Deneb', 'Altair', 'Arcturus'
    ]
    data['fixed_stars_names'] = []
    for star_name in fixed_stars_list:
        try:
            star_data, star_name_ret, _ = swe.fixstar_ut(star_name, jd, swe.FLG_SWIEPH)
            if star_name_ret not in data['planet_data']:
                data['planet_data'][star_name_ret] = {'lon': star_data[0], 'lat': star_data[1], 'dist': 0, 'speed': 0, 'retro': False}
                data['fixed_stars_names'].append(star_name_ret)
        except:
            pass
    
    # Case astrologice
    cusps, ascmc = swe.houses_ex(jd, LAT, LON, b'P')
    data['ascendant'] = ascmc[0]
    data['mc'] = ascmc[1]
    
    # Skyfield names pentru planete
    data['skyfield_names'] = {
        'Soare': 'SUN', 'Luna': 'MOON', 'Mercur': 'MERCURY', 'Venus': 'VENUS',
        'Marte': 'MARS', 'Jupiter': 'JUPITER BARYCENTER', 'Saturn': 'SATURN BARYCENTER',
        'Uranus': 'URANUS BARYCENTER', 'Neptun': 'NEPTUNE BARYCENTER', 'Pluto': 'PLUTO BARYCENTER',
    }
    
    data['planet_ids'] = planet_ids
    data['asteroid_ids'] = asteroid_ids
    
    # Toate evenimentele lunare unificate (pentru afișare)
    end_utc = _now_utc + timedelta(days=45)
    data['all_lunar_events'] = find_all_lunar_events(_now_utc, end_utc, ts, eph, earth, moon_eph)
        
    return data
    
# ═══════════════════════════════════════════════════════════════
# INTERFAȚA STREAMLIT
# ═══════════════════════════════════════════════════════════════

st.markdown("""
<style>
    .stApp, .stMarkdown, .stCaption, .stText, p, div, span, label {
        font-size: 18px !important;
        color: #000000 !important;
    }
    h2, h3, .stSubheader {
        font-size: 18px !important;
        color: #000000 !important;
        font-weight: bold;
    }
    .stCaption {
        color: #000000 !important;
        font-size: 18px !important;
    }
    .streamlit-expanderContent p {
        font-size: 18px !important;
        color: #000000 !important;
    }
    
    /* NOI REGULI PENTRU BARELE DE PROGRES */
    div[data-testid="column"] {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 50px;
    }
    
    div[data-testid="column"] h1 {
        font-size: 28px !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1 !important;
    }
    
    .stProgress > div {
        margin: 0 !important;
    }
    
    /* >>> NEW RULE TO FORCE SCROLLING <<< */
    .main > div {
        overflow-y: auto !important;
        height: 100vh !important;
    }
    section.main > div {
        overflow-y: auto !important;
    }    
</style>
""", unsafe_allow_html=True)

# Inițializare
now = datetime.now(TZ)
now_utc = now.astimezone(pytz.UTC)
data = calculate_all_data(now_utc, now)
ts, eph = load_ephemeris()
observer = eph['earth'] + wgs84.latlon(LAT, LON, ELEVATION)
t_now = ts.from_datetime(now_utc)
sun = eph['sun']
moon_eph = eph['moon']

# Extrageri rapide
jd = data['jd']
ts, eph = load_ephemeris()
observer = eph['earth'] + wgs84.latlon(LAT, LON, ELEVATION)
t_now = ts.from_datetime(now_utc)
sun = eph['sun']
moon_eph = eph['moon']
earth = eph['earth']

# ═══════════════════════════ HEADER ═══════════════════════════

day_of_year = now.timetuple().tm_yday
week_number = now.isocalendar()[1]
day_name_ro = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri', 'Sâmbătă', 'Duminică'][now.weekday()]
day_rulers = {0: 'Luna', 1: 'Marte', 2: 'Mercur', 3: 'Jupiter', 4: 'Venus', 5: 'Saturn', 6: 'Soare'}
day_ruler = day_rulers[now.weekday()]
hour_ruler = data['current_hour'][1] if data['current_hour'] else ""

st.subheader("Astro")
st.markdown(f"""
**{day_name_ro}, {now.strftime('%d %B %Y, %H:%M:%S %Z')}**  
(UTC: {now_utc.strftime('%d-%m-%Y %H:%M:%S')}) · JD: {jd:.4f}  
**București, Romania** ({LAT}° N, {LON}° E)  
Ziua {day_of_year} din an · Săptămâna {week_number}  
Guvernator zi: **{day_ruler}** · Guvernator oră: **{hour_ruler}**
""")

st.divider()

# ═══════════════════════════ TABURI ═══════════════════════════

tab1, tab2, tab3, tab4 = st.tabs(["Soare", "Lună", "Planete", "Aspecte"])

# ═══════════════════════════ TAB 1: SOARE ═══════════════════════
with tab1:
    st.subheader("Soare")
    
    sun_lon = data['sun_lon']
    sun_lat = data['sun_lat']
    sun_dist = data['sun_dist']
    sun_speed = data['sun_speed']
    sun_equ = data['sun_equ']
    sun_xyz = data['sun_xyz']
    sun_alt = data['sun_alt']
    sun_az = data['sun_az']
    sunrise_today = data['sunrise_today']
    sunset_today = data['sunset_today']
    sunrise_next = data['sunrise_next']
    sunrise_az = data['sunrise_az']
    sunset_az = data['sunset_az']
    culm_sup = data['culm_sup']
    culm_inf = data['culm_inf']
    alt_culm_sup = data['alt_culm_sup']
    alt_culm_inf = data['alt_culm_inf']
    twilights = data['twilights']
    hours_plan = data['hours_plan']
    current_hour = data['current_hour']
    day_h = data['day_h']
    night_h = data['night_h']
    perihelion_t = data['perihelion_t']
    perihelion_d = data['perihelion_d']
    aphelion_t = data['aphelion_t']
    aphelion_d = data['aphelion_d']
    current_season = data['current_season']
    next_seasons = data['next_seasons']
    
    # Rânduri principale
    st.caption(f"Poziție: {format_zodiac(sun_lon)}")
    st.caption(f"Răsărit: {sunrise_today.strftime('%H:%M:%S') if sunrise_today else '-'}")
    st.caption(f"Culminație superioară: {culm_sup.strftime('%H:%M:%S')} ({alt_culm_sup:.1f}°)" if culm_sup else "Culminație superioară: -")
    st.caption(f"Apus: {sunset_today.strftime('%H:%M:%S') if sunset_today else '-'}")
    st.caption(f"Culminație inferioară: {culm_inf.strftime('%H:%M:%S')} ({alt_culm_inf:.1f}°)" if culm_inf else "Culminație inferioară: -")
    st.caption(f"Altitudine (acum): {sun_alt:.2f}°")
    st.caption(f"Azimut (acum): {sun_az:.2f}°")
    
    # Expander 1: Amurguri
    with st.expander("Amurguri"):
        for name, time_str in twilights:
            st.caption(f"{name}: {time_str}")
    
    # Expander 2: Date orbitale și coordonate
    with st.expander("Date orbitale și coordonate"):
        st.caption(f"Longitudine ecliptică: {format_dms(sun_lon)}")
        st.caption(f"Latitudine ecliptică: {format_dms(sun_lat, True)}")
        st.caption(f"Distanță (AU): {sun_dist:.6f}")
        st.caption(f"Viteză longitudinală: {sun_speed:.6f} °/zi")
        st.caption(f"Ascensie dreaptă: {format_dms(sun_equ[0])}")
        st.caption(f"Declinație: {format_dms(sun_equ[1], True)}")
        st.caption(f"Coord. X (AU): {sun_xyz[0]:.6f}")
        st.caption(f"Coord. Y (AU): {sun_xyz[1]:.6f}")
        st.caption(f"Coord. Z (AU): {sun_xyz[2]:.6f}")
        st.caption(f"Azimut răsărit: {sunrise_az:.2f}°" if sunrise_az else "Azimut răsărit: -")
        st.caption(f"Azimut apus: {sunset_az:.2f}°" if sunset_az else "Azimut apus: -")
    
    # Expander 3: Durate și ore planetare
    with st.expander("Durata zilei și ore planetare"):
        if sunrise_today and sunset_today:
            day_dur = (sunset_today - sunrise_today).total_seconds()
            night_dur = (sunrise_next - sunset_today).total_seconds() if sunrise_next else (86400 - day_dur)
            
            st.caption(f"Durata zilei: {int(day_dur//3600)}h {int(day_dur//60)%60:02d}m {int(day_dur%60):02d}s")
            st.caption(f"Durata nopții: {int(night_dur//3600)}h {int(night_dur//60)%60:02d}m {int(night_dur%60):02d}s")
            st.caption(f"Proporție: {day_dur/864:.1f}% zi / {night_dur/864:.1f}% noapte")
            st.caption(f"Oră planetară (zi): {int(day_h//60)}m {int(day_h%60):02.0f}s")
            st.caption(f"Oră planetară (noapte): {int(night_h//60)}m {int(night_h%60):02.0f}s")
            
            if current_hour:
                num, planet, start, end, tip = current_hour
                st.caption(f"Ora planetară curentă: {planet} (ora {num}, {tip}) {start.strftime('%H:%M')} – {end.strftime('%H:%M')}")
            
        with st.expander("Toate cele 24 de ore planetare"):
            for num, planet, start, end, tip in hours_plan:
                line = f"Ora {num:02d} ({tip}): {planet} {start.strftime('%H:%M')} – {end.strftime('%H:%M')}"
                if current_hour and num == current_hour[0] and tip == current_hour[4]:
                    st.caption(f"**{line}**")
                else:
                    st.caption(line)
    
    # Expander 4: Anotimpuri
    with st.expander("Anotimpuri"):
        st.caption(f"Anotimp curent: {current_season or '-'}")
        with st.expander("Echinocții și Solstiții"):
            for name, date_str in next_seasons:
                st.caption(f"{name}: {date_str}")
    
    # Expander 5: Periheliu și Afeliu
    with st.expander("Periheliu și Afeliu"):
        if perihelion_t is not None and aphelion_t is not None:
            current_dist = earth.at(t_now).observe(sun).distance().km
            min_d = perihelion_d
            max_d = aphelion_d
            progress = (current_dist - min_d) / (max_d - min_d)
            
            peri_day = perihelion_t.astimezone(TZ).timetuple().tm_yday
            aph_day = aphelion_t.astimezone(TZ).timetuple().tm_yday
            today_day = now.timetuple().tm_yday
            
            if peri_day < aph_day:
                going_to_aphelion = today_day < aph_day
            else:
                going_to_aphelion = today_day < aph_day or today_day >= peri_day
            
            st.caption(f"Periheliu: {min_d:,.0f} km ({perihelion_t.astimezone(TZ).strftime('%d %b %Y %H:%M')})")
            st.progress(float(progress))
            st.caption(f"Afeliu: {max_d:,.0f} km ({aphelion_t.astimezone(TZ).strftime('%d %b %Y %H:%M')})")
            
            if going_to_aphelion:
                st.caption(f"Acum: {current_dist:,.0f} km → ne îndreptăm spre afeliu")
            else:
                st.caption(f"Acum: {current_dist:,.0f} km ← ne întoarcem spre periheliu")
    
    # Expander 6: Sinusoida altitudinii Soarelui (24h)
    with st.expander("Sinusoida altitudinii Soarelui (24h)"):
        times_sin = []
        alts_sin = []
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for minutes in range(0, 24*60, 5):
            dt = midnight + timedelta(minutes=minutes)
            t = ts.from_datetime(dt.astimezone(pytz.UTC))
            alt, _, _ = observer.at(t).observe(sun).apparent().altaz()
            times_sin.append(dt.strftime('%H:%M'))
            alts_sin.append(alt.degrees)        
        import plotly.graph_objects as go
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=times_sin, y=alts_sin, mode='lines',
                                 line=dict(color='#f0c040', width=1.5), showlegend=False))
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.4)
        
        def closest_index(target_dt):
            return round((target_dt.hour * 60 + target_dt.minute) / 5)
        
        alt_now_sun, _, _ = observer.at(t_now).observe(sun).apparent().altaz()
        idx_now = closest_index(now)
        fig.add_trace(go.Scatter(x=[times_sin[idx_now]], y=[alt_now_sun.degrees], mode='markers',
                                 marker=dict(color='gold', size=10, symbol='circle',
                                             line=dict(color='orange', width=1)),
                                 showlegend=False))
        
        if sunrise_today:
            idx_sr = closest_index(sunrise_today)
            fig.add_trace(go.Scatter(x=[times_sin[idx_sr]], y=[0], mode='markers+text',
                                     marker=dict(color='orange', size=8, symbol='triangle-up'),
                                     text=['R'], textposition='top center', textfont=dict(size=9),
                                     showlegend=False))
        
        if sunset_today:
            idx_ss = closest_index(sunset_today)
            fig.add_trace(go.Scatter(x=[times_sin[idx_ss]], y=[0], mode='markers+text',
                                     marker=dict(color='red', size=8, symbol='triangle-down'),
                                     text=['A'], textposition='top center', textfont=dict(size=9),
                                     showlegend=False))
        
        if culm_sup:
            idx_culm = closest_index(culm_sup)
            fig.add_trace(go.Scatter(x=[times_sin[idx_culm]], y=[alt_culm_sup], mode='markers+text',
                                     marker=dict(color='yellow', size=8, symbol='diamond'),
                                     text=['C'], textposition='bottom center', textfont=dict(size=9),
                                     showlegend=False))
        
        # Ore pe axa X: doar răsărit, culminație, apus
        tick_vals = []
        tick_texts = []
        if sunrise_today: tick_vals.append(sunrise_today.strftime('%H:%M')); tick_texts.append('R')
        if culm_sup: tick_vals.append(culm_sup.strftime('%H:%M')); tick_texts.append('C')
        if sunset_today: tick_vals.append(sunset_today.strftime('%H:%M')); tick_texts.append('A')
        
        fig.update_layout(
            xaxis=dict(tickmode='array', tickvals=tick_vals, ticktext=tick_texts, showgrid=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=200, margin=dict(l=0, r=0, t=0, b=20),
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    
    # Expander 7: Grafic proporție zi/noapte
    with st.expander("Proporția zi/noapte"):
        if sunrise_today and sunset_today:
            day_sec = (sunset_today - sunrise_today).total_seconds()
            night_sec = 86400 - day_sec
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=['Zi', 'Noapte'], values=[day_sec, night_sec],
                marker=dict(colors=['#f0c040', '#1a1a2e']), hole=0.1,
                rotation=0.743 * sunrise_az + 202.04,
                textinfo='label+percent',
                textfont=dict(size=14, color=['black', 'white'])
            )])
            
            fig_pie.update_layout(
                title=f"Zi: {int(day_sec//3600)}h {int(day_sec//60)%60:02d}m | Noapte: {int(night_sec//3600)}h {int(night_sec//60)%60:02d}m",
                height=400, margin=dict(l=20, r=20, t=40, b=20), template="plotly_white"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            st.caption(f"Răsărit: {sunrise_today.strftime('%H:%M:%S')} | Apus: {sunset_today.strftime('%H:%M:%S')}")

# ═══════════════════════════ TAB 2: LUNĂ ═══════════════════════
with tab2:
    st.subheader("Lună")
    
    moon_lon = data['moon_lon']
    moon_lat = data['moon_lat']
    moon_dist = data['moon_dist']
    moon_speed = data['moon_speed']
    moon_equ = data['moon_equ']
    moon_xyz = data['moon_xyz']
    moon_alt = data['moon_alt']
    moon_az = data['moon_az']
    arc_sl = data['arc_sl']
    moon_illum = data['moon_illum']
    moon_age = data['moon_age']
    moon_phase_name = data['moon_phase_name']
    mansion_num = data['mansion_num']
    mansion_name = data['mansion_name']
    mansion_trans = data['mansion_trans']
    moonrise_next = data['moonrise_next']
    moonset_next = data['moonset_next']
    moon_culm_sup = data['moon_culm_sup']
    moon_culm_inf = data['moon_culm_inf']
    moon_alt_culm_sup = data['moon_alt_culm_sup']
    moon_alt_culm_inf = data['moon_alt_culm_inf']
    moon_nodes = data['moon_nodes']
    moon_phases = data['moon_phases']
    perigee_t = data['perigee_t']
    perigee_d = data['perigee_d']
    apogee_t = data['apogee_t']
    apogee_d = data['apogee_d']
    
    # Rânduri principale
    st.caption(f"Poziție: {format_zodiac(moon_lon)}")
    st.caption(f"Răsărit: {moonrise_next.strftime('%d %b %H:%M') if moonrise_next else '-'}")
    st.caption(f"Culminație superioară: {moon_culm_sup.strftime('%d %b %H:%M')} ({moon_alt_culm_sup:.1f}°)" if moon_culm_sup else "Culminație superioară: -")
    st.caption(f"Apus: {moonset_next.strftime('%d %b %H:%M') if moonset_next else '-'}")
    st.caption(f"Culminație inferioară: {moon_culm_inf.strftime('%d %b %H:%M')} ({moon_alt_culm_inf:.1f}°)" if moon_culm_inf else "Culminație inferioară: -")
    st.caption(f"Altitudine (acum): {moon_alt:.2f}°")
    st.caption(f"Azimut (acum): {moon_az:.2f}°")
    st.caption(f"Arc solar-lunar: {format_dms(arc_sl)}")
    st.caption(f"Iluminare: {moon_illum*100:.2f}%")
    st.caption(f"Vârsta Lunii: {moon_age:.2f} zile")
    st.caption(f"Fază: {moon_phase_name}")
        
    if mansion_num:
        # Găsim următorul conac
        next_mansion_num = mansion_num + 1 if mansion_num < 28 else 1
        next_start = mansions_list[next_mansion_num - 1][3]  # start-ul următorului
        
        # Calculăm când Luna atinge longitudinea de start a următorului conac
        jd_next = jd
        step = 0.05
        prev_diff = None
        while jd_next < jd + 30:
            moon_lon_next = swe.calc_ut(jd_next, swe.MOON, swe.FLG_SWIEPH)[0][0]
            diff = (moon_lon_next - next_start + 180) % 360 - 180
            
            if prev_diff is not None and prev_diff * diff < 0:
                jd_left = jd_next - step
                jd_right = jd_next
                for _ in range(30):
                    jd_mid = (jd_left + jd_right) / 2
                    moon_mid = swe.calc_ut(jd_mid, swe.MOON, swe.FLG_SWIEPH)[0][0]
                    diff_mid = (moon_mid - next_start + 180) % 360 - 180
                    
                    moon_left = swe.calc_ut(jd_left, swe.MOON, swe.FLG_SWIEPH)[0][0]
                    diff_left = (moon_left - next_start + 180) % 360 - 180
                    
                    if diff_left * diff_mid < 0:
                        jd_right = jd_mid
                    else:
                        jd_left = jd_mid
                
                jd_exact = (jd_left + jd_right) / 2
                t_next = ts.tt_jd(jd_exact)
                next_date = t_next.astimezone(TZ).strftime('%d %b %Y %H:%M')
                next_name = mansions_list[next_mansion_num - 1][1]
                
                if mansion_trans != "TBD":
                    st.caption(f"Conac Arabesc: {mansion_num}. {mansion_name} — {mansion_trans}")
                else:
                    st.caption(f"Conac Arabesc: {mansion_num}. {mansion_name}")
                st.caption(f"→ {next_name} ({next_date})")
                break
            
            prev_diff = diff
            jd_next += step
    

    # Expander 1: Conace Arabești
    with st.expander("Conacele Arabești"):
        for num, name, trans, start, end in mansions_list:
            display = f"{name} — {trans}" if trans != "TBD" else name
            if mansion_num and num == mansion_num:
                st.caption(f"**{num}. {display}** ({format_dms(start)} – {format_dms(end)})")
            else:
                st.caption(f"{num}. {display} ({format_dms(start)} – {format_dms(end)})")
    
    # Expander 2: Date orbitale și coordonate
    with st.expander("Date orbitale și coordonate"):
        st.caption(f"Longitudine ecliptică: {format_dms(moon_lon)}")
        st.caption(f"Latitudine ecliptică: {format_dms(moon_lat, True)}")
        st.caption(f"Distanță (AU): {moon_dist:.6f}")
        st.caption(f"Distanță (km): {moon_dist * 149597870.7:,.0f}")
        st.caption(f"Viteză longitudinală: {moon_speed:.6f} °/zi")
        st.caption(f"Ascensie dreaptă: {format_dms(moon_equ[0])}")
        st.caption(f"Declinație: {format_dms(moon_equ[1], True)}")
        st.caption(f"Coord. X (AU): {moon_xyz[0]:.6f}")
        st.caption(f"Coord. Y (AU): {moon_xyz[1]:.6f}")
        st.caption(f"Coord. Z (AU): {moon_xyz[2]:.6f}")
    
    # Expander 3: Evenimente Lunare
    with st.expander("Evenimente Lunare (următoarele 45 zile)"):
        all_events = data.get('all_lunar_events', [])
        
        if all_events:
            for t_event, label, event_type in all_events:
                dt_event = t_event.astimezone(TZ)
                if dt_event >= now:  # doar evenimente din viitor
                    st.caption(f"{label}: {dt_event.strftime('%d %b %Y %H:%M')}")
        else:
            st.caption("Nu s-au găsit evenimente")
    
    
    # Expander 3b: Bare de progres Lunare
    with st.expander("Progres Lună (faze, noduri, distanță)"):
        
        # Folosim datele extinse (inclusiv anterioare)
        moon_phases_all = data.get('moon_phases_all', moon_phases)
        moon_nodes_all = data.get('moon_nodes_all', moon_nodes)
        perigee_t_all = data.get('perigee_t_all', perigee_t)
        perigee_d_all = data.get('perigee_d_all', perigee_d)
        apogee_t_all = data.get('apogee_t_all', apogee_t)
        apogee_d_all = data.get('apogee_d_all', apogee_d)
        
        # ─── Bara 1: Faza anterioară → Faza următoare ───
        if len(moon_phases_all) >= 2:
            # Sortăm fazele
            sorted_phases = []
            for label, date_str in moon_phases_all:
                dt = datetime.strptime(date_str, '%d %b %Y %H:%M')
                dt = TZ.localize(dt)
                sorted_phases.append((label, dt, date_str))
            sorted_phases.sort(key=lambda x: x[1])
            
            # Găsim faza anterioară și următoarea
            prev_phase = None
            next_phase = None
            for i, (label, dt, date_str) in enumerate(sorted_phases):
                if dt <= now:
                    prev_phase = (label, dt, date_str)
                elif dt > now and next_phase is None:
                    next_phase = (label, dt, date_str)
                    break
            
            if prev_phase and next_phase:
                def phase_icon(label):
                    if "🌑" in label: return "🌑"
                    elif "🌓" in label: return "🌓"
                    elif "🌕" in label: return "🌕"
                    elif "🌗" in label: return "🌗"
                    return ""
                
                left_icon = phase_icon(prev_phase[0])
                right_icon = phase_icon(next_phase[0])
                
                total_sec = (next_phase[1] - prev_phase[1]).total_seconds()
                elapsed_sec = (now - prev_phase[1]).total_seconds()
                progress_phase = max(0, min(1, elapsed_sec / total_sec))
                
                remaining_sec = total_sec - elapsed_sec
                rem_d = int(remaining_sec // 86400)
                rem_h = int((remaining_sec % 86400) // 3600)
                rem_m = int((remaining_sec % 3600) // 60)
                
                st.markdown(f"""
                <div style="display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: nowrap;">
                    <div style="flex: 0 0 auto; min-width: 50px; text-align: center;">
                        <span style='font-size: 32px; line-height: 1;'>{left_icon}</span>
                    </div>
                    <div style="flex: 1 1 auto; min-width: 100px;">
                        <div style='background-color: #e0e0e0; border-radius: 10px; height: 6px;'>
                            <div style='width: {progress_phase*100}%; background-color: #3182ce; height: 6px; border-radius: 10px;'></div>
                        </div>
                    </div>
                    <div style="flex: 0 0 auto; min-width: 50px; text-align: center;">
                        <span style='font-size: 32px; line-height: 1;'>{right_icon}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.caption(f"{prev_phase[0]} → {next_phase[0]} ({rem_d}z {rem_h}h {rem_m}m)")
            else:
                st.caption("Faze: date insuficiente")
        else:
            st.caption("Faze: date insuficiente")
        
        st.caption("")
        
        # ─── Bara 2: Noduri Lunare ───
        moon_nodes_all_time = data.get('moon_nodes_all_time', [])
        
        if len(moon_nodes_all_time) >= 2:
            # Găsește nodul anterior și următorul
            prev_node = None
            next_node = None
            
            for label, t_node in moon_nodes_all_time:
                dt_node = t_node.astimezone(TZ)
                if dt_node <= now:
                    prev_node = (label, dt_node)
                elif dt_node > now and next_node is None:
                    next_node = (label, dt_node)
                    break
            
            if prev_node and next_node:
                left_icon = "☊" if "Ascendent" in prev_node[0] else "☋"
                right_icon = "☊" if "Ascendent" in next_node[0] else "☋"
                
                total_sec_n = (next_node[1] - prev_node[1]).total_seconds()
                elapsed_sec_n = (now - prev_node[1]).total_seconds()
                progress_node = max(0, min(1, elapsed_sec_n / total_sec_n))
                
                remaining_sec_n = total_sec_n - elapsed_sec_n
                rem_d_n = int(remaining_sec_n // 86400)
                rem_h_n = int((remaining_sec_n % 86400) // 3600)
                rem_m_n = int((remaining_sec_n % 3600) // 60)
                
                st.markdown(f"""
                <div style="display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: nowrap;">
                    <div style="flex: 0 0 auto; min-width: 50px; text-align: center;">
                        <span style='font-size: 32px; line-height: 1;'>{left_icon}</span>
                    </div>
                    <div style="flex: 1 1 auto; min-width: 100px;">
                        <div style='background-color: #e0e0e0; border-radius: 10px; height: 6px;'>
                            <div style='width: {progress_node*100}%; background-color: #3182ce; height: 6px; border-radius: 10px;'></div>
                        </div>
                    </div>
                    <div style="flex: 0 0 auto; min-width: 50px; text-align: center;">
                        <span style='font-size: 32px; line-height: 1;'>{right_icon}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.caption(f"{prev_node[0]} → {next_node[0]} ({rem_d_n}z {rem_h_n}h {rem_m_n}m)")
            else:
                st.caption("Noduri: date insuficiente")
        else:
            st.caption("Noduri: date insuficiente")
        
        st.caption("")
        
        # ─── Bara 3: Evenimentul anterior → Evenimentul următor ───
        prev_event = data.get('prev_ap_event')
        next_event = data.get('next_ap_event')
        
        if prev_event and next_event:
            label_prev, t_prev, dist_prev = prev_event
            label_next, t_next, dist_next = next_event
            
            # Convertim skyfield Time în datetime
            dt_prev = t_prev.astimezone(TZ)
            dt_next = t_next.astimezone(TZ)
            
            total_sec_ap = (dt_next - dt_prev).total_seconds()
            elapsed_sec_ap = (now - dt_prev).total_seconds()
            progress_ap = max(0, min(1, elapsed_sec_ap / total_sec_ap))
            
            remaining_sec_ap = total_sec_ap - elapsed_sec_ap
            rem_d_ap = int(remaining_sec_ap // 86400)
            rem_h_ap = int((remaining_sec_ap % 86400) // 3600)
            rem_m_ap = int((remaining_sec_ap % 3600) // 60)
            
            st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: nowrap;">
                <div style="flex: 0 0 auto; min-width: 50px; text-align: center;">
                    <span style='font-size: 32px; font-weight: bold; line-height: 1;'>{label_prev}</span>
                </div>
                <div style="flex: 1 1 auto; min-width: 100px;">
                    <div style='background-color: #e0e0e0; border-radius: 10px; height: 6px;'>
                        <div style='width: {progress_ap*100}%; background-color: #3182ce; height: 6px; border-radius: 10px;'></div>
                    </div>
                </div>
                <div style="flex: 0 0 auto; min-width: 50px; text-align: center;">
                    <span style='font-size: 32px; font-weight: bold; line-height: 1;'>{label_next}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.caption(f"{label_prev} ({dist_prev:,.0f} km) → {label_next} ({dist_next:,.0f} km) ({rem_d_ap}z {rem_h_ap}h {rem_m_ap}m)")
        else:
            st.caption("Perigeu/Apogeu: date insuficiente")
    
    
    
    # Expander 4: Sinusoida altitudinii Lunii (24h)
    with st.expander("Sinusoida altitudinii Lunii (24h)"):
        times_sin_moon = []
        alts_sin_moon = []
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for minutes in range(0, 24*60, 5):
            dt = midnight + timedelta(minutes=minutes)
            t = ts.from_datetime(dt.astimezone(pytz.UTC))
            alt, _, _ = observer.at(t).observe(moon_eph).apparent().altaz()
            times_sin_moon.append(dt.strftime('%H:%M'))
            alts_sin_moon.append(alt.degrees)
        
        import plotly.graph_objects as go
        
        fig_moon = go.Figure()
        fig_moon.add_trace(go.Scatter(x=times_sin_moon, y=alts_sin_moon, mode='lines',
                                      line=dict(color='#c0c0c0', width=1.5), showlegend=False))
        fig_moon.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.4)
        
        def closest_index(target_dt):
            return round((target_dt.hour * 60 + target_dt.minute) / 5)
        
        alt_now_moon, _, _ = observer.at(t_now).observe(moon_eph).apparent().altaz()
        idx_now_moon = closest_index(now)
        fig_moon.add_trace(go.Scatter(x=[times_sin_moon[idx_now_moon]], y=[alt_now_moon.degrees],
                                      mode='markers', marker=dict(color='silver', size=10, symbol='circle',
                                                                  line=dict(color='gray', width=1)),
                                      showlegend=False))
        
        if moonrise_next:
            idx_mr = closest_index(moonrise_next)
            fig_moon.add_trace(go.Scatter(x=[times_sin_moon[idx_mr]], y=[0], mode='markers+text',
                                          marker=dict(color='lightblue', size=8, symbol='triangle-up'),
                                          text=['R'], textposition='top center', textfont=dict(size=9),
                                          showlegend=False))
        
        if moonset_next:
            idx_ms = closest_index(moonset_next)
            fig_moon.add_trace(go.Scatter(x=[times_sin_moon[idx_ms]], y=[0], mode='markers+text',
                                          marker=dict(color='lightcoral', size=8, symbol='triangle-down'),
                                          text=['A'], textposition='top center', textfont=dict(size=9),
                                          showlegend=False))
        
        if moon_culm_sup:
            idx_mc = closest_index(moon_culm_sup)
            fig_moon.add_trace(go.Scatter(x=[times_sin_moon[idx_mc]], y=[moon_alt_culm_sup], mode='markers+text',
                                          marker=dict(color='yellow', size=8, symbol='diamond'),
                                          text=['C'], textposition='bottom center', textfont=dict(size=9),
                                          showlegend=False))
        
        tick_vals = []
        tick_texts = []
        if moonrise_next: tick_vals.append(moonrise_next.strftime('%H:%M')); tick_texts.append('R')
        if moon_culm_sup: tick_vals.append(moon_culm_sup.strftime('%H:%M')); tick_texts.append('C')
        if moonset_next: tick_vals.append(moonset_next.strftime('%H:%M')); tick_texts.append('A')
        
        fig_moon.update_layout(
            xaxis=dict(tickmode='array', tickvals=tick_vals, ticktext=tick_texts, showgrid=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=200, margin=dict(l=0, r=0, t=0, b=20),
            template="plotly_white"
        )
        st.plotly_chart(fig_moon, use_container_width=True, config={'displayModeBar': False})    
    
    
    # Expander 5: Faza Lunii
    with st.expander("Faza Lunii (vizual)"):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            iluminare_procent = moon_illum * 100
            is_waning = arc_sl > 180
            
            fig_luna, ax_luna = plt.subplots(figsize=(3, 3), facecolor='white')
            ax_luna.set_xlim(-1.05, 1.05)
            ax_luna.set_ylim(-1.05, 1.05)
            ax_luna.set_aspect('equal')
            ax_luna.axis('off')
            
            c_lumina = '#fefeec'
            c_umbra = '#2c2c2c'
            
            if not is_waning:
                stanga_color, dreapta_color = c_umbra, c_lumina
                elipsa_color = c_umbra if iluminare_procent < 50 else c_lumina
            else:
                stanga_color, dreapta_color = c_lumina, c_umbra
                elipsa_color = c_lumina if iluminare_procent < 50 else c_umbra
            
            ax_luna.add_patch(Wedge((0, 0), 1, 90, 270, color=stanga_color, zorder=1))
            ax_luna.add_patch(Wedge((0, 0), 1, -90, 90, color=dreapta_color, zorder=1))
            
            latime_elipsa = abs(2.0 * (iluminare_procent / 100.0) - 1.0)
            if latime_elipsa > 0:
                ax_luna.add_patch(Ellipse((0, 0), latime_elipsa * 2, 2, color=elipsa_color, zorder=2))
            
            ax_luna.add_patch(plt.Circle((0, 0), 1, color='black', fill=False, linewidth=1.5, zorder=3))
            st.pyplot(fig_luna)
            st.caption(f"Iluminare: {iluminare_procent:.1f}% | {moon_phase_name}")
        
        with col2:
            st.caption(f"Vârsta Lunii: {moon_age:.2f} zile")
            st.caption(f"Arc solar-lunar: {format_dms(arc_sl)}")
            st.caption("Iluminare:")
            st.progress(float(moon_illum))
            st.caption(f"{iluminare_procent:.1f}%")
            st.caption("")
            st.caption("Fazele următoare:")
            for label, date_str in moon_phases[:4]:
                st.caption(f"{label}: {date_str}")
                
# ═══════════════════════════ TAB 3: PLANETE ═══════════════════════
with tab3:
    st.subheader("Planete")
    
    planet_data = data['planet_data']
    planet_ids = data['planet_ids']
    asteroid_ids = data['asteroid_ids']
    skyfield_names = data['skyfield_names']
    fixed_stars_names = data['fixed_stars_names']
    ascendant = data['ascendant']
    mc = data['mc']
    
    # Demnități
    dignities = {
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
    
    def get_dignity(name, lon):
        if name not in dignities:
            return ""
        signs = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis']
        sign_idx = int(lon // 30)
        current_sign = signs[sign_idx]
        
        d = dignities[name]
        dom_signs = d['dom'].split('/')
        exil_signs = d['exil'].split('/')
        
        if current_sign in dom_signs:
            return "D"
        elif current_sign == d['ex']:
            return "X"
        elif current_sign in exil_signs:
            return "E"
        elif current_sign == d['cad']:
            return "C"
        return ""
    
    # Rânduri principale
    all_bodies = list(planet_ids.keys()) + ['Nod Nord (Mean)', 'Nod Sud (Mean)', 'Lilith (Mean)'] + list(asteroid_ids.keys())
    
    for name in all_bodies:
        if name not in planet_data:
            continue
        pdata = planet_data[name]
        dign = get_dignity(name, pdata['lon']) if name in dignities else ""
        retro_str = " R" if pdata['retro'] else ""
        dign_str = f" [{dign}]" if dign else ""
        
        st.caption(f"{name}: {format_zodiac(pdata['lon'])}{retro_str}{dign_str} | Viteză: {pdata['speed']:.4f}°/zi")
    
    # Expander 1: Date orbitale complete
    with st.expander("Date orbitale și coordonate"):
        for name in all_bodies:
            if name not in planet_data:
                continue
            pdata = planet_data[name]
            dec_str = ""
            if name in planet_ids:
                equ_pos = swe.calc_ut(jd, planet_ids[name], swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)[0]
                dec_str = f" | Decl {format_dms(equ_pos[1], True)}"
            
            st.caption(f"{name}: L {format_dms(pdata['lon'])} | B {format_dms(pdata['lat'], True)} | Dist {pdata['dist']:.6f} AU | Viteză {pdata['speed']:.4f}°/zi{dec_str}")
    
    # Expander 2: Altitudine/Azimut
    with st.expander("Altitudine și Azimut (acum)"):
        visible_planets = []
        for name in planet_ids:
            if name in ['Soare', 'Luna']:
                continue
            sname = skyfield_names[name]
            try:
                p = observer.at(t_now).observe(eph[sname]).apparent()
                alt, az, _ = p.altaz()
                visible_planets.append((name, alt.degrees, az.degrees))
            except:
                pass
        
        alt_sun, az_sun, _ = observer.at(t_now).observe(sun).apparent().altaz()
        alt_moon, az_moon, _ = observer.at(t_now).observe(moon_eph).apparent().altaz()
        visible_planets.insert(0, ('Luna', alt_moon.degrees, az_moon.degrees))
        visible_planets.insert(0, ('Soare', alt_sun.degrees, az_sun.degrees))
        
        for name, alt, az in visible_planets:
            st.caption(f"{name}: alt {alt:.2f}° | az {az:.2f}°")
    
    # Expander 3: Răsărit/Apus planete
    with st.expander("Răsărit și Apus (următoarele 24h)"):
        t0_planets = ts.from_datetime(now_utc)
        t1_planets = ts.from_datetime(now_utc + timedelta(hours=24))
        
        planet_rise_set = []
        for name, sname in skyfield_names.items():
            if name in ['Soare', 'Luna']:
                continue
            try:
                f_rs = almanac.risings_and_settings(eph, eph[sname], wgs84.latlon(LAT, LON))
                times_rs, events_rs = almanac.find_discrete(t0_planets, t1_planets, f_rs)
                for t, ev in zip(times_rs, events_rs):
                    if ev == 1:
                        planet_rise_set.append((name, 'Răsărit', t.astimezone(TZ).strftime('%H:%M')))
                    elif ev == 0:
                        planet_rise_set.append((name, 'Apus', t.astimezone(TZ).strftime('%H:%M')))
            except:
                pass
        
        if planet_rise_set:
            planet_rise_set.sort(key=lambda x: x[2])
            for name, event, time_str in planet_rise_set:
                st.caption(f"{name}: {event} {time_str}")
        else:
            st.caption("Nicio planetă nu răsare/apune în următoarele 24h")
    
    # Expander 4: Faze Mercur și Venus
    with st.expander("Fazele planetelor interioare"):
        col1, col2 = st.columns(2)
        
        for inner_name, inner_sname in [('Mercur', 'MERCURY'), ('Venus', 'VENUS')]:
            with col1 if inner_name == 'Mercur' else col2:
                inner_pos = earth.at(t_now).observe(eph[inner_sname]).apparent()
                sun_pos_now = earth.at(t_now).observe(sun).apparent()
                phase_angle = sun_pos_now.separation_from(inner_pos)
                illum_pct = (1 + math.cos(phase_angle.radians)) / 2 * 100
                
                st.caption(f"{inner_name}: iluminare {illum_pct:.1f}%")
                st.progress(float(illum_pct / 100))
    
    # Expander 5: Unghiuri (AS, MC)
    with st.expander("Unghiuri (Ascendent și MC)"):
        st.caption(f"Ascendent: {format_zodiac(ascendant)} ({format_dms(ascendant)})")
        st.caption(f"MC (Midheaven): {format_zodiac(mc)} ({format_dms(mc)})")
    
    # Expander 6: Stele Fixe Principale
    with st.expander("Stele Fixe Principale"):
        for star_name in fixed_stars_names:
            if star_name in planet_data:
                st.caption(f"{star_name}: {format_zodiac(planet_data[star_name]['lon'])}")
                
# ═══════════════════════════ TAB 4: ASPECTE ═══════════════════════
with tab4:
    st.subheader("Aspecte")
    
    orb = st.slider("Orb (grade)", min_value=1.0, max_value=8.0, value=0.5, step=0.5)
    
    fixed_stars_list = [
        'Aldebaran', 'Regulus', 'Antares', 'Fomalhaut',
        'Spica', 'Sirius', 'Vega', 'Pollux', 'Castor',
        'Procyon', 'Betelgeuse', 'Rigel', 'Capella',
        'Deneb', 'Altair', 'Arcturus'
    ]
    fixed_stars_names = []
    for star_name in fixed_stars_list:
        try:
            star_data, star_name_ret, _ = swe.fixstar_ut(star_name, jd, swe.FLG_SWIEPH)
            if star_name_ret not in planet_data:
                planet_data[star_name_ret] = {'lon': star_data[0], 'lat': star_data[1], 'dist': 0, 'speed': 0, 'retro': False}
                fixed_stars_names.append(star_name_ret)
        except:
            pass
    
    all_bodies_list = list(planet_ids.keys()) + ['Nod Nord (Mean)', 'Nod Sud (Mean)', 'Lilith (Mean)'] + list(asteroid_ids.keys()) + fixed_stars_names
    
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
        
        for j, body2 in enumerate(all_bodies_list):
            if j <= i:
                continue
            if body2 not in planet_data:
                continue
            
            if body1 in ['Nod Nord (Mean)', 'Nod Sud (Mean)'] and body2 in ['Nod Nord (Mean)', 'Nod Sud (Mean)']:
                continue
            
            lon2 = planet_data[body2]['lon']
            
            diff = abs(lon2 - lon1)
            if diff > 180:
                diff = 360 - diff
            
            for aspect_name, aspect_angle in aspect_types.items():
                angle_diff = abs(diff - aspect_angle)
                if angle_diff <= orb:
                    speed1 = planet_data[body1]['speed']
                    speed2 = planet_data[body2]['speed']
                    
                    if speed1 > speed2:
                        sign = "+"
                    elif speed2 > speed1:
                        sign = "-"
                    else:
                        sign = ""
                    
                    aspects.append((angle_diff, body1, body2, aspect_name, sign))
    
    aspects.sort(key=lambda x: x[0])
    
    if aspects:
        for diff, body1, body2, aspect_name, sign in aspects:
            diff_dms = format_dms(diff)
            st.caption(f"{body1} – {body2}: {aspect_name} ({diff_dms}{sign})")
    else:
        st.caption("Niciun aspect cu orbul selectat.")

st.divider()
st.caption(f"Generat la {now.strftime('%Y-%m-%d %H:%M:%S')}")