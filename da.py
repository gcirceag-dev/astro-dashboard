import streamlit as st
import os
import math
import json
from datetime import datetime, timedelta
import pytz
import swisseph as swe
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Ellipse

# =====================================================================
# CONFIGURARE STREAMLIT
# =====================================================================
st.set_page_config(
    page_title="Dashboard astro",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Stil CSS minimalist
st.markdown("""
<style>
    .stApp {
        max-width: 1000px;
        margin: 0 auto;
    }
    .stMarkdown, .stText, .stDataFrame, .stMetric {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #000000;
        font-size: 16px !important;
    }
    .stDataFrame {
        font-size: 15px !important;
    }
    .stExpander {
        border: none;
        box-shadow: none;
    }
    table {
        font-size: 15px !important;
    }
    td, th {
        white-space: normal !important;
        word-wrap: break-word !important;
    }
    hr {
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================================
# BLOCUL 1: CONFIGURARE, COORDONATE FIXE ȘI CĂI
# =====================================================================
LATITUDINE = 44.42
LONGITUDINE = 26.12
ALTITUDINE = 80.0  # metri

cale_curenta = os.path.dirname(os.path.abspath(__file__))
cale_efemeride = os.path.join(cale_curenta, "ephe")
swe.set_ephe_path(cale_efemeride)

swe.set_topo(LONGITUDINE, LATITUDINE, ALTITUDINE)

zona_locala = pytz.timezone("Europe/Bucharest")
UA_IN_KM = 149597870.7

CALC_RISE = 1
CALC_SET = 2
CALC_TRANSIT = 4
FLAG_FIIZIC = swe.FLG_SWIEPH | swe.FLG_SPEED

ORDINE_CHALDEAN = ["Saturn", "Jupiter", "Marte", "Soare", "Venus", "Mercur", "Luna"]

STAPAN_ZI = {
    0: "Luna", 1: "Marte", 2: "Mercur", 3: "Jupiter", 4: "Venus", 5: "Saturn", 6: "Soare"
}

DEMNITATI_MODERNE = {
    "Soare":   {"dom": ["Leo"],             "exalt": ["Ari"],    "exil": ["Aqu"],          "cadere": ["Lib"]},
    "Luna":    {"dom": ["Can"],             "exalt": ["Tau"],      "exil": ["Cap"],         "cadere": ["Sco"]},
    "Mercur":  {"dom": ["Gem", "Vir"], "exalt": ["Vir"], "exil": ["Sag", "Pis"], "cadere": ["Pis"]},
    "Venus":   {"dom": ["Tau", "Lib"], "exalt": ["Pis"],     "exil": ["Sco", "Ari"], "cadere": ["Vir"]},
    "Marte":   {"dom": ["Ari", "Sco"], "exalt": ["Cap"], "exil": ["Lib", "Tau"],    "cadere": ["Can"]},
    "Jupiter": {"dom": ["Sag", "Pis"], "exalt": ["Can"],       "exil": ["Gem", "Vir"], "cadere": ["Cap"]},
    "Saturn":  {"dom": ["Cap", "Aqu"], "exalt": ["Lib"], "exil": ["Can", "Leo"],         "cadere": ["Ari"]},
    "Uranus":  {"dom": ["Aqu"],         "exalt": ["Sco"],  "exil": ["Leo"],               "cadere": ["Tau"]},
    "Neptun":  {"dom": ["Pis"],            "exalt": ["Can"],       "exil": ["Vir"],          "cadere": ["Cap"]},
    "Pluto":   {"dom": ["Sco"],         "exalt": ["Ari"],    "exil": ["Tau"],              "cadere": ["Lib"]}
}

SEMNE_ZODIAC = [
    "Ari", "Tau", "Gem", "Can", "Leo", "Vir",
    "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"
]

MANZILE_DATE = {
    1: ("Al-Sharatain", "Cele doua semne"), 2: ("Al-Butain", "Micul pantece"), 3: ("Al-Thurayya", "Pleiadele / Abundenta"),
    4: ("Al-Dabaran", "Urmaritorul / Aldebaran"), 5: ("Al-Haq'ah", "Cercul de par / Corona"), 6: ("Al-Han'ah", "Semnul de foc / Arc"),
    7: ("Al-Dhira", "Bratul leului / Gem"), 8: ("Al-Nathrah", "Zborul / Cuibul"), 9: ("Al-Tarf", "Privirea / Ochii Leolui"),
    10: ("Al-Jabhah", "Fruntea Leolui / Regulus"), 11: ("Al-Zubrah", "Coama Leolui"), 12: ("Al-Sarfah", "Schimbatorul de vreme"),
    13: ("Al-Awwa", "Cainele latrator"), 14: ("Al-Simak", "Cel Neinarmat / Spica"), 15: ("Al-Ghafr", "Acoperamantul"),
    16: ("Al-Zubana", "Clestii Scoului"), 17: ("Al-Iklil", "Coroana"), 18: ("Al-Qalb", "Inima / Antares"),
    19: ("Al-Shaulah", "Acul Scoului"), 20: ("Al-Na'aim", "Strutii"), 21: ("Al-Baldah", "Orasul / Spatiul gol"),
    22: ("Al-Sa'd al-Dhabih", "Norocul Macelarului"), 23: ("Al-Sa'd al-Bula", "Norocul Inghititorului"),
    24: ("Al-Sa'd al-Su'ud", "Norocul Norocurilor"), 25: ("Al-Sa'd al-Ahbiyah", "Norocul Corturilor"),
    26: ("Al-Fargh al-Muqaddam", "Gura de sus a putului"), 27: ("Al-Fargh al-Mu'ahhar", "Gura de jos a putului"),
    28: ("Risha / Batn al-Hut", "Pantecele Pestelui")
}

ASPECTE_MAJORE = {
    "CON": 0.0,
    "SEX": 60.0,
    "CAR": 90.0,
    "TRI": 120.0,
    "OPO": 180.0
}

# =====================================================================
# BLOCUL 2: UTILITARE PENTRU TIMP ȘI FORMATĂRI
# =====================================================================
def get_times():
    """Obține timpul curent, rotunjit la minutul fix, pentru sincronizare perfectă."""
    acum_local = datetime.now(zona_locala)
    
    acum_local = acum_local.replace(second=0, microsecond=0)
    acum_utc = acum_local.astimezone(pytz.utc)
    
    jd_acum = swe.julday(
        acum_utc.year, acum_utc.month, acum_utc.day,
        acum_utc.hour + acum_utc.minute / 60.0 + acum_utc.second / 3600.0
    )
    
    miez_local = acum_local.replace(hour=0, minute=0, second=0, microsecond=0)
    miez_utc = miez_local.astimezone(pytz.utc)
    jd_miez = swe.julday(
        miez_utc.year, miez_utc.month, miez_utc.day,
        miez_utc.hour + miez_utc.minute / 60.0 + miez_utc.second / 3600.0
    )
    
    return acum_local, jd_acum, jd_miez

def jd_to_datetime(jd_val):
    year, month, day, hour_dec = swe.revjul(jd_val)
    h = int(hour_dec)
    m = int((hour_dec - h) * 60)
    s = int(round((((hour_dec - h) * 60) - m) * 60))
    if s >= 60: m += 1; s = 0
    if m >= 60: h += 1; m = 0
    dt_utc = datetime(year, month, day, h, m, s, tzinfo=pytz.utc)
    return dt_utc.astimezone(zona_locala)

def format_grade(grade_zecimale):
    semn = "-" if grade_zecimale < 0 else ""
    val = abs(grade_zecimale)
    d = int(val)
    m = int((val - d) * 60)
    s = int(round((((val - d) * 60) - m) * 60))
    if s >= 60: m += 1; s = 0
    if m >= 60: d += 1; m = 0
    return f"{semn}{d}°{m:02d}'{s:02d}\""

def format_durata(ore_zecimale):
    h = int(ore_zecimale)
    m = int((ore_zecimale - h) * 60)
    s = int(round((((ore_zecimale - h) * 60) - m) * 60))
    if s >= 60: m += 1; s = 0
    if m >= 60: h += 1; m = 0
    return f"{h:02d} h {m:02d} m {s:02d} s"

def format_pozitie_astrologica(lon_zecimala):
    index_semn = int(lon_zecimala / 30.0) % 12
    grade_in_semn = lon_zecimala % 30.0
    
    m = int((grade_in_semn - int(grade_in_semn)) * 60)
    s = int(round((((grade_in_semn - int(grade_in_semn)) * 60) - m) * 60))
    if s >= 60: m += 1; s = 0
    if m >= 60: grade_in_semn += 1; m = 0
    
    nume_semn = SEMNE_ZODIAC[index_semn]
    return f"{int(grade_in_semn):02d}° {m:02d}'{s:02d}\" {nume_semn}"

def format_orba_aspect(orba_zecimala):
    val = abs(orba_zecimala)
    d = int(val)
    m = int((val - d) * 60)
    s = int(round((((val - d) * 60) - m) * 60))
    if s >= 60: m += 1; s = 0
    if m >= 60: d += 1; m = 0
    return f"{d}° {m:02d}' {s:02d}\""
    
# =====================================================================
# BLOCUL 3: LOGICA DE CALCUL EXPERTĂ (SWISS EPHEMERIS)
# =====================================================================
def calculeaza_evenimente_orizont(jd_miez, corp_id, geopos_lista):
    rezultate = {}
    evenimente = {"Rasarit": CALC_RISE, "Meridian": CALC_TRANSIT, "Apus": CALC_SET}
    for nume_ev, masca_rsmi in evenimente.items():
        status, date_tup = swe.rise_trans(jd_miez, corp_id, masca_rsmi, geopos_lista)
        rezultate[nume_ev] = date_tup[0] if status == 0 else None
    return rezultate

def calculeaza_date_timp_real(jd_ut, corp_id):
    date_ecl_tuplu, flag_ret = swe.calc_ut(jd_ut, corp_id, FLAG_FIIZIC)
    
    lon = date_ecl_tuplu[0]
    lat = date_ecl_tuplu[1]
    dist_raw = date_ecl_tuplu[2]
    
    dlon_cos = date_ecl_tuplu[3] * math.cos(math.radians(lat))
    dlat = date_ecl_tuplu[4]
    viteza_unghiulara_zi = math.sqrt(dlon_cos**2 + dlat**2)
    
    geopos = [float(LONGITUDINE), float(LATITUDINE), float(ALTITUDINE)]
    xin = [float(lon), float(lat), float(dist_raw)]
    
    az_sud, alt, alt_aparent = swe.azalt(jd_ut, 0, geopos, 1013.25, 15.0, xin)
    az_nord = (az_sud + 180.0) % 360.0
    
    distanta_km = dist_raw * UA_IN_KM
    omega = (viteza_unghiulara_zi * math.pi) / (180.0 * 86400.0)
    viteza_km_s = omega * distanta_km

    return {
        "lon_ecliptica": lon,
        "altitudine": alt_aparent,
        "azimut": az_nord,
        "distanta": distanta_km,
        "viteza": viteza_km_s
    }

def calculeaza_pozitie_astrologica(jd_ut, corp_id):
    flag_astrologic = swe.FLG_SWIEPH | swe.FLG_SPEED
    res_calc = swe.calc_ut(jd_ut, corp_id, flag_astrologic)
    
    date_ecl = res_calc[0]
    lon = date_ecl[0]
    viteza = date_ecl[3]
    
    miscare = "R" if viteza < 0 else "D"
    
    return {
        "pozitie_text": format_pozitie_astrologica(lon),
        "miscare": miscare,
        "lon_pura": lon
    }

def calculeaza_case_astrologice(jd_ut, sistem_caracter=b'P'):
    lat_rad = math.radians(float(LATITUDINE))
    lat_geocentrica = math.degrees(math.atan(0.993277 * math.tan(lat_rad)))
    
    cuspide, ascmc = swe.houses(jd_ut, lat_geocentrica, float(LONGITUDINE), sistem_caracter)
    
    ascendent = ascmc[0]
    mc = ascmc[1]
    descendent = (ascendent + 180.0) % 360.0
    ic = (mc + 180.0) % 360.0
    
    case_redenumite = {}
    etichete_case = {1: "AS", 4: "IC", 7: "DS", 10: "MC"}
    
    for i in range(1, 13):
        nume_afisat = etichete_case.get(i, f"Casa {i:02d}")
        
        if i == 1: lon_punct = ascendent
        elif i == 4: lon_punct = ic
        elif i == 7: lon_punct = descendent
        elif i == 10: lon_punct = mc
        else: lon_punct = cuspide[i - 1]
            
        case_redenumite[nume_afisat] = format_pozitie_astrologica(lon_punct)
        
    return case_redenumite

def determina_casa_planetei(lon_planeta, jd_ut):
    cuspide, _ = swe.houses(jd_ut, float(LATITUDINE), float(LONGITUDINE), b'P')
    
    for i in range(12):
        start_casa = cuspide[i]
        end_casa = cuspide[(i + 1) % 12]
        
        if start_casa < end_casa:
            if start_casa <= lon_planeta < end_casa:
                return i + 1
        else:
            if lon_planeta >= start_casa or lon_planeta < end_casa:
                return i + 1
    return 1

def calculeaza_dinamica_lunii(jd_ut):
    res_pheno = swe.pheno_ut(jd_ut, swe.MOON, swe.FLG_SWIEPH)
    procent_iluminare = res_pheno[1] * 100.0  
    
    res_soare = swe.calc_ut(jd_ut, swe.SUN, swe.FLG_SWIEPH)
    res_luna = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SWIEPH)
    
    lon_soare = res_soare[0][0]
    lon_luna = res_luna[0][0]
    
    elongatie = (lon_luna - lon_soare) % 360.0
    varsta_zile = (elongatie / 360.0) * 29.53059
    
    if 0.0 <= elongatie < 45.0:
        faza_text = "Luna Noua / Secera in crestere"
    elif 45.0 <= elongatie < 135.0:
        faza_text = "Primul Patrar"
    elif 135.0 <= elongatie < 225.0:
        faza_text = "Luna Plina"
    elif 225.0 <= elongatie < 315.0:
        faza_text = "Ultimul Patrar"
    else:
        faza_text = "Secera in descrestere / Luna Noua"
        
    return {
        "iluminare": procent_iluminare,
        "varsta": varsta_zile,
        "faza": faza_text,
        "elongatie": elongatie
    }

def gaseste_faza_dinamica(jd_baza, faza_tinta, cauta_in_trecut=False):
    t0 = jd_baza - 15.0 if cauta_in_trecut else jd_baza
    t1 = jd_baza if cauta_in_trecut else jd_baza + 15.0
    
    for _ in range(24):
        mijloc = (t0 + t1) / 2.0
        res_soare = swe.calc_ut(mijloc, swe.SUN, swe.FLG_SWIEPH)
        res_luna = swe.calc_ut(mijloc, swe.MOON, swe.FLG_SWIEPH)
        
        lon_soare = res_soare[0][0]
        lon_luna = res_luna[0][0]
        
        dif_lon = (lon_luna - lon_soare) % 360.0
        dif = dif_lon - faza_tinta
        
        if dif > 180.0: dif -= 360.0
        elif dif < -180.0: dif += 360.0
        
        if dif > 0:
            t1 = mijloc
        else:
            t0 = mijloc
            
    return (t0 + t1) / 2.0

def genereaza_ore_planetare(dt_rasarit, dt_apus):
    zi_saptamana = dt_rasarit.weekday()
    stapan_pornire = STAPAN_ZI[zi_saptamana]
    index_curent = ORDINE_CHALDEAN.index(stapan_pornire)
    
    durata_zi = dt_apus - dt_rasarit
    durata_noapte = timedelta(hours=24) - durata_zi
    
    lungime_ora_zi = durata_zi / 12
    lungime_ora_noapte = durata_noapte / 12
    
    ore_zi = []
    ore_noapte = []
    
    timp_cursor = dt_rasarit
    for i in range(12):
        planeta = ORDINE_CHALDEAN[index_curent]
        start_ora = timp_cursor
        timp_cursor += lungime_ora_zi
        ore_zi.append((i + 1, planeta, start_ora, timp_cursor))
        index_curent = (index_curent + 1) % 7
        
    for i in range(12):
        planeta = ORDINE_CHALDEAN[index_curent]
        start_ora = timp_cursor
        timp_cursor += lungime_ora_noapte
        ore_noapte.append((i + 1, planeta, start_ora, timp_cursor))
        index_curent = (index_curent + 1) % 7
        
    return ore_zi, ore_noapte

def gaseste_moment_cardinal(an, longitudine_tinta):
    zi_estimata = int((longitudine_tinta / 360.0) * 365.25) + 78
    jd_start = swe.julday(an, 1, 1, 0.0) + zi_estimata
    
    t0 = jd_start - 5.0
    t1 = jd_start + 5.0
    
    for _ in range(15):
        mijloc = (t0 + t1) / 2.0
        date_ecl_tuplu, flag_ret = swe.calc_ut(mijloc, swe.SUN, swe.FLG_SWIEPH)
        lon_act = date_ecl_tuplu[0]
        
        dif = lon_act - longitudine_tinta
        if dif > 180.0: dif -= 360.0
        elif dif < -180.0: dif += 360.0
        
        if dif > 0: t1 = mijloc
        else: t0 = mijloc
        
    return (t0 + t1) / 2.0

def calculeaza_anotimp_curent(lon_soare):
    if 0.0 <= lon_soare < 90.0:
        return "Primavara"
    elif 90.0 <= lon_soare < 180.0:
        return "Vara"
    elif 180.0 <= lon_soare < 270.0:
        return "Toamna"
    else:
        return "Iarna"

def determina_manzila_araba(lon_zecimala):
    dimensiune_manzila = 360.0 / 28.0
    numar_manzila = int(lon_zecimala / dimensiune_manzila) + 1
    if numar_manzila > 28: numar_manzila = 28
    
    grade_rest = lon_zecimala % dimensiune_manzila
    nume_arab, traducere = MANZILE_DATE.get(numar_manzila, ("Unknown", "Necunoscut"))
    
    return {
        "numar": numar_manzila,
        "nume_arab": nume_arab,
        "traducere": traducere,
        "progres_text": format_grade(grade_rest)
    }

def evalueaza_forta_planeta(nume_p, lon_p, casa_p, miscare_p, lon_soare):
    scor = 0
    justificari = []
    
    idx_semn = int(lon_p / 30.0) % 12
    semn_p = SEMNE_ZODIAC[idx_semn]
    
    if nume_p in DEMNITATI_MODERNE:
        dm = DEMNITATI_MODERNE[nume_p]
        if semn_p in dm["dom"]:
            scor += 5
            justificari.append(f"Domiciliu {semn_p} (+5)")
        elif semn_p in dm["exalt"]:
            scor += 4
            justificari.append(f"Exaltare {semn_p} (+4)")
        elif semn_p in dm["exil"]:
            scor -= 5
            justificari.append(f"Exil {semn_p} (-5)")
        elif semn_p in dm["cadere"]:
            scor -= 4
            justificari.append(f"Cadere {semn_p} (-4)")
        else:
            justificari.append("Pelerin (0)")

    if miscare_p == "D":
        scor += 2
        justificari.append("D (+2)")
    elif miscare_p == "R":
        scor -= 2
        justificari.append("R (-2)")

    if casa_p in [1, 4, 7, 10]:
        scor += 3
        justificari.append(f"Casa {casa_p:02d} Angulara (+3)")
    elif casa_p in [2, 5, 8, 11]:
        scor += 1
        justificari.append(f"Casa {casa_p:02d} Succedenta (+1)")
    else:
        scor -= 2
        justificari.append(f"Casa {casa_p:02d} Cadenta (-2)")

    if nume_p not in ["Soare", "Luna"]:
        dif_s = abs(lon_p - lon_soare)
        dist_soare = dif_s if dif_s <= 180.0 else 360.0 - dif_s
        if dist_soare < 8.5:
            scor -= 4
            justificari.append("COMBUST (-4)")

    eficienta = ((scor + 13) / 23.0) * 100.0
    
    return {"scor": scor, "eficienta": eficienta, "justificari": justificari}

def calculeaza_stea_fixa(jd_ut, nume_stea_se):
    flag_astrologic = swe.FLG_SWIEPH | swe.FLG_SPEED
    res_fixstar = swe.fixstar_ut(nume_stea_se, jd_ut, flag_astrologic)
    date_ecl_tuplu = res_fixstar[0]
    lon = date_ecl_tuplu[0]
    
    return {
        "pozitie_text": format_pozitie_astrologica(lon),
        "lon_pura": lon
    }

def calculeaza_toate_aspectele(toate_coordonatele, orba_maxima=6.0):
    aspecte_temporare = []
    nume_corpuri = list(toate_coordonatele.keys())
    total_corpuri = len(nume_corpuri)
    
    nume_stele_fixe = [
        "Algol", "Pleiades (Alcyone)", "Aldebaran", "Rigel", "Betelgeuse", 
        "Sirius", "Regulus", "Spica", "Arcturus", "Antares", "Vega", "Altair", "Fomalhaut"
    ]
    
    puncte_fictive_zgomot = [
        "NNM", "NSM", "NNT", "NST",
        "LM", "LT",
        "AI", "PI"
    ]    
    for i in range(total_corpuri):
        for j in range(i + 1, total_corpuri):
            c1 = nume_corpuri[i]
            c2 = nume_corpuri[j]
            
            if c1 in nume_stele_fixe and c2 in nume_stele_fixe:
                continue
            if c1 in puncte_fictive_zgomot and c2 in puncte_fictive_zgomot:
                continue
                
            lon1 = toate_coordonatele[c1]
            lon2 = toate_coordonatele[c2]
            
            dif = abs(lon1 - lon2)
            distanta = dif if dif <= 180.0 else 360.0 - dif
            
            for abrevier, unghi_perfect in ASPECTE_MAJORE.items():
                if (c1 in nume_stele_fixe or c2 in nume_stele_fixe) and abrevier not in ["CON", "OPO"]:
                    continue
                    
                deviatie_bruta = distanta - unghi_perfect
                orba_exacta = abs(deviatie_bruta)
                
                if orba_exacta <= orba_maxima:
                    semn = "+" if deviatie_bruta >= 0 else "-"
                    orba_text = format_orba_aspect(orba_exacta)
                    
                    text_formatat = f"{c1} {abrevier} {c2} ({semn}{orba_text})"
                    aspecte_temporare.append((orba_exacta, text_formatat))
                    break
                    
    aspecte_temporare.sort(key=lambda x: x[0])
    return [item[1] for item in aspecte_temporare]

def calculeaza_punct_arab(lon_asc, lon_corp1, lon_corp2, este_diurn=True, formula_diurna_fixa=True):
    if formula_diurna_fixa:
        if este_diurn:
            lon_punct = (lon_asc + lon_corp1 - lon_corp2) % 360.0
        else:
            lon_punct = (lon_asc + lon_corp2 - lon_corp1) % 360.0
    else:
        lon_punct = (lon_asc + lon_corp1 - lon_corp2) % 360.0
        
    return {
        "pozitie_text": format_pozitie_astrologica(lon_punct),
        "lon_pura": lon_punct
    }
    
# =====================================================================
# BLOCUL 9: EXECUTARE ȘI CALCULE (TOATE DATELE SUNT SALVATE ÎN VARIABILE)
# =====================================================================
acum_local, jd_acum, jd_miez = get_times()
geopos_lista = [LONGITUDINE, LATITUDINE, ALTITUDINE]

delta_t_zile = swe.deltat(jd_acum) / 86400.0
jd_et_planete = jd_acum + delta_t_zile
jd_ut_case = jd_acum

# Dicționar pentru a salva toate rezultatele
date_output = {}

corpuri = {"SOARE": swe.SUN, "LUNA": swe.MOON}
date_orizont_soare = {}
date_fizice = {}
lon_soare_acum = 0.0
manzila_luna_text = ""

for nume, corp_id in corpuri.items():
    ore_orizont = calculeaza_evenimente_orizont(jd_miez, corp_id, geopos_lista)
    date_output[f"{nume}_orizont"] = {}
    for nume_ev, jd_ev in ore_orizont.items():
        if jd_ev:
            dt_ev = jd_to_datetime(jd_ev)
            date_output[f"{nume}_orizont"][nume_ev] = dt_ev.strftime('%H:%M:%S')
            if corp_id == swe.SUN:
                date_orizont_soare[nume_ev] = dt_ev
        else:
            date_output[f"{nume}_orizont"][nume_ev] = "Date indisponibile"

    try:
        date_tr = calculeaza_date_timp_real(jd_acum, corp_id)
        date_output[f"{nume}_fizice"] = {
            "altitudine": format_grade(date_tr['altitudine']),
            "azimut": format_grade(date_tr['azimut']),
            "distanta": f"{date_tr['distanta']:,.2f} km",
            "viteza": f"{date_tr['viteza']:.4f} km/s"
        }
        if corp_id == swe.SUN:
            lon_soare_acum = date_tr["lon_ecliptica"]
    
        if corp_id == swe.MOON:
            res_luna_brut = swe.calc_ut(jd_et_planete, swe.MOON, swe.FLG_SWIEPH)
            lon_luna_brut = res_luna_brut[0][0]
            m_luna = determina_manzila_araba(lon_luna_brut)
            manzila_luna_text = f"Conac {m_luna['numar']:02d}/28 - {m_luna['nume_arab']} ({m_luna['traducere']}) | Poziție: {m_luna['progres_text']}"
            date_output["LUNA_manzila"] = manzila_luna_text
    except Exception as e:
        date_output[f"{nume}_fizice"] = {"eroare": str(e)}

# Dinamica Lunii
try:
    date_luna_dinamica = calculeaza_dinamica_lunii(jd_acum)
    res_soare = swe.calc_ut(jd_et_planete, swe.SUN, swe.FLG_SWIEPH)
    res_luna = swe.calc_ut(jd_et_planete, swe.MOON, swe.FLG_SWIEPH)
    elongatie_act = (res_luna[0][0] - res_soare[0][0]) % 360.0
    
    date_output["luna_dinamica"] = {
        "faza curenta": date_luna_dinamica['faza'],
        "iluminare": f"{date_luna_dinamica['iluminare']:.2f}%",
        "varsta": f"{date_luna_dinamica['varsta']:.2f} zile",
        "arc soli-lunar": format_grade(elongatie_act)
    }
    
    faze_ordine = [0.0, 90.0, 180.0, 270.0]
    nume_faze = {0.0: "Luna Noua", 90.0: "Primul Patrar", 180.0: "Luna Plina", 270.0: "Ultimul Patrar"}
    
    if 0.0 <= elongatie_act < 90.0:
        idx_trecut = 0
    elif 90.0 <= elongatie_act < 180.0:
        idx_trecut = 1
    elif 180.0 <= elongatie_act < 270.0:
        idx_trecut = 2
    else:
        idx_trecut = 3
        
    faza_t = faze_ordine[idx_trecut]
    jd_t = gaseste_faza_dinamica(jd_acum, faza_t, cauta_in_trecut=True)
    dt_t = jd_to_datetime(jd_t)
    
    date_output["faze_luna"] = [f" {nume_faze[faza_t]} : {dt_t.strftime('%d-%m-%Y %H:%M:%S')}"]
    
    jd_cursor = jd_t + 1.0  
    for k in range(1, 4):
        idx_v = (idx_trecut + k) % 4
        faza_v = faze_ordine[idx_v]
        jd_v = gaseste_faza_dinamica(jd_cursor, faza_v, cauta_in_trecut=False)
        dt_v = jd_to_datetime(jd_v)
        date_output["faze_luna"].append(f" {nume_faze[faza_v]} : {dt_v.strftime('%d-%m-%Y %H:%M:%S')}")
        jd_cursor = jd_v + 1.0
except Exception as e:
    date_output["luna_dinamica"] = {"eroare": str(e)}

# Durate și ore planetare - varianta CORECTĂ (cu răsăritul de mâine)
dt_r_azi = date_orizont_soare.get("Rasarit")
dt_a_azi = date_orizont_soare.get("Apus")

ore_zi, ore_noapte = [], []
guvernator_zi = ""
guvernator_ora = "Nedeterminat"
interval_ora_curenta = ""
durata_zi_ore = 0
durata_noapte_ore = 0
durata_totala_ore = 0

if dt_r_azi and dt_a_azi:
    # Calculează răsăritul de mâine
    # Avem nevoie de JD pentru ziua de mâine pentru a calcula răsăritul corect
    import pytz
    import swisseph as swe
    
    # Calculează JD pentru mâine la aceeași oră aproximativă
    maine = dt_r_azi + timedelta(days=1)
    maine_utc = maine.astimezone(pytz.utc)
    jd_main = swe.julday(maine_utc.year, maine_utc.month, maine_utc.day,
                         maine_utc.hour + maine_utc.minute / 60.0)
    
    # Calculează răsăritul de mâine
    geopos_lista = [LONGITUDINE, LATITUDINE, ALTITUDINE]
    rezultat_main = calculeaza_evenimente_orizont(jd_main - 0.5, swe.SUN, geopos_lista)
    dt_r_maine = None
    if rezultat_main.get("Rasarit"):
        dt_r_maine = jd_to_datetime(rezultat_main["Rasarit"])
    
    if dt_r_maine:
        # Durata reală a zilei (de la răsărit la răsărit)
        durata_totala_sec = (dt_r_maine - dt_r_azi).total_seconds()
        durata_totala_ore = durata_totala_sec / 3600.0
        
        # Durata luminii (ziua)
        durata_zi_sec = (dt_a_azi - dt_r_azi).total_seconds()
        durata_zi_ore = durata_zi_sec / 3600.0
        
        # Durata nopții (de la apus la răsăritul de mâine)
        durata_noapte_sec = (dt_r_maine - dt_a_azi).total_seconds()
        durata_noapte_ore = durata_noapte_sec / 3600.0
        
        # Acum generează orele planetare corecte
        lungime_ora_zi = timedelta(seconds=durata_zi_sec / 12)
        lungime_ora_noapte = timedelta(seconds=durata_noapte_sec / 12)
        
        # Generează orele de zi
        zi_saptamana = dt_r_azi.weekday()
        stapan_pornire = STAPAN_ZI[zi_saptamana]
        index_curent = ORDINE_CHALDEAN.index(stapan_pornire)
        
        timp_cursor = dt_r_azi
        for i in range(12):
            planeta = ORDINE_CHALDEAN[index_curent]
            start_ora = timp_cursor
            timp_cursor += lungime_ora_zi
            ore_zi.append((i + 1, planeta, start_ora, timp_cursor))
            index_curent = (index_curent + 1) % 7
        
        # Generează orele de noapte
        timp_cursor = dt_a_azi
        for i in range(12):
            planeta = ORDINE_CHALDEAN[index_curent]
            start_ora = timp_cursor
            timp_cursor += lungime_ora_noapte
            ore_noapte.append((i + 1, planeta, start_ora, timp_cursor))
            index_curent = (index_curent + 1) % 7
        
        # Guvernatorii
        guvernator_zi = STAPAN_ZI[dt_r_azi.weekday()]
        
        for numar, planeta, start, end in ore_zi:
            if start <= acum_local < end:
                guvernator_ora = planeta
                interval_ora_curenta = f"{start.strftime('%H:%M:%S')} - {end.strftime('%H:%M:%S')}"
                break
                
        if guvernator_ora == "Nedeterminat":
            for numar, planeta, start, end in ore_noapte:
                if start <= acum_local < end:
                    guvernator_ora = planeta
                    interval_ora_curenta = f"{start.strftime('%H:%M:%S')} - {end.strftime('%H:%M:%S')}"
                    break

date_output["durata_zi"] = format_durata(durata_zi_ore)
date_output["durata_noapte"] = format_durata(durata_noapte_ore)
date_output["durata_totala"] = format_durata(durata_totala_ore)
date_output["guvernator_zi"] = guvernator_zi.upper()
date_output["guvernator_ora"] = guvernator_ora.upper()
date_output["interval_ora"] = interval_ora_curenta

ore_zi_list = []
for numar, planeta, start, end in ore_zi:
    ore_zi_list.append(f"Ora {numar:02d} ({planeta:<7}) : {start.strftime('%H:%M:%S')} - {end.strftime('%H:%M:%S')}")
date_output["ore_zi"] = ore_zi_list

ore_noapte_list = []
for numar, planeta, start, end in ore_noapte:
    ore_noapte_list.append(f"Ora {numar:02d} ({planeta:<7}) : {start.strftime('%H:%M:%S')} - {end.strftime('%H:%M:%S')}")
date_output["ore_noapte"] = ore_noapte_list

# Anotimpuri
anotimp = calculeaza_anotimp_curent(lon_soare_acum)
date_output["anotimp"] = f"{anotimp} (Pozitie Soare: {format_grade(lon_soare_acum)})"

puncte_cardinale = {
    "Echinoctiu de primavara": 0.0,
    "Solstitiu de vara": 90.0,
    "Echinoctiu de toamna": 180.0,
    "Solstitiu de iarna": 270.0
}

date_output["puncte_cardinale"] = []
for nume_pct, unghi in puncte_cardinale.items():
    jd_pct = gaseste_moment_cardinal(acum_local.year, unghi)
    dt_pct = jd_to_datetime(jd_pct)
    date_output["puncte_cardinale"].append(f"{nume_pct} : {dt_pct.strftime('%d-%m-%Y %H:%M:%S')}")

# Case astrologice
try:
    tabel_case = calculeaza_case_astrologice(jd_acum, b'P')
    date_output["case_astrologice"] = tabel_case
except Exception as e:
    date_output["case_astrologice"] = {"eroare": str(e)}

# Poziții astrologice
coordonate_totale = {}

planete_standard = {
    "Soare": swe.SUN, "Luna": swe.MOON, "Mercur": swe.MERCURY, "Venus": swe.VENUS,
    "Marte": swe.MARS, "Jupiter": swe.JUPITER, "Saturn": swe.SATURN,
    "Uranus": swe.URANUS, "Neptun": swe.NEPTUNE, "Pluto": swe.PLUTO
}

date_output["planete"] = []
for nume, corp_id in planete_standard.items():
    try:
        p = calculeaza_pozitie_astrologica(jd_et_planete, corp_id)
        numar_casa = determina_casa_planetei(p['lon_pura'], jd_ut_case)
        date_output["planete"].append(f"{nume:<15} : {p['pozitie_text']:<25} | Casa: {numar_casa:02d} | ({p['miscare']})")
        coordonate_totale[nume] = p['lon_pura']
    except Exception as e:
        date_output["planete"].append(f"{nume:<15} : Eroare: {e}")

puncte_fictive = {
    "NNM": swe.MEAN_NODE,      # Nod Nord (Mean)
    "NNT": swe.TRUE_NODE,      # Nod Nord (True)
    "LM": swe.MEAN_APOG,       # Lilith (Mean)
    "LT": swe.OSCU_APOG,       # Lilith (True)
    "AI": 21,                  # Apogeu Interp.
    "PI": 22                   # Perigeu Interp.
}

date_output["puncte_fictive"] = []
for nume, corp_id in puncte_fictive.items():
    try:
        p = calculeaza_pozitie_astrologica(jd_et_planete, corp_id)
        numar_casa = determina_casa_planetei(p['lon_pura'], jd_ut_case)
        date_output["puncte_fictive"].append(f"{nume:<15} : {p['pozitie_text']:<25} | Casa: {numar_casa:02d} | ({p['miscare']})")
        coordonate_totale[nume] = p['lon_pura']
        
        # Pentru Nodurile Sud (calculate pe loc)
        if nume == "NNM":
            lon_sud = (p['lon_pura'] + 180.0) % 360.0
            numar_casa_sud = determina_casa_planetei(lon_sud, jd_ut_case)
            pozitie_sud = format_pozitie_astrologica(lon_sud)
            date_output["puncte_fictive"].append(f"NSM : {pozitie_sud:<25} | Casa: {numar_casa_sud:02d} | ({p['miscare']})")
            coordonate_totale["NSM"] = lon_sud
        elif nume == "NNT":
            lon_sud = (p['lon_pura'] + 180.0) % 360.0
            numar_casa_sud = determina_casa_planetei(lon_sud, jd_ut_case)
            pozitie_sud = format_pozitie_astrologica(lon_sud)
            date_output["puncte_fictive"].append(f"NST : {pozitie_sud:<25} | Casa: {numar_casa_sud:02d} | ({p['miscare']})")
            coordonate_totale["NST"] = lon_sud
    except Exception as e:
        date_output["puncte_fictive"].append(f"{nume:<15} : Eroare: {e}")

asteroizi = {
    "Ceres": swe.CERES, "Pallas": swe.PALLAS, "Juno": swe.JUNO,
    "Vesta": swe.VESTA, "Chiron": swe.CHIRON, "Pholus": 16
}

date_output["asteroizi"] = []
for nume, corp_id in asteroizi.items():
    try:
        p = calculeaza_pozitie_astrologica(jd_et_planete, corp_id)
        numar_casa = determina_casa_planetei(p['lon_pura'], jd_ut_case)
        date_output["asteroizi"].append(f"{nume:<15} : {p['pozitie_text']:<25} | Casa: {numar_casa:02d} | ({p['miscare']})")
        coordonate_totale[nume] = p['lon_pura']
    except Exception as e:
        date_output["asteroizi"].append(f"{nume:<15} : Eroare: {e}")

uraniene = {
    "Cupido": 40, "Hades": 41, "Zeus": 42, "Kronos": 43,
    "Apollon": 44, "Admetos": 45, "Vulkanus": 46, "Poseidon": 47, "Isis": 48
}

date_output["uraniene"] = []
for nume, corp_id in uraniene.items():
    try:
        p = calculeaza_pozitie_astrologica(jd_et_planete, corp_id)
        numar_casa = determina_casa_planetei(p['lon_pura'], jd_ut_case)
        date_output["uraniene"].append(f"{nume:<15} : {p['pozitie_text']:<25} | Casa: {numar_casa:02d} | ({p['miscare']})")
        coordonate_totale[nume] = p['lon_pura']
    except Exception as e:
        date_output["uraniene"].append(f"{nume:<15} : Eroare: {e}")

stele_fixe = {
    "Algol": "Algol", "Pleiades (Alcyone)": "Alcyone", "Aldebaran": "Aldebaran",
    "Rigel": "Rigel", "Betelgeuse": "Betelgeuse", "Sirius": "Sirius",
    "Regulus": "Regulus", "Spica": "Spica", "Arcturus": "Arcturus",
    "Antares": "Antares", "Vega": "Vega", "Altair": "Altair", "Fomalhaut": "Fomalhaut"
}

date_output["stele"] = []
for nume_afisat, nume_se in stele_fixe.items():
    try:
        s = calculeaza_stea_fixa(jd_et_planete, nume_se)
        numar_casa = determina_casa_planetei(s['lon_pura'], jd_ut_case)
        date_output["stele"].append(f"{nume_afisat:<19} : {s['pozitie_text']:<25} | Casa: {numar_casa:02d}")
        coordonate_totale[nume_afisat] = s['lon_pura']
    except Exception as e:
        date_output["stele"].append(f"{nume_afisat:<19} : Eroare: {e}")
        
# Scoruri planetare
scoruri_planete_json = {}
total_eficienta_colectata = 0.0
numar_planete_evaluate = 0
l_soare_eval = coordonate_totale.get("Soare", 0.0)

date_output["scoruri"] = []
for nume_p in ["Soare", "Luna", "Mercur", "Venus", "Marte", "Jupiter", "Saturn", "Uranus", "Neptun", "Pluto"]:
    if nume_p in coordonate_totale:
        lon_p = coordonate_totale[nume_p]
        casa_p = determina_casa_planetei(lon_p, jd_ut_case)
        p_stat = calculeaza_pozitie_astrologica(jd_et_planete, planete_standard[nume_p])
        res_eval = evalueaza_forta_planeta(nume_p, lon_p, casa_p, p_stat['miscare'], l_soare_eval)
        
        justificari_text = " | ".join(res_eval["justificari"])
        date_output["scoruri"].append(f"{nume_p:<10} : [{justificari_text}] -> Scor: {res_eval['scor']:+2} | Eficiență: {res_eval['eficienta']:.1f}%")
        
        total_eficienta_colectata += res_eval['eficienta']
        numar_planete_evaluate += 1
        
        scoruri_planete_json[nume_p] = {
            "scor_numeric": res_eval['scor'],
            "procent_eficienta": f"{res_eval['eficienta']:.1f}%",
            "justificari": res_eval["justificari"]
        }

scor_cosmic_global = total_eficienta_colectata / numar_planete_evaluate if numar_planete_evaluate > 0 else 0.0
date_output["scor_cosmic"] = scor_cosmic_global

# Aspecte
try:
    liste_aspecte = calculeaza_toate_aspectele(coordonate_totale, orba_maxima=6.0)
    date_output["aspecte"] = liste_aspecte if liste_aspecte else ["Nu s-au găsit aspecte unghiulare strânse sub 6°"]
except Exception as e:
    date_output["aspecte"] = [f"Eroare la generarea aspectelor: {e}"]

# Puncte arabe
try:
    case_brute, ascmc_brut = swe.houses(jd_ut_case, float(LATITUDINE), float(LONGITUDINE), b'P')
    l_asc = ascmc_brut[0]
    l_soare = coordonate_totale.get("Soare", 0.0)
    l_luna = coordonate_totale.get("Luna", 0.0)
    l_mercur = coordonate_totale.get("Mercur", 0.0)
    l_venus = coordonate_totale.get("Venus", 0.0)
    l_jupiter = coordonate_totale.get("Jupiter", 0.0)
    
    casa_soare = determina_casa_planetei(l_soare, jd_ut_case)
    este_harta_diurna = casa_soare >= 7
    
    date_output["tip_secta"] = f"Tipul Sectei (Harta): {'DIURNĂ (Zi)' if este_harta_diurna else 'NOCTURNĂ (Noapte)'}"
    
    puncte_arabe_list = []
    fortuna = calculeaza_punct_arab(l_asc, l_luna, l_soare, este_harta_diurna, formula_diurna_fixa=True)
    casa_fortuna = determina_casa_planetei(fortuna['lon_pura'], jd_ut_case)
    puncte_arabe_list.append(f"Pars Fortunae (Noroc)   : {fortuna['pozitie_text']:<25} | Casa: {casa_fortuna:02d}")
    
    spirit = calculeaza_punct_arab(l_asc, l_soare, l_luna, este_harta_diurna, formula_diurna_fixa=True)
    casa_spirit = determina_casa_planetei(spirit['lon_pura'], jd_ut_case)
    puncte_arabe_list.append(f"Pars Spiritus (Suflet)  : {spirit['pozitie_text']:<25} | Casa: {casa_spirit:02d}")
    
    eros = calculeaza_punct_arab(l_asc, l_venus, spirit['lon_pura'], este_harta_diurna, formula_diurna_fixa=True)
    casa_eros = determina_casa_planetei(eros['lon_pura'], jd_ut_case)
    puncte_arabe_list.append(f"Pars Amoris (Eros)      : {eros['pozitie_text']:<25} | Casa: {casa_eros:02d}")
    
    necesitate = calculeaza_punct_arab(l_asc, fortuna['lon_pura'], l_mercur, este_harta_diurna, formula_diurna_fixa=True)
    casa_necesitate = determina_casa_planetei(necesitate['lon_pura'], jd_ut_case)
    puncte_arabe_list.append(f"Pars Necessitatis       : {necesitate['pozitie_text']:<25} | Casa: {casa_necesitate:02d}")
    
    victorie = calculeaza_punct_arab(l_asc, l_jupiter, fortuna['lon_pura'], este_harta_diurna, formula_diurna_fixa=True)
    casa_victorie = determina_casa_planetei(victorie['lon_pura'], jd_ut_case)
    puncte_arabe_list.append(f"Pars Victoriae (Succes) : {victorie['pozitie_text']:<25} | Casa: {casa_victorie:02d}")
    
    date_output["puncte_arabe"] = puncte_arabe_list
except Exception as e:
    date_output["puncte_arabe"] = [f"Eroare la calculul Punctelor Arabe: {e}"]

# =====================================================================
# AFIȘAREA STREAMLIT - ORGANIZATĂ PE TAB-URI CU TABELE
# =====================================================================

# Header nou pe mai multe rânduri
# Dicționar pentru zile săptămână în engleză (abreviat)
ZILE_SAPTAMANA_EN = {
    0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"
}

def numar_zi_din_an(data):
    """Returnează numărul zilei din an (1-366)."""
    return data.timetuple().tm_yday

def numar_saptamana_din_an(data):
    """Returnează numărul săptămânii din an (1-53)."""
    return data.isocalendar()[1]

zi_nume = ZILE_SAPTAMANA_EN[acum_local.weekday()]
zi_din_an = numar_zi_din_an(acum_local)
saptamana_din_an = numar_saptamana_din_an(acum_local)
guv_ora = date_output.get('guvernator_ora', 'N/A')

st.title("Dashboard astro")
st.markdown(f"""
**{zi_nume} {acum_local.strftime('%d-%b-%Y %H:%M:%S')} {guv_ora}**  
*Ziua {zi_din_an} · Săptămâna {saptamana_din_an}*
""")
st.caption(f"Coordonate: {LATITUDINE}° N, {LONGITUDINE}° E")

# Creare tab-uri
tab1, tab2, tab3 = st.tabs(["Soare & Luna", "Astro", "Aspecte"])

# =====================================================================
# TAB 1 - SOARE & LUNĂ
# =====================================================================
with tab1:
    # Soarele - tabel cu popover pentru date fizice
    st.subheader("Soare")
    
    df_soare_ev = pd.DataFrame(
        list(date_output.get("SOARE_orizont", {}).items()),
        columns=["Eveniment", "Ora"]
    )
    st.dataframe(df_soare_ev, hide_index=True, use_container_width=False)
    
    with st.popover("Dinamica"):
        df_soare_fiz = pd.DataFrame(
            list(date_output.get("SOARE_fizice", {}).items()),
            columns=["Parametru", "Valoare"]
        )
        st.dataframe(df_soare_fiz, hide_index=True, use_container_width=False)
    
    st.divider()
    
    # Luna - tabel cu popover pentru date fizice și Manzil
    st.subheader("Luna")
    
    df_luna_ev = pd.DataFrame(
        list(date_output.get("LUNA_orizont", {}).items()),
        columns=["Eveniment", "Ora"]
    )
    st.dataframe(df_luna_ev, hide_index=True, use_container_width=False)
    
    with st.popover("Dinamica si Conac"):
        date_luna_fiz = {k: v for k, v in date_output.get("LUNA_fizice", {}).items() if k != "eroare"}
        df_luna_fiz = pd.DataFrame(
            list(date_luna_fiz.items()),
            columns=["Parametru", "Valoare"]
        )
        st.dataframe(df_luna_fiz, hide_index=True, use_container_width=False)
        
        # Manzila pe 3 rânduri
        if date_output.get("LUNA_manzila"):
            manzila_str = date_output["LUNA_manzila"]
            import re
            match_statie = re.search(r'Conac (\d+)/28 - ([^\(]+) \(([^\)]+)\)', manzila_str)
            match_pozitie = re.search(r'Poziție: ([^\|]+)', manzila_str)
            
            if match_statie:
                numar_statie = match_statie.group(1)
                nume_manzil = match_statie.group(2).strip()
                traducere = match_statie.group(3)
            else:
                numar_statie = "?"
                nume_manzil = "?"
                traducere = "?"
            
            pozitie = match_pozitie.group(1) if match_pozitie else "?"
            
            df_manzila = pd.DataFrame([
                ["Manzil", f"Stația {numar_statie} - {nume_manzil}"],
                ["Traducere", traducere],
                ["Poziție în manzil", pozitie]
            ], columns=["", "Detalii"])
            st.dataframe(df_manzila, hide_index=True, use_container_width=False)
    
    st.divider()
    
    # Fazele Lunii - tabele unite, coloană Valoare mai largă
    st.subheader("Fazele Lunii")
    
    if "luna_dinamica" in date_output and "eroare" not in date_output["luna_dinamica"]:
        ld = date_output["luna_dinamica"]
        df_luna_din = pd.DataFrame(
            list(ld.items()),
            columns=["Parametru", "Valoare"]
        )
        st.dataframe(df_luna_din, hide_index=True, use_container_width=False, column_config={
            "Valoare": st.column_config.TextColumn("Valoare", width="medium")
        })
        
        # Fazele principale
        df_faze = pd.DataFrame(
            [faza.split(" : ") for faza in date_output.get("faze_luna", [])],
            columns=["Faza", "Data și ora"]
        )
        st.dataframe(df_faze, hide_index=True, use_container_width=False)

st.subheader("Vizualizări")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Faza Lunii în timp real**")
    
    iluminare_procent = 10.0  # Valoare din exemplul tău
    if "luna_dinamica" in date_output and "eroare" not in date_output["luna_dinamica"]:
        iluminare_str = date_output["luna_dinamica"].get("iluminare", "0%")
        iluminare_procent = float(iluminare_str.replace("%", "").strip())
    
    faza = date_output["luna_dinamica"].get("faza curenta", "").lower()
    is_waning = "waning" in faza or "descrescatoare" in faza or "ultimul" in faza

    fig_luna, ax_luna = plt.subplots(figsize=(3, 3), facecolor='white')
    ax_luna.set_xlim(-1.05, 1.05)
    ax_luna.set_ylim(-1.05, 1.05)
    ax_luna.set_aspect('equal')
    ax_luna.axis('off')

    # Culori
    c_lumina = '#fefeec'
    c_umbra = '#2c2c2c'

    # Metoda trigonometrică infailibilă pentru fazele lunii:
    # Desenăm o jumătate albă și una neagră, apoi o elipsă la mijloc care își schimbă culoarea
    if not is_waning:  # Luna Crește (Lumina e în dreapta)
        stanga_color = c_umbra
        dreapta_color = c_lumina
        elipsa_color = c_umbra if iluminare_procent < 50 else c_lumina
    else:  # Luna Descrește (Lumina e în stânga)
        stanga_color = c_lumina
        dreapta_color = c_umbra
        elipsa_color = c_lumina if iluminare_procent < 50 else c_umbra

    # Desenăm cele două jumătăți de bază (Wedges)
    baza_stanga = Wedge((0, 0), 1, 90, 270, color=stanga_color, zorder=1)
    baza_dreapta = Wedge((0, 0), 1, -90, 90, color=dreapta_color, zorder=1)
    ax_luna.add_patch(baza_stanga)
    ax_luna.add_patch(baza_dreapta)

    # Calculăm lățimea elipsei centrale (linia de demarcație a umbrei)
    # Proporția variază de la 1.0 (lună plină/nouă) la 0.0 (sferturi)
    latime_elipsa = abs(2.0 * (iluminare_procent / 100.0) - 1.0)

    if latime_elipsa > 0:
        elipsa_tranzitie = Ellipse((0, 0), latime_elipsa * 2, 2, color=elipsa_color, zorder=2)
        ax_luna.add_patch(elipsa_tranzitie)

    # Bordură exterioară perfectă
    bordura = plt.Circle((0, 0), 1, color='black', fill=False, linewidth=1.5, zorder=3)
    ax_luna.add_patch(bordura)

    st.pyplot(fig_luna)
    st.caption(f"Iluminare: {iluminare_procent:.1f}% | {faza.capitalize()}")

with col2:
    st.markdown("**Durata Zilei vs Nopții**")
    
    durata_zi = date_output.get('durata_zi', '14 h 00 m 00 s')
    durata_noapte = date_output.get('durata_noapte', '10 h 00 m 00 s')
    
    def extrage_ore_totale(durata_str):
        match = re.search(r'(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?', durata_str)
        if match:
            h = float(match.group(1)) if match.group(1) else 0.0
            m = float(match.group(2)) if match.group(2) else 0.0
            return h + (m / 60.0)
        return 12.0

    ore_zi = extrage_ore_totale(durata_zi)
    ore_noapte = extrage_ore_totale(durata_noapte)
    total = ore_zi + ore_noapte
    procent_zi = (ore_zi / total) * 100 if total > 0 else 50.0

    fig_zn, ax_zn = plt.subplots(figsize=(3, 3), facecolor='white')
    ax_zn.set_xlim(-1.05, 1.05)
    ax_zn.set_ylim(-1.05, 1.05)
    ax_zn.set_aspect('equal')
    ax_zn.axis('off')

    # ALINIERE ORA 8 (240°) și ORA 4 (120°)
    # În Matplotlib: Ora 3 = 0°, Ora 12 = 90°, Ora 9 = 180°, Ora 6 = 270°
    # Ora 4 geometric este la -30° (sau 330°), Ora 8 este la 210°
    # Centrul arcului de zi (Sus) este fixat la 90° (Ora 12)
    
    unghi_zi_total = (procent_zi / 100.0) * 360.0
    
    # Ziua se va extinde simetric în stânga și dreapta axei de sus (90°)
    unghi_start = 90.0 - (unghi_zi_total / 2.0)
    unghi_end = 90.0 + (unghi_zi_total / 2.0)

    # Felia pentru ZI (Galben - Sus)
    if unghi_zi_total > 0:
        zi = Wedge((0, 0), 1, unghi_start, unghi_end, color='#FFD700', edgecolor='black', linewidth=0.5, zorder=1)
        ax_zn.add_patch(zi)
    
    # Felia pentru NOAPTE (Albastru închis - Jos)
    if (360.0 - unghi_zi_total) > 0:
        noapte = Wedge((0, 0), 1, unghi_end, unghi_start + 360.0, color='#1a1a2e', edgecolor='black', linewidth=0.5, zorder=1)
        ax_zn.add_patch(noapte)

    # Bordură exterioară neagră
    bordura_zn = plt.Circle((0, 0), 1, color='black', fill=False, linewidth=1.5, zorder=3)
    ax_zn.add_patch(bordura_zn)

    st.pyplot(fig_zn)
    st.caption(f"Zi: {durata_zi}  |  Noapte: {durata_noapte}")
    
    st.divider()
    
    # Durate și guvernatori
    st.subheader("Durate calendaristice")
    
    df_durate = pd.DataFrame([
        ["Durata zilei", date_output.get('durata_zi', 'N/A')],
        ["Durata nopții", date_output.get('durata_noapte', 'N/A')],
        ["Guvernatorul zilei", date_output.get('guvernator_zi', 'N/A')],
        ["Guvernatorul orei", f"{date_output.get('guvernator_ora', 'N/A')} ({date_output.get('interval_ora', 'N/A')})"]
    ], columns=["Parametru", "Valoare"])
    st.dataframe(df_durate, hide_index=True, use_container_width=False)
    
    # Ore planetare cu expander
    with st.expander("Ore de zi"):
        df_ore_zi = pd.DataFrame(
            [ora.split(" : ") for ora in date_output.get("ore_zi", [])],
            columns=["Ora planetară", "Interval"]
        )
        st.dataframe(df_ore_zi, hide_index=True, use_container_width=False)
    
    with st.expander("Ore de noapte"):
        df_ore_noapte = pd.DataFrame(
            [ora.split(" : ") for ora in date_output.get("ore_noapte", [])],
            columns=["Ora planetară", "Interval"]
        )
        st.dataframe(df_ore_noapte, hide_index=True, use_container_width=False)
    
    # Anotimpuri cu expander
    with st.expander("Anotimpuri"):
        st.markdown(f"**Anotimpul curent:** {date_output.get('anotimp', 'N/A')}")
        df_cardinale = pd.DataFrame(
            [pct.split(" : ") for pct in date_output.get("puncte_cardinale", [])],
            columns=["Eveniment", "Data și ora"]
        )
        st.dataframe(df_cardinale, hide_index=True, use_container_width=False)

# =====================================================================
# TAB 2 - ASTRO
# =====================================================================
with tab2:
    # Case astrologice - expander închis implicit, tabel în 3 coloane
    st.subheader("Case")
    with st.expander("Afișează casele", expanded=False):
        if "case_astrologice" in date_output and "eroare" not in date_output["case_astrologice"]:
            # Transformă dicționarul în listă de rânduri cu 3 coloane
            case_date = []
            for casa, pozitie in date_output["case_astrologice"].items():
                # Poziția vine în format "19° 15'09\" Berbec"
                # Separă grade/minute/secunde de zodie
                import re
                match = re.match(r'(\d+°\s+\d+\'\d+")\s+([A-Za-z]+)', pozitie)
                if match:
                    grade = match.group(1)
                    zodie = match.group(2)
                else:
                    grade = pozitie
                    zodie = ""
                case_date.append([casa, grade, zodie])
            
            df_case = pd.DataFrame(case_date, columns=["Casa", "Poziție", "Zodie"])
            st.dataframe(df_case, hide_index=True, use_container_width=False)
    
    st.divider()
        
    # Poziții planete standard
        # Poziții astrologice - sparte în 5 coloane
    st.subheader("Pozitii")
    
    # Funcție ajutătoare pentru a extrage cele 5 coloane
    def parse_pozitie(linie):
        """
        Linie exemplu: "Soare          : 19° 15'09\" Berbec | Casa: 07 | (D)"
        """
        if not linie or "Eroare" in linie:
            return ["", "", "", "", ""]
        
        # Separă numele de rest
        if " : " in linie:
            nume, rest = linie.split(" : ", 1)
        else:
            nume = linie.split()[0] if linie else ""
            rest = linie
        
        # Extrage poziția, zodiacul, casa și mișcarea
        import re
        # Pattern: grade° mm'ss" Zodie | Casa: nn | (D/R)
        match = re.match(r'(\d+°\s+\d+\'\d+")\s+([A-Za-z]+)\s+\|\s+Casa:\s+(\d+)\s+\|\s+\(([DR])\)', rest)
        if match:
            pozitie = match.group(1)
            zodie = match.group(2)
            casa = match.group(3)
            miscare = match.group(4)
        else:
            pozitie = rest[:25] if len(rest) > 25 else rest
            zodie = ""
            casa = ""
            miscare = ""
        
        return [nume.strip(), pozitie, zodie, casa, miscare]
    
    # Planete standard
    st.markdown("**Planete standard**")
    planete_date = []
    for p in date_output.get("planete", []):
        planete_date.append(parse_pozitie(p))
    df_planete = pd.DataFrame(planete_date, columns=["Nume", "Poziție", "Zodie", "Casa", "D/R"])
    st.dataframe(df_planete, hide_index=True, use_container_width=False)
    
    # Noduri și puncte fictive
    # Noduri și puncte fictive - inclusiv Nodurile Sud
    with st.expander("Noduri & Lilith"):
        fictive_date = []
        for p in date_output.get("puncte_fictive", []):
            # Verifică dacă linia conține "Nod Sud" (deja are format diferit)
            if "Nod Sud" in p:
                # Linie exemplu: "Nod Sud (Mean) : 04° 52'55" Vir | Casa: 04"
                if " : " in p:
                    nume, rest = p.split(" : ", 1)
                    import re
                    match = re.match(r'(\d+°\s+\d+\'\d+")\s+([A-Za-z]+)\s+\|\s+Casa:\s+(\d+)', rest)
                    if match:
                        pozitie = match.group(1)
                        zodie = match.group(2)
                        casa = match.group(3)
                        fictive_date.append([nume.strip(), pozitie, zodie, casa, "R"])
                    else:
                        fictive_date.append([p[:25], "", "", "", ""])
                else:
                    fictive_date.append([p[:25], "", "", "", ""])
            else:
                # Parsează normal pentru celelalte puncte
                fictive_date.append(parse_pozitie(p))
        df_fictive = pd.DataFrame(fictive_date, columns=["Nume", "Poziție", "Zodie", "Casa", "D/R"])
        st.dataframe(df_fictive, hide_index=True, use_container_width=False)
            
    # Asteroizi
    with st.expander("Asteroizi"):
        asteroizi_date = []
        for a in date_output.get("asteroizi", []):
            asteroizi_date.append(parse_pozitie(a))
        df_asteroizi = pd.DataFrame(asteroizi_date, columns=["Nume", "Poziție", "Zodie", "Casa", "D/R"])
        st.dataframe(df_asteroizi, hide_index=True, use_container_width=False)
    
    # Planete uraniene
    with st.expander("Planete uraniene"):
        uraniene_date = []
        for u in date_output.get("uraniene", []):
            uraniene_date.append(parse_pozitie(u))
        df_uraniene = pd.DataFrame(uraniene_date, columns=["Nume", "Poziție", "Zodie", "Casa", "D/R"])
        st.dataframe(df_uraniene, hide_index=True, use_container_width=False)
    
    # Stele fixe (nu au D/R, doar poziție și casă)
    # Stele fixe - fără coloana D/R (4 coloane)
    with st.expander("Stele fixe"):
        stele_date = []
        for s in date_output.get("stele", []):
            if " : " in s:
                nume, rest = s.split(" : ", 1)
                import re
                match = re.match(r'(\d+°\s+\d+\'\d+")\s+([A-Za-z]+)\s+\|\s+Casa:\s+(\d+)', rest)
                if match:
                    pozitie = match.group(1)
                    zodie = match.group(2)
                    casa = match.group(3)
                else:
                    pozitie = rest[:25]
                    zodie = ""
                    casa = ""
                stele_date.append([nume.strip(), pozitie, zodie, casa])
            else:
                stele_date.append([s[:20], "", "", ""])
        df_stele = pd.DataFrame(stele_date, columns=["Nume", "Poziție", "Zodie", "Casa"])
        st.dataframe(df_stele, hide_index=True, use_container_width=False)
            
    st.divider()
    
    # Scoruri planetare - sparte în 7 coloane
    st.subheader("Scor planetar")
    
    def parse_scor(linie):
        """
        Linie exemplu: "Soare      : [Domiciliu Leo (+5) | D (+2) | Casa 01 Angulara (+3)] -> Scor: +10 | Eficiență: 100.0%"
        """
        if not linie:
            return ["", "", "", "", "", "", ""]
        
        # Separă planeta de rest
        if " : [" in linie:
            planeta, rest = linie.split(" : [", 1)
            planeta = planeta.strip()
        else:
            planeta = linie.split()[0] if linie else ""
            rest = linie
        
        # Separă partea de justificări de scor
        if "] -> Scor: " in rest:
            just_part, scor_part = rest.split("] -> Scor: ", 1)
        else:
            just_part = rest
            scor_part = ""
        
        # Extrage eficiența
        eficienta = ""
        if " | Eficiență: " in scor_part:
            scor_val, eficienta = scor_part.split(" | Eficiență: ")
        else:
            scor_val = scor_part
        
        # Parsează justificările
        demnitate = ""
        dr = ""
        tip_casa = ""
        combust = ""
        
        parts = just_part.split(" | ")
        for part in parts:
            part = part.strip()
            if any(word in part for word in ["Domiciliu", "Exaltare", "Exil", "Cadere", "Esențial", "Pelerin"]):
                demnitate = part
            elif "D (+2)" in part or "R (-2)" in part:
                dr = part
            elif "Angulara" in part or "Succedenta" in part or "Cadenta" in part:
                tip_casa = part
            elif "COMBUST" in part:
                combust = part
        
        # Dacă nu s-a găsit nicio demnitate, dar există "Pelerin" în just_part
        if not demnitate and "Pelerin" in just_part:
            demnitate = "Pelerin (0)"
        
        # Dacă nu s-au găsit, încearcă pattern-uri mai simple
        if not dr:
            if "D (+2)" in just_part:
                dr = "D (+2)"
            elif "R (-2)" in just_part:
                dr = "R (-2)"
        
        return [planeta, demnitate, dr, tip_casa, combust, scor_val.strip(), eficienta.replace("%", "") + "%" if eficienta else ""]
    
    scoruri_date = []
    for scor in date_output.get("scoruri", []):
        scoruri_date.append(parse_scor(scor))
    
    if scoruri_date:
        df_scoruri = pd.DataFrame(scoruri_date, columns=["Planeta", "Demnitate", "D/R", "Casa", "Combust", "Scor", "Eficiență"])
        st.dataframe(df_scoruri, hide_index=True, use_container_width=False)
    
    st.divider()
        
    # Scor cosmic
    st.subheader("Scor global")
    scor = date_output.get("scor_cosmic", 0)
    st.progress(int(scor))
    st.metric("Indice de eficiență planetară totală", f"{scor:.1f}%")

# =====================================================================
# TAB 3 - ASPECTE & FILOSOFIC
# =====================================================================
with tab3:
    # Aspecte - cu slider pentru orbă
    st.subheader("Aspecte active")
    
    # Slider pentru selectarea orbei maxime
    orba_maxima = st.slider(
        "Orbă maximă (grade)",
        min_value=0.0,
        max_value=10.0,
        value=6.0,
        step=0.5,
        help="Selectează toleranța maximă pentru aspecte (0° - 10°)"
    )
    
    # Recalculează aspectele cu noua orbă
    try:
        liste_aspecte_filtrate = calculeaza_toate_aspectele(coordonate_totale, orba_maxima=orba_maxima)
        aspecte_filtrate = liste_aspecte_filtrate if liste_aspecte_filtrate else ["Nu s-au găsit aspecte sub " + str(orba_maxima) + "°"]
    except Exception as e:
        aspecte_filtrate = [f"Eroare: {e}"]
    
    def parse_aspect(linie):
        if not linie:
            return ["", "", "", ""]
        
        import re
        match = re.match(r'^(.+?)\s+(CON|SEX|CAR|TRI|OPO)\s+(.+?)\s+\(([^)]+)\)', linie)
        if match:
            planeta1 = match.group(1).strip()
            tip_aspect = match.group(2)
            planeta2 = match.group(3).strip()
            orba = match.group(4).strip()
            return [planeta1, tip_aspect, planeta2, orba]
        
        return [linie[:30], "", "", ""]
    
    aspecte_date = []
    for a in aspecte_filtrate:
        aspecte_date.append(parse_aspect(a))
    
    df_aspecte = pd.DataFrame(aspecte_date, columns=["Planeta 1", "Aspect", "Planeta 2", "Orbă"])
    st.dataframe(df_aspecte, hide_index=True, use_container_width=False)
    
    st.divider()
    
    # Puncte arabe - sparte în 4 coloane
    st.subheader("Puncte arabe majore")
    
    st.text(date_output.get("tip_secta", ""))
    
    def parse_punct_arab(linie):
        if not linie or "Eroare" in linie:
            return ["", "", "", ""]
        
        if " : " in linie:
            nume, rest = linie.split(" : ", 1)
        else:
            nume = linie[:30]
            rest = linie
        
        import re
        match = re.match(r'(\d+°\s+\d+\'\d+")\s+([A-Za-z]+)\s+\|\s+Casa:\s+(\d+)', rest)
        if match:
            pozitie = match.group(1)
            zodie = match.group(2)
            casa = match.group(3)
            return [nume.strip(), pozitie, zodie, casa]
        else:
            return [nume.strip(), rest[:30], "", ""]
    
    puncte_date = []
    for pa in date_output.get("puncte_arabe", []):
        puncte_date.append(parse_punct_arab(pa))
    
    df_pa = pd.DataFrame(puncte_date, columns=["Punct arab", "Poziție", "Zodie", "Casa"])
    st.dataframe(df_pa, hide_index=True, use_container_width=False)

# Închidere
swe.close()