import streamlit as st
import os
import math
import json
from datetime import datetime, timedelta
import pytz
import swisseph as swe
import pandas as pd
from io import StringIO

# =====================================================================
# CONFIGURARE PAGINĂ STREAMLIT
# =====================================================================
st.set_page_config(
    page_title="AstroCalcul Pro - Dashboard Astronomic",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# BLOCUL 1: CONFIGURARE, COORDONATE FIXE ȘI CĂI
# =====================================================================
LATITUDINE = 44.42
LONGITUDINE = 26.12
ALTITUDINE = 80.0  # metri

# Configurare căi efemeride (necesită ajustare pentru Streamlit Cloud)
@st.cache_resource
def init_swiss_ephem():
    """Inițializează Swiss Ephemeris cu calea corectă."""
    cale_curenta = os.path.dirname(os.path.abspath(__file__))
    cale_efemeride = os.path.join(cale_curenta, "ephe")
    
    # Pentru Streamlit Cloud, poți avea nevoie de o cale diferită
    if not os.path.exists(cale_efemeride):
        # Încearcă calea relativă
        cale_efemeride = "ephe"
    
    swe.set_ephe_path(cale_efemeride)
    swe.set_topo(LONGITUDINE, LATITUDINE, ALTITUDINE)
    return True

# Inițializare
init_swiss_ephem()

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
    "Soare":   {"dom": ["Leu"],             "exalt": ["Berbec"],    "exil": ["Varsator"],          "cadere": ["Balanta"]},
    "Luna":    {"dom": ["Rac"],             "exalt": ["Taur"],      "exil": ["Capricorn"],         "cadere": ["Scorpion"]},
    "Mercur":  {"dom": ["Gemeni", "Fecioara"], "exalt": ["Fecioara"], "exil": ["Sagetator", "Pesti"], "cadere": ["Pesti"]},
    "Venus":   {"dom": ["Taur", "Balanta"], "exalt": ["Pesti"],     "exil": ["Scorpion", "Berbec"], "cadere": ["Fecioara"]},
    "Marte":   {"dom": ["Berbec", "Scorpion"], "exalt": ["Capricorn"], "exil": ["Balanta", "Taur"],    "cadere": ["Rac"]},
    "Jupiter": {"dom": ["Sagetator", "Pesti"], "exalt": ["Rac"],       "exil": ["Gemeni", "Fecioara"], "cadere": ["Capricorn"]},
    "Saturn":  {"dom": ["Capricorn", "Varsator"], "exalt": ["Balanta"], "exil": ["Rac", "Leu"],         "cadere": ["Berbec"]},
    "Uranus":  {"dom": ["Varsator"],         "exalt": ["Scorpion"],  "exil": ["Leu"],               "cadere": ["Taur"]},
    "Neptun":  {"dom": ["Pesti"],            "exalt": ["Rac"],       "exil": ["Fecioara"],          "cadere": ["Capricorn"]},
    "Pluto":   {"dom": ["Scorpion"],         "exalt": ["Berbec"],    "exil": ["Taur"],              "cadere": ["Balanta"]}
}

SEMNE_ZODIAC = [
    "Berbec", "Taur", "Gemeni", "Rac", "Leu", "Fecioara",
    "Balanta", "Scorpion", "Sagetator", "Capricorn", "Varsator", "Pesti"
]

