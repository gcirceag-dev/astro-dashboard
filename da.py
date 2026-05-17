import os
import math
from datetime import datetime, timedelta
import pytz
import swisseph as swe
import streamlit as st

# --- CORECOȚIE ABSOLUTĂ: Adaugă linia asta aici, în capul fișierului! ---
st.set_page_config(page_title="Astro Dashboard", page_icon="🌌", layout="wide")
# -----------------------------------------------------------------------

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


# =====================================================================
# BLOCUL 2: UTILITARE PENTRU TIMP ȘI FORMATĂRI
# =====================================================================
def get_times():
    """Obține timpul curent, rotunjit la minutul fix, pentru sincronizare perfectă."""
    acum_local = datetime.now(zona_locala)
    
    # CHEIA: Eliminăm secundele și microsecundele din calculul dinamic
    acum_local = acum_local.replace(second=0, microsecond=0)
    acum_utc = acum_local.astimezone(pytz.utc)
    
    # JD pentru momentul actual fixat la minut
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
    return f"{h:02d} ore, {m:02d} minute, {s:02d} secunde"

# =====================================================================
# BLOCUL 3: LOGICA DE CALCUL EXPERTĂ (SWISS EPHEMERIS)
# =====================================================================
def calculeaza_evenimente_orizont(jd_miez, corp_id, geopos_lista):
    rezultate = {}
    evenimente = {"Rasarit": CALC_RISE, "Tranzit (Meridian)": CALC_TRANSIT, "Apus": CALC_SET}
    for nume_ev, masca_rsmi in evenimente.items():
        status, date_tup = swe.rise_trans(jd_miez, corp_id, masca_rsmi, geopos_lista)
        rezultate[nume_ev] = date_tup[0] if status == 0 else None
    return rezultate

def calculeaza_date_timp_real(jd_ut, corp_id):
    """Calculează azimutul, altitudinea aparentă, distanța și viteza corectă."""
    # Despachetăm explicit tuplul de pe prima poziție returnat de calc_ut
    date_ecl_tuplu, flag_ret = swe.calc_ut(jd_ut, corp_id, FLAG_FIIZIC)
    
    lon = date_ecl_tuplu[0]
    lat = date_ecl_tuplu[1]
    dist_raw = date_ecl_tuplu[2]
    
    dlon_cos = date_ecl_tuplu[3] * math.cos(math.radians(lat))
    dlat = date_ecl_tuplu[4]
    viteza_unghiulara_zi = math.sqrt(dlon_cos**2 + dlat**2)
    
    geopos = [float(LONGITUDINE), float(LATITUDINE), float(ALTITUDINE)]
    xin = [float(lon), float(lat), float(dist_raw)]
    
    # Apelăm corect azalt cu valorile float despachetate din index
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

# =====================================================================
# BLOCUL 4: LOGICA PENTRU ORE PLANETARE INEVALE
# =====================================================================
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

# =====================================================================
# BLOCUL 5: LOGICA REZOLVARE ANOTIMPURI ȘI CARDINALE SOARE
# =====================================================================
def gaseste_moment_cardinal(an, longitudine_tinta):
    """Găsește valoarea JD exactă când Soarele atinge o anumită lungime unghiulară."""
    zi_estimata = int((longitudine_tinta / 360.0) * 365.25) + 78
    jd_start = swe.julday(an, 1, 1, 0.0) + zi_estimata
    
    t0 = jd_start - 5.0
    t1 = jd_start + 5.0
    
    for _ in range(15):
        mijloc = (t0 + t1) / 2.0
        # Despachetăm corect tuplul returnat de calc_ut
        date_ecl_tuplu, flag_ret = swe.calc_ut(mijloc, swe.SUN, swe.FLG_SWIEPH)
        lon_act = date_ecl_tuplu[0]  # Luăm strict float-ul longitudinii
        
        dif = lon_act - longitudine_tinta
        if dif > 180.0: dif -= 360.0
        elif dif < -180.0: dif += 360.0
        
        if dif > 0: t1 = mijloc
        else: t0 = mijloc
        
    return (t0 + t1) / 2.0