MANZILE_DATE = {
    1: ("Al-Sharatain", "Cele doua semne"), 2: ("Al-Butain", "Micul pantece"), 
    3: ("Al-Thurayya", "Pleiadele / Abundenta"), 4: ("Al-Dabaran", "Urmaritorul / Aldebaran"),
    5: ("Al-Haq'ah", "Cercul de par / Corona"), 6: ("Al-Han'ah", "Semnul de foc / Arc"),
    7: ("Al-Dhira", "Bratul leului / Gemeni"), 8: ("Al-Nathrah", "Zborul / Cuibul"),
    9: ("Al-Tarf", "Privirea / Ochii Leului"), 10: ("Al-Jabhah", "Fruntea Leului / Regulus"),
    11: ("Al-Zubrah", "Coama Leului"), 12: ("Al-Sarfah", "Schimbatorul de vreme"),
    13: ("Al-Awwa", "Cainele latrator"), 14: ("Al-Simak", "Cel Neinarmat / Spica"),
    15: ("Al-Ghafr", "Acoperamantul"), 16: ("Al-Zubana", "Clestii Scorpionului"),
    17: ("Al-Iklil", "Coroana"), 18: ("Al-Qalb", "Inima / Antares"),
    19: ("Al-Shaulah", "Acul Scorpionului"), 20: ("Al-Na'aim", "Strutii"),
    21: ("Al-Baldah", "Orasul / Spatiul gol"), 22: ("Al-Sa'd al-Dhabih", "Norocul Macelarului"),
    23: ("Al-Sa'd al-Bula", "Norocul Inghititorului"), 24: ("Al-Sa'd al-Su'ud", "Norocul Norocurilor"),
    25: ("Al-Sa'd al-Ahbiyah", "Norocul Corturilor"), 26: ("Al-Fargh al-Muqaddam", "Gura de sus a putului"),
    27: ("Al-Fargh al-Mu'ahhar", "Gura de jos a putului"), 28: ("Risha / Batn al-Hut", "Pantecele Pestelui")
}

ASPECTE_MAJORE = {
    "CON": 0.0,
    "SEX": 60.0,
    "CAR": 90.0,
    "TRI": 120.0,
    "OPO": 180.0
}

# =====================================================================
# FUNCȚII UTILITARE
# =====================================================================
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
    return f"{h:02d} ore, {m:02d} minute, {s:02d} secunde"

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

@st.cache_data(ttl=60)
def get_times():
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

# =====================================================================
# FUNCȚII DE CALCUL (păstrate identice cu originalul)
# =====================================================================
def calculeaza_evenimente_orizont(jd_miez, corp_id, geopos_lista):
    rezultate = {}
    evenimente = {"Rasarit": CALC_RISE, "Tranzit (Meridian)": CALC_TRANSIT, "Apus": CALC_SET}
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
    
    miscare = "Retrograd" if viteza < 0 else "Direct"
    
    return {
        "pozitie_text": format_pozitie_astrologica(lon),
        "miscare": miscare,
        "lon_pura": lon
    }

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
        faza_text = "🌑 Luna Noua / Secera in crestere"
    elif 45.0 <= elongatie < 135.0:
        faza_text = "🌓 Primul Patrar"
    elif 135.0 <= elongatie < 225.0:
        faza_text = "🌕 Luna Plina"
    elif 225.0 <= elongatie < 315.0:
        faza_text = "🌗 Ultimul Patrar"
    else:
        faza_text = "🌘 Secera in descrestere / Luna Noua"
        
    return {
        "iluminare": procent_iluminare,
        "varsta": varsta_zile,
        "faza": faza_text,
        "elongatie": elongatie
    }

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