def calculeaza_anotimp_curent(lon_soare):
    """Determină anotimpul curent din emisfera nordică pe baza longitudinii Soarelui."""
    if 0.0 <= lon_soare < 90.0:
        return "Primavara"
    elif 90.0 <= lon_soare < 180.0:
        return "Vara"
    elif 180.0 <= lon_soare < 270.0:
        return "Toamna"
    else:
        return "Iarna"


# =====================================================================
# BLOCUL 6: LOGICA PENTRU FAZELE ȘI DINAMICA LUNII
# =====================================================================
def calculeaza_dinamica_lunii(jd_ut):
    """Calculează iluminarea, vârsta aproximativă și faza curentă a Lunii."""
    # Indexul 1 conține fracția de iluminare reală (0.0 - 1.0) conform structurii
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
        "faza": faza_text
    }

def gaseste_faza_dinamica(jd_baza, faza_tinta, cauta_in_trecut=False):
    """
    Găsește valoarea JD exactă pentru faza țintă cea mai apropiată de jd_baza.
    faza_tinta: 0 = Lună Nouă, 90 = Primul Pătrar, 180 = Lună Plină, 270 = Ultimul Pătrar
    """
    # Dacă vrem faza din trecut, pornim căutarea cu 15 zile în urmă
    t0 = jd_baza - 15.0 if cauta_in_trecut else jd_baza
    t1 = jd_baza if cauta_in_trecut else jd_baza + 15.0
    
    # Căutare prin bisecție de înaltă precizie
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


# =====================================================================
# BLOCUL 7: LOGICA ASTROLOGICĂ PENTRU PLANETE, PUNCTE ȘI ASTEROIZI
# =====================================================================
SEMNE_ZODIAC = [
    "Berbec", "Taur", "Gemeni", "Rac", "Leu", "Fecioara",
    "Balanta", "Scorpion", "Sagetator", "Capricorn", "Varsator", "Pesti"
]

def format_pozitie_astrologica(lon_zecimala):
    """Transformă longitudinea ecliptică în formatul: Grade Minute'Secunde" Semn."""
    index_semn = int(lon_zecimala / 30.0) % 12
    grade_in_semn = lon_zecimala % 30.0
    
    m = int((grade_in_semn - int(grade_in_semn)) * 60)
    s = int(round((((grade_in_semn - int(grade_in_semn)) * 60) - m) * 60))
    if s >= 60: m += 1; s = 0
    if m >= 60: grade_in_semn += 1; m = 0
    
    nume_semn = SEMNE_ZODIAC[index_semn]
    # Modificarea liniei de return pentru a pune semnul la final
    return f"{int(grade_in_semn):02d}° {m:02d}'{s:02d}\" {nume_semn}"


def calculeaza_pozitie_astrologica(jd_ut, corp_id):
    """Calculează longitudinea ecliptică tropicală și viteza unui corp/punct."""
    flag_astrologic = swe.FLG_SWIEPH | swe.FLG_SPEED
    res_calc = swe.calc_ut(jd_ut, corp_id, flag_astrologic)
    
    date_ecl = res_calc[0]
    lon = date_ecl[0]
    viteza = date_ecl[3]
    
    miscare = "Retrograd" if viteza < 0 else "Direct"
    
    return {
        "pozitie_text": format_pozitie_astrologica(lon),
        "miscare": miscare,
        "lon_pura": lon  # Returnăm și valoarea numerică pentru calcule ulterioare
    }

def calculeaza_case_astrologice(jd_ut, sistem_caracter=b'P'):
    """
    Calculează cele 12 case în sistemul solicitat (implicit Placidus).
    Folosește swe.houses pentru aliniere perfectă cu Planetdance.
    """
    # Corecție geometrică pentru latitudinea geocentrică (elimină eroarea de 8-9 minute)
    lat_rad = math.radians(float(LATITUDINE))
    lat_geocentrica = math.degrees(math.atan(0.993277 * math.tan(lat_rad)))

    # Trimitem lat_geocentrica în loc de LATITUDINE directă
    cuspide, ascmc = swe.houses(
        jd_ut,
        lat_geocentrica,
        float(LONGITUDINE),
        sistem_caracter
    )
    
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
        else: 
            lon_punct = cuspide[i - 1]
            
        case_redenumite[nume_afisat] = format_pozitie_astrologica(lon_punct)
        
    return case_redenumite