def calculeaza_anotimp_curent(lon_soare):
    if 0.0 <= lon_soare < 90.0:
        return "🌸 Primavara"
    elif 90.0 <= lon_soare < 180.0:
        return "☀️ Vara"
    elif 180.0 <= lon_soare < 270.0:
        return "🍂 Toamna"
    else:
        return "❄️ Iarna"

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
            justificari.append("Esențial: Standard (0)")

    if miscare_p == "Direct":
        scor += 2
        justificari.append("Direct (+2)")
    elif miscare_p == "Retrograd":
        scor -= 2
        justificari.append("Retrograd (-2)")

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
        "Nod Nord (Mean)", "Nod Sud (Mean)", "Nod Nord (True)", "Nod Sud (True)",
        "Lilith (Mean)  ", "Lilith (True)  ", "Lilith (Mean)", "Lilith (True)",
        "Apogeu Interp. ", "Perigeu Interp.", "Apogeu Interp.", "Perigeu Interp."
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
                    
                    text_formatat = f"• {c1} {abrevier} {c2} ({semn}{orba_text})"
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
# FUNCȚIA PRINCIPALĂ DE CALCUL STREAMLIT
# =====================================================================
@st.cache_data(ttl=60)
def calculeaza_toate_datele():
    """Rulează toate calculele și returnează un dicționar cu rezultatele."""
    
    acum_local, jd_acum, jd_miez = get_times()
    geopos_lista = [LONGITUDINE, LATITUDINE, ALTITUDINE]
    
    delta_t_zile = swe.deltat(jd_acum) / 86400.0
    jd_et_planete = jd_acum + delta_t_zile
    jd_ut_case = jd_acum
    
    # Evenimente Soare
    corpuri = {"SOARE": swe.SUN, "LUNA": swe.MOON}
    date_orizont_soare = {}
    lon_soare_acum = 0.0
    
    for nume, corp_id in corpuri.items():
        ore_orizont = calculeaza_evenimente_orizont(jd_miez, corp_id, geopos_lista)
        if corp_id == swe.SUN:
            for nume_ev, jd_ev in ore_orizont.items():
                if jd_ev:
                    date_orizont_soare[nume_ev] = jd_to_datetime(jd_ev)
        
        if corp_id == swe.SUN:
            date_tr = calculeaza_date_timp_real(jd_acum, corp_id)
            lon_soare_acum = date_tr["lon_ecliptica"]
    
    # Dinamica Lunii
    date_luna_dinamica = calculeaza_dinamica_lunii(jd_acum)
    
    # Ore planetare
    dt_r = date_orizont_soare.get("Rasarit")
    dt_a = date_orizont_soare.get("Apus")
    
    ore_zi, ore_noapte = [], []
    guvernator_zi = ""
    guvernator_ora = "Nedeterminat"
    interval_ora_curenta = ""
    durata_zi_ore = 0
    
    if dt_r and dt_a:
        durata_zi_ore = (dt_a - dt_r).total_seconds() / 3600.0
        ore_zi, ore_noapte = genereaza_ore_planetare(dt_r, dt_a)
        
        guvernator_zi = STAPAN_ZI[dt_r.weekday()]
        
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
    
    # Case astrologice
    tabel_case = calculeaza_case_astrologice(jd_acum, b'P')
    
    # Colectare coordonate totale pentru aspecte
    coordonate_totale = {}
    
    # Planete standard
    planete_standard = {
        "Soare": swe.SUN, "Luna": swe.MOON, "Mercur": swe.MERCURY, "Venus": swe.VENUS,
        "Marte": swe.MARS, "Jupiter": swe.JUPITER, "Saturn": swe.SATURN,
        "Uranus": swe.URANUS, "Neptun": swe.NEPTUNE, "Pluto": swe.PLUTO
    }
    
    planete_date = []
    for nume, corp_id in planete_standard.items():
        try:
            p = calculeaza_pozitie_astrologica(jd_et_planete, corp_id)
            numar_casa = determina_casa_planetei(p['lon_pura'], jd_ut_case)
            planete_date.append({
                "nume": nume,
                "pozitie": p['pozitie_text'],
                "casa": f"{numar_casa:02d}",
                "miscare": p['miscare']
            })
            coordonate_totale[nume] = p['lon_pura']
        except:
            pass
    
    # Asteroizi
    asteroizi = {
        "Ceres": swe.CERES, "Pallas": swe.PALLAS, "Juno": swe.JUNO,
        "Vesta": swe.VESTA, "Chiron": swe.CHIRON, "Pholus": 16
    }
    
    asteroizi_date = []
    for nume, corp_id in asteroizi.items():
        try:
            p = calculeaza_pozitie_astrologica(jd_et_planete, corp_id)
            numar_casa = determina_casa_planetei(p['lon_pura'], jd_ut_case)
            asteroizi_date.append({
                "nume": nume,
                "pozitie": p['pozitie_text'],
                "casa": f"{numar_casa:02d}",
                "miscare": p['miscare']
            })
            coordonate_totale[nume] = p['lon_pura']
        except:
            pass
    
    # Stele fixe
    stele_fixe = {
        "Algol": "Algol", "Pleiades": "Alcyone", "Aldebaran": "Aldebaran",
        "Sirius": "Sirius", "Regulus": "Regulus", "Spica": "Spica",
        "Antares": "Antares", "Vega": "Vega", "Altair": "Altair"
    }
    
    stele_date = []
    for nume_afisat, nume_se in stele_fixe.items():
        try:
            s = calculeaza_stea_fixa(jd_et_planete, nume_se)
            numar_casa = determina_casa_planetei(s['lon_pura'], jd_ut_case)
            stele_date.append({
                "nume": nume_afisat,
                "pozitie": s['pozitie_text'],
                "casa": f"{numar_casa:02d}"
            })
            coordonate_totale[nume_afisat] = s['lon_pura']
        except:
            pass
    
    # Scoruri planetare
    scoruri_planete = {}
    total_eficienta = 0
    numar_evaluate = 0
    
    for nume_p in ["Soare", "Luna", "Mercur", "Venus", "Marte", "Jupiter", "Saturn", "Uranus", "Neptun", "Pluto"]:
        if nume_p in coordonate_totale:
            lon_p = coordonate_totale[nume_p]
            casa_p = determina_casa_planetei(lon_p, jd_ut_case)
            p_stat = calculeaza_pozitie_astrologica(jd_et_planete, planete_standard[nume_p])
            res_eval = evalueaza_forta_planeta(nume_p, lon_p, casa_p, p_stat['miscare'], lon_soare_acum)
            
            scoruri_planete[nume_p] = {
                "scor": res_eval['scor'],
                "eficienta": res_eval['eficienta'],
                "justificari": res_eval['justificari']
            }
            total_eficienta += res_eval['eficienta']
            numar_evaluate += 1
    
    scor_cosmic = total_eficienta / numar_evaluate if numar_evaluate > 0 else 0
    
    # Aspecte
    aspecte = calculeaza_toate_aspectele(coordonate_totale, 6.0)
    
    # Puncte arabe
    case_brute, ascmc_brut = swe.houses(jd_ut_case, float(LATITUDINE), float(LONGITUDINE), b'P')
    l_asc = ascmc_brut[0]
    l_soare = coordonate_totale.get("Soare", 0.0)
    l_luna = coordonate_totale.get("Luna", 0.0)
    l_venus = coordonate_totale.get("Venus", 0.0)
    l_jupiter = coordonate_totale.get("Jupiter", 0.0)
    
    casa_soare = determina_casa_planetei(l_soare, jd_ut_case)
    este_diurna = casa_soare >= 7
    
    puncte_arabe = {}
    try:
        fortuna = calculeaza_punct_arab(l_asc, l_luna, l_soare, este_diurna)
        puncte_arabe["Pars Fortunae (Noroc)"] = fortuna
        
        spirit = calculeaza_punct_arab(l_asc, l_soare, l_luna, este_diurna)
        puncte_arabe["Pars Spiritus (Suflet)"] = spirit
        
        eros = calculeaza_punct_arab(l_asc, l_venus, spirit['lon_pura'], este_diurna)
        puncte_arabe["Pars Amoris (Eros)"] = eros
    except:
        pass
    
    # Anotimp
    anotimp = calculeaza_anotimp_curent(lon_soare_acum)
    
    # Manzila Lunii
    res_luna = swe.calc_ut(jd_et_planete, swe.MOON, swe.FLG_SWIEPH)
    manzila_luna = determina_manzila_araba(res_luna[0][0])
    
    return {
        "timestamp": acum_local,
        "date_orizont_soare": date_orizont_soare,
        "lon_soare_acum": lon_soare_acum,
        "date_luna_dinamica": date_luna_dinamica,
        "durata_zi_ore": durata_zi_ore,
        "ore_zi": ore_zi,
        "ore_noapte": ore_noapte,
        "guvernator_zi": guvernator_zi,
        "guvernator_ora": guvernator_ora,
        "interval_ora_curenta": interval_ora_curenta,
        "tabel_case": tabel_case,
        "planete_date": planete_date,
        "asteroizi_date": asteroizi_date,
        "stele_date": stele_date,
        "scoruri_planete": scoruri_planete,
        "scor_cosmic": scor_cosmic,
        "aspecte": aspecte,
        "puncte_arabe": puncte_arabe,
        "anotimp": anotimp,
        "manzila_luna": manzila_luna
    }