def determina_casa_planetei(lon_planeta, jd_ut):
    """
    Determină numărul casei (1-12) în care se află o planetă.
    Folosește sistemul Placidus (b'P') bazat pe coordonatele tale fixe.
    """
    # Obținem cuspedele brute în grade (tuplu de 12 elemente, indexate 0-11)
    cuspide, _ = swe.houses(
        jd_ut,
        float(LATITUDINE),
        float(LONGITUDINE),
        b'P'
    )
    
    # Parcurgem cele 12 sectoare de case
    for i in range(12):
        start_casa = cuspide[i]
        # Casa următoare (iar pentru Casa 12, casa următoare este Casa 1)
        end_casa = cuspide[(i + 1) % 12]
        
        # Caz standard: cuspida de sfârșit are valoare mai mare decât cea de început
        if start_casa < end_casa:
            if start_casa <= lon_planeta < end_casa:
                return i + 1
        # Caz special: casa intersectează punctul de 0° Berbec (ex: start=345°, end=15°)
        else:
            if lon_planeta >= start_casa or lon_planeta < end_casa:
                return i + 1
                
    return 1  # Valoare de siguranță

def calculeaza_punct_arab(lon_asc, lon_corp1, lon_corp2, este_diurn=True, formula_diurna_fixa=True):
    """
    Calculează poziția unui punct arab după formula standard: Asc + Corp1 - Corp2.
    """
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

MANZILE_DATE = {
    1: ("Al-Sharatain", "Cele doua semne"), 2: ("Al-Butain", "Micul pantece"), 3: ("Al-Thurayya", "Pleiadele / Abundenta"),
    4: ("Al-Dabaran", "Urmaritorul / Aldebaran"), 5: ("Al-Haq'ah", "Cercul de par / Corona"), 6: ("Al-Han'ah", "Semnul de foc / Arc"),
    7: ("Al-Dhira", "Bratul leului / Gemeni"), 8: ("Al-Nathrah", "Zborul / Cuibul"), 9: ("Al-Tarf", "Privirea / Ochii Leului"),
    10: ("Al-Jabhah", "Fruntea Leului / Regulus"), 11: ("Al-Zubrah", "Coama Leului"), 12: ("Al-Sarfah", "Schimbatorul de vreme"),
    13: ("Al-Awwa", "Cainele latrator"), 14: ("Al-Simak", "Cel Neinarmat / Spica"), 15: ("Al-Ghafr", "Acoperamantul"),
    16: ("Al-Zubana", "Clestii Scorpionului"), 17: ("Al-Iklil", "Coroana"), 18: ("Al-Qalb", "Inima / Antares"),
    19: ("Al-Shaulah", "Acul Scorpionului"), 20: ("Al-Na'aim", "Strutii"), 21: ("Al-Baldah", "Orasul / Spatiul gol"),
    22: ("Al-Sa'd al-Dhabih", "Norocul Macelarului"), 23: ("Al-Sa'd al-Bula", "Norocul Inghititorului"),
    24: ("Al-Sa'd al-Su'ud", "Norocul Norocurilor"), 25: ("Al-Sa'd al-Ahbiyah", "Norocul Corturilor"),
    26: ("Al-Fargh al-Muqaddam", "Gura de sus a putului"), 27: ("Al-Fargh al-Mu'ahhar", "Gura de jos a putului"),
    28: ("Risha / Batn al-Hut", "Pantecele Pestelui")
}