# =====================================================================
# INTERFAȚA STREAMLIT
# =====================================================================

st.title("🌙 AstroCalcul Pro")
st.markdown("### Dashboard Astronomic și Astrologic Avansat")
st.markdown(f"**Locație:** {LATITUDINE}° N, {LONGITUDINE}° E | **Altitudine:** {ALTITUDINE} m")

# Sidebar pentru configurații
with st.sidebar:
    st.header("⚙️ Configurații")
    
    auto_refresh = st.checkbox("Auto-împrospătare (60 sec)", value=False)
    if auto_refresh:
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    st.header("📊 Informații")
    st.info(
        "Această aplicație calculează în timp real:\n"
        "• Pozițiile planetelor\n"
        "• Casele astrologice\n"
        "• Aspectele planetare\n"
        "• Orele planetare\n"
        "• Forța planetară\n"
        "• Și multe altele..."
    )
    
    st.divider()
    if st.button("🔄 Reîmprospătează datele"):
        st.cache_data.clear()
        st.rerun()

# Calculează datele
with st.spinner("Se calculează datele astronomice..."):
    date = calculeaza_toate_datele()

# Afișare timestamp
st.caption(f"Ultima actualizare: {date['timestamp'].strftime('%d-%m-%Y %H:%M:%S')}")