def determina_manzila_araba(lon_zecimala):
    """
    Determină numărul, numele arab și traducerea Manzilei Arăbești (1-28).
    Fiecare manzilă ocupă fix 12.8571 grade (12° 51' 26").
    """
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
    """
    Calculează scorul matematic (-13 la +10) și eficiența (0-100%) pentru o planetă.
    """
    scor = 0
    justificari = []
    
    idx_semn = int(lon_p / 30.0) % 12
    semn_p = SEMNE_ZODIAC[idx_semn]
    
    # 1. Evaluare Demnități Esențiale
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

    # 2. Evaluare Mișcare
    if miscare_p == "Direct":
        scor += 2
        justificari.append("Direct (+2)")
    elif miscare_p == "Retrograd":
        scor -= 2
        justificari.append("Retrograd (-2)")

    # 3. Evaluare Poziție în Case
    if casa_p in [1, 4, 7, 10]:
        scor += 3
        justificari.append(f"Casa {casa_p:02d} Angulara (+3)")
    elif casa_p in [2, 5, 8, 11]:
        scor += 1
        justificari.append(f"Casa {casa_p:02d} Succedenta (+1)")
    else:
        scor -= 2
        justificari.append(f"Casa {casa_p:02d} Cadenta (-2)")

    # 4. Evaluare Combustie (Doar pentru corpuri care nu sunt Soarele sau Luna)
    if nume_p not in ["Soare", "Luna"]:
        dif_s = abs(lon_p - lon_soare)
        dist_soare = dif_s if dif_s <= 180.0 else 360.0 - dif_s
        if dist_soare < 8.5:
            scor -= 4
            justificari.append("COMBUST (-4)")

    # Mapare matematică de la intervalul [-13, +10] la [0%, 100%]
    # Eficiență = (scor - (-13)) / (10 - (-13)) * 100
    eficienta = ((scor + 13) / 23.0) * 100.0
    
    return {"scor": scor, "eficienta": eficienta, "justificari": justificari}


def calculeaza_stea_fixa(jd_ut, nume_stea_se):
    """
    Calculează longitudinea ecliptică tropicală și poziția în casă pentru o stea fixă.
    """
    flag_astrologic = swe.FLG_SWIEPH | swe.FLG_SPEED
    
    # Prindem întreaga structură brută returnată de modul (tuplu de 3 elemente)
    res_fixstar = swe.fixstar_ut(nume_stea_se, jd_ut, flag_astrologic)
    
    # Primul element conține lista de coordonate [lon, lat, dist, dlon, dlat, ddist]
    date_ecl_tuplu = res_fixstar[0]
    lon = date_ecl_tuplu[0]
    
    return {
        "pozitie_text": format_pozitie_astrologica(lon),
        "lon_pura": lon
    }




# =====================================================================
# BLOCUL 8: LOGICA PENTRU CALCULUL ASPECTELOR PLANETARE COMPLET
# =====================================================================
ASPECTE_MAJORE = {
    "CON": 0.0,
    "SEX": 60.0,
    "CAR": 90.0,
    "TRI": 120.0,
    "OPO": 180.0
}

def format_orba_aspect(orba_zecimala):
    """Formatare precisă pentru orba reziduală în minute și secunde."""
    val = abs(orba_zecimala)
    d = int(val)
    m = int((val - d) * 60)
    s = int(round((((val - d) * 60) - m) * 60))
    if s >= 60: m += 1; s = 0
    if m >= 60: d += 1; m = 0
    return f"{d}° {m:02d}' {s:02d}\""

def calculeaza_toate_aspectele(toate_coordonatele, orba_maxima=6.0):
    """
    Compară TOATE corpurile din listă, le sortează ascendent după orbă 
    și returnează șirurile de text. Filtrează stelele și punctele fictive.
    """
    aspecte_temporare = []
    nume_corpuri = list(toate_coordonatele.keys())
    total_corpuri = len(nume_corpuri)
    
    # 1. Lista cu numele exacte ale stelelor
    nume_stele_fixe = [
        "Algol", "Pleiades (Alcyone)", "Aldebaran", "Rigel", "Betelgeuse", 
        "Sirius", "Regulus", "Spica", "Arcturus", "Antares", "Vega", "Altair", "Fomalhaut"
    ]
    
    # 2. Lista neagră cu cele 10 puncte fictive/matematice care generează zgomot
    puncte_fictive_zgomot = [
        "Nod Nord (Mean)", "Nod Sud (Mean)", 
        "Nod Nord (True)", "Nod Sud (True)",
        "Lilith (Mean)  ", "Lilith (True)  ",
        "Lilith (Mean)", "Lilith (True)",  # Fallback în caz de variații de spații
        "Apogeu Interp. ", "Perigeu Interp.",
        "Apogeu Interp.", "Perigeu Interp."
    ]
    
    for i in range(total_corpuri):
        for j in range(i + 1, total_corpuri):
            c1 = nume_corpuri[i]
            c2 = nume_corpuri[j]
            
            # FILTRU 1: Nu calculăm aspecte între două stele fixe
            if c1 in nume_stele_fixe and c2 in nume_stele_fixe:
                continue
                
            # FILTRU 2: Nu calculăm aspecte interne între punctele matematice (Noduri, Lilith, Apogeu)
            # Curăță toate conjuncțiile/opozițiile dintre True și Mean
            if c1 in puncte_fictive_zgomot and c2 in puncte_fictive_zgomot:
                continue
                
            lon1 = toate_coordonatele[c1]
            lon2 = toate_coordonatele[c2]
            
            dif = abs(lon1 - lon2)
            distanta = dif if dif <= 180.0 else 360.0 - dif
            
            for abrevier, unghi_perfect in ASPECTE_MAJORE.items():
                # REGULA TRADIȚIONALĂ: Dacă implică o stea fixă, acceptăm DOAR CON și OPO
                if (c1 in nume_stele_fixe or c2 in nume_stele_fixe) and abrevier not in ["CON", "OPO"]:
                    continue
                    
                deviatie_bruta = distanta - unghi_perfect
                orba_exacta = abs(deviatie_bruta)
                
                if orba_exacta <= orba_maxima:
                    semn = "+" if deviatie_bruta >= 0 else "-"
                    orba_text = format_orba_aspect(orba_exacta)
                    
                    text_formatat = f"  - {c1:<17} {abrevier} {c2:<17} {semn} {orba_text}"
                    aspecte_temporare.append((orba_exacta, text_formatat))
                    break
                    
    aspecte_temporare.sort(key=lambda x: x[0])
    return [item[1] for item in aspecte_temporare]