# Tab-uri pentru organizare
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌞 Astronomie", "⭐ Poziții", "🏠 Case", "🔮 Aspecte", "📈 Analiză"
])

# TAB 1: Astronomie și Fenomene
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("☀️ Soarele")
        if date['date_orizont_soare']:
            rasarit = date['date_orizont_soare'].get('Rasarit')
            apus = date['date_orizont_soare'].get('Apus')
            if rasarit:
                st.metric("Răsărit", rasarit.strftime("%H:%M:%S"))
            if apus:
                st.metric("Apus", apus.strftime("%H:%M:%S"))
        
        st.subheader("🌙 Luna")
        luna = date['date_luna_dinamica']
        st.metric("Faza", luna['faza'])
        st.metric("Iluminare", f"{luna['iluminare']:.1f}%")
        st.metric("Vârsta", f"{luna['varsta']:.1f} zile")
        
        st.subheader("📍 Manzila Lunară")
        manzila = date['manzila_luna']
        st.write(f"**Stația {manzila['numar']:02d}/28**")
        st.write(f"*{manzila['nume_arab']}* - {manzila['traducere']}")
        st.caption(f"Progres: {manzila['progres_text']}")
    
    with col2:
        st.subheader("🕐 Ore Planetare")
        st.metric("Guvernatorul Zilei", date['guvernator_zi'].upper())
        st.metric("Guvernatorul Orei", date['guvernator_ora'].upper())
        st.caption(f"Interval activ: {date['interval_ora_curenta']}")
        
        durata_zi = date['durata_zi_ore']
        if durata_zi > 0:
            st.metric("Durata Zilei", format_durata(durata_zi))
            st.metric("Durata Nopții", format_durata(24 - durata_zi))
        
        st.subheader("🌍 Anotimp")
        st.metric("Anotimp curent", date['anotimp'])
    
    # Ore planetare detaliate - expander
    with st.expander("📋 Tabel complet ore planetare"):
        if date['ore_zi']:
            st.markdown("**Ore de Zi**")
            ore_zi_df = pd.DataFrame([
                {"Ora": f"{num:02d}", "Planeta": p, "Start": s.strftime("%H:%M:%S"), "Sfârșit": e.strftime("%H:%M:%S")}
                for num, p, s, e in date['ore_zi']
            ])
            st.dataframe(ore_zi_df, use_container_width=True, hide_index=True)
        
        if date['ore_noapte']:
            st.markdown("**Ore de Noapte**")
            ore_noapte_df = pd.DataFrame([
                {"Ora": f"{num:02d}", "Planeta": p, "Start": s.strftime("%H:%M:%S"), "Sfârșit": e.strftime("%H:%M:%S")}
                for num, p, s, e in date['ore_noapte']
            ])
            st.dataframe(ore_noapte_df, use_container_width=True, hide_index=True)