# =====================================================================
# BLOCUL 9: INTERFAȚA GRAFICĂ (BUCATA 1: TABEL CURAT SOARE - LUNĂ)
# =====================================================================
st.set_page_config(page_title="Astro Dashboard", page_icon="🌌", layout="wide")

# CSS global: fundal alb pur, text negru pur, font monospace uniform
st.markdown(
    """
    <style>
    .stApp, div[data-testid="stAppViewContainer"], table, tr, td, th {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #000000 !important;
        font-family: monospace !important;
        font-size: 14px !important;
    }
    button[title="Copy to clipboard"] { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True
)

tab1, tab2, tab3 = st.tabs(["Soare - Luna", "Astro", "Aspecte"])

with tab1:
    corpuri_luna_soare = {"Soare": swe.SUN, "Luna": swe.MOON}
    date_orizont_soare = {}
    lon_soare_acum = 0.0
    
    # Construim setul de date simplificat pentru tabelul nativ
    luna_soare_date = []
    for nume, corp_id in corpuri_luna_soare.items():
        try:
            ore_orizont = calculeaza_evenimente_orizont(jd_miez, corp_id, geopos_lista)
            date_tr = calculeaza_date_timp_real(jd_acum, corp_id)
            
            rasarit_t = jd_to_datetime(ore_orizont["Rasarit"]).strftime('%H:%M:%S') if ore_orizont["Rasarit"] else "N/A"
            meridian_t = jd_to_datetime(ore_orizont["Tranzit (Meridian)"]).strftime('%H:%M:%S') if ore_orizont["Tranzit (Meridian)"] else "N/A"
            apus_t = jd_to_datetime(ore_orizont["Apus"]).strftime('%H:%M:%S') if ore_orizont["Apus"] else "N/A"
            
            if corp_id == swe.SUN:
                lon_soare_acum = date_tr["lon_ecliptica"]
                date_orizont_soare = ore_orizont
                
            # Adăugăm rândul curat în matrice
            luna_soare_date.append({
                "Corp": nume,
                "Răsărit": rasarit_t,
                "Meridian": meridian_t,
                "Apus": apus_t,
                "Altitudine": format_grade(date_tr['altitudine']),
                "Azimut": format_grade(date_tr['azimut']),
                "Distanță (km)": f"{date_tr['distanta']:,.2f}",
                "Viteză (km/s)": f"{date_tr['viteza']:.4f}"
            })
        except:
            pass

    # Randăm tabelul nativ Streamlit, fin, aliniat la stânga și cu auto-wrap activat
    st.dataframe(
        luna_soare_date,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Corp": st.column_config.TextColumn("Corp", width="small"),
            "Răsărit": st.column_config.TextColumn("Răsărit", width="small"),
            "Meridian": st.column_config.TextColumn("Meridian", width="small"),
            "Apus": st.column_config.TextColumn("Apus", width="small")
        }
    )




swe.close()