# TAB 2: Poziții Astrologice
with tab2:
    st.subheader("🪐 Planete")
    if date['planete_date']:
        df_planete = pd.DataFrame(date['planete_date'])
        st.dataframe(df_planete, use_container_width=True, hide_index=True)
    
    st.subheader("🌠 Asteroizi")
    if date['asteroizi_date']:
        df_asteroizi = pd.DataFrame(date['asteroizi_date'])
        st.dataframe(df_asteroizi, use_container_width=True, hide_index=True)
    
    st.subheader("✨ Stele Fixe")
    if date['stele_date']:
        df_stele = pd.DataFrame(date['stele_date'])
        st.dataframe(df_stele, use_container_width=True, hide_index=True)
    
    st.subheader("⚜️ Puncte Arabe")
    if date['puncte_arabe']:
        for nume, punct in date['puncte_arabe'].items():
            st.metric(nume, punct['pozitie_text'])

# TAB 3: Case Astrologice
with tab3:
    st.subheader("🏠 Sistem Placidus")
    
    # Organizare case în 2 coloane
    if date['tabel_case']:
        col1, col2 = st.columns(2)
        items = list(date['tabel_case'].items())
        mid = len(items) // 2
        
        with col1:
            for eticheta, pozitie in items[:mid]:
                st.metric(eticheta, pozitie)
        
        with col2:
            for eticheta, pozitie in items[mid:]:
                st.metric(eticheta, pozitie)
    
    st.divider()
    st.caption("Sistemul Placidus - calculat cu latitudine geocentrică corectată")

# TAB 4: Aspecte Planetare
with tab4:
    st.subheader("🔮 Aspecte Active (Orbă ≤ 6°)")
    
    if date['aspecte']:
        for aspect in date['aspecte']:
            st.write(aspect)
    else:
        st.info("Nu s-au găsit aspecte majore în acest moment.")
    
    st.divider()
    st.caption("Aspecte calculate: Conjuncție (CON), Sextil (SEX), Cadran (CAR), Trion (TRI), Opoziție (OPO)")

# TAB 5: Analiză și Scoruri
with tab5:
    st.subheader("📊 Scor Cosmic Global")
    
    # Gauge pentru scorul cosmic
    scor = date['scor_cosmic']
    st.progress(scor / 100, text=f"Eficiență planetară totală: {scor:.1f}%")
    
    st.divider()
    st.subheader("⭐ Forța Planetară Individuală")
    
    if date['scoruri_planete']:
        for planeta, date_scor in date['scoruri_planete'].items():
            with st.expander(f"**{planeta}** - Scor: {date_scor['scor']:+d} | Eficiență: {date_scor['eficienta']:.1f}%"):
                for justif in date_scor['justificari']:
                    st.write(f"• {justif}")
    
    st.divider()
    
    # Export JSON
    st.subheader("💾 Export Date")
    if st.button("Exportă ca JSON"):
        # Pregătește datele pentru export
        export_data = {
            "timestamp": date['timestamp'].isoformat(),
            "configurare": {"lat": LATITUDINE, "lon": LONGITUDINE, "alt": ALTITUDINE},
            "scor_cosmic": date['scor_cosmic'],
            "scoruri_planete": date['scoruri_planete'],
            "aspecte": date['aspecte']
        }
        
        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Descarcă JSON",
            data=json_str,
            file_name=f"astro_data_{date['timestamp'].strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

# Footer
st.divider()
st.caption("🔮 Date calculate cu Swiss Ephemeris | Sistem tropical | Case Placidus")