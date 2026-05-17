import os
import math
import json
from datetime import datetime, timedelta
import pytz
import swisseph as swe

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
# BLOCUL 9: EXECUTARE ȘI AFIȘARE DATE
# =====================================================================
acum_local, jd_acum, jd_miez = get_times()
geopos_lista = [LONGITUDINE, LATITUDINE, ALTITUDINE]

# Aici pui cele două linii noi pentru corecția Delta T
delta_t_zile = swe.deltat(jd_acum) / 86400.0
jd_et_planete = jd_acum + delta_t_zile
jd_ut_case = jd_acum

print(f"Data calculului (Local): {acum_local.strftime('%d-%m-%Y')} | Ora actuala: {acum_local.strftime('%H:%M:%S')}")
print(f"Coordonate fixe: {LATITUDINE} N, {LONGITUDINE} E")
print("=" * 60)

corpuri = {"SOARE": swe.SUN, "LUNA": swe.MOON}
date_orizont_soare = {}
lon_soare_acum = 0.0

for nume, corp_id in corpuri.items():
    print(f"\n[{nume}]")
    print("  Evenimente zilnice de baza:")
    ore_orizont = calculeaza_evenimente_orizont(jd_miez, corp_id, geopos_lista)
    for nume_ev, jd_ev in ore_orizont.items():
        if jd_ev:
            dt_ev = jd_to_datetime(jd_ev)
            print(f"    - {nume_ev:<22} : {dt_ev.strftime('%H:%M:%S')}")
            if corp_id == swe.SUN:
                date_orizont_soare[nume_ev] = dt_ev
        else:
            print(f"    - {nume_ev:<22} : Date indisponibile")

    print("  Date fizice in timp real (acum):")
    try:
        date_tr = calculeaza_date_timp_real(jd_acum, corp_id)
        print(f"    - Altitudine             : {format_grade(date_tr['altitudine'])}")
        print(f"    - Azimut (de la Nord)    : {format_grade(date_tr['azimut'])}")
        print(f"    - Distanta curenta       : {date_tr['distanta']:,.2f} km")
        print(f"    - Viteza orbitala        : {date_tr['viteza']:.4f} km/s")
        if corp_id == swe.SUN:
            lon_soare_acum = date_tr["lon_ecliptica"]
    
        # --- AICI INSERĂM AFISAREA MANZILEI DOAR PENTRU LUNĂ ---
        if corp_id == swe.MOON:
            # Pentru că în această fază a scriptului coordonate_totale nu e definit, calculăm poziția brută pe loc
            res_luna_brut = swe.calc_ut(jd_et_planete, swe.MOON, swe.FLG_SWIEPH)
            lon_luna_brut = res_luna_brut[0][0]
            m_luna = determina_manzila_araba(lon_luna_brut)
            print(f"    - Manzil al-Qamar (Luna) : Stația {m_luna['numar']:02d}/28 - {m_luna['nume_arab']} ({m_luna['traducere']}) | Poziție: {m_luna['progres_text']}")
        # ------------------------------------------------------
    
    except Exception as e:
        print(f"    - Eroare date dinamice: {e}")

# Secțiunea Dinamica și Fazele Lunii
print("\n" + "=" * 60)
print("[DINAMICA ȘI FAZELE LUNII]")
try:
    date_luna_dinamica = calculeaza_dinamica_lunii(jd_acum)
    print(f"  - Faza curenta             : {date_luna_dinamica['faza']}")
    print(f"  - Iluminare disc           : {date_luna_dinamica['iluminare']:.2f}%")
    print(f"  - Varsta Lunii             : {date_luna_dinamica['varsta']:.2f} zile")
    
    # 1. Aflăm elongația curentă (Arcul Soli-Lunar) din motorul de calcul
    res_soare = swe.calc_ut(jd_et_planete, swe.SUN, swe.FLG_SWIEPH)
    res_luna = swe.calc_ut(jd_et_planete, swe.MOON, swe.FLG_SWIEPH)
    elongatie_act = (res_luna[0][0] - res_soare[0][0]) % 360.0
    
    # --- PROPRIA LINIE DE AFIȘARE A ARCULUI ---
    print(f"  - Arcul Soli-Lunar         : {format_grade(elongatie_act)}")
    # ------------------------------------------
    
    print("  Momentele fazelor principale (Cronologic):")
    
    faze_ordine = [0.0, 90.0, 180.0, 270.0]
    nume_faze = {0.0: "Luna Noua      ", 90.0: "Primul Patrar  ", 180.0: "Luna Plina     ", 270.0: "Ultimul Patrar "}
    
    # Identificăm indexul fazei din trecut pe baza elongației deja extrase
    if 0.0 <= elongatie_act < 90.0: idx_trecut = 0
    elif 90.0 <= elongatie_act < 180.0: idx_trecut = 1
    elif 180.0 <= elongatie_act < 270.0: idx_trecut = 2
    else: idx_trecut = 3
        
    # 2. Calculăm și afișăm faza din TRECUT
    faza_t = faze_ordine[idx_trecut]
    jd_t = gaseste_faza_dinamica(jd_acum, faza_t, cauta_in_trecut=True)
    dt_t = jd_to_datetime(jd_t)
    print(f"    - [TRECUT] {nume_faze[faza_t]} : {dt_t.strftime('%d-%m-%Y %H:%M:%S')}")
    
    # 3. Calculăm și afișăm următoarele 3 faze din VIITOR
    jd_cursor = jd_t + 1.0  
    for k in range(1, 4):
        idx_v = (idx_trecut + k) % 4
        faza_v = faze_ordine[idx_v]
        
        jd_v = gaseste_faza_dinamica(jd_cursor, faza_v, cauta_in_trecut=False)
        dt_v = jd_to_datetime(jd_v)
        print(f"    - [VIITOR] {nume_faze[faza_v]} : {dt_v.strftime('%d-%m-%Y %H:%M:%S')}")
        
        jd_cursor = jd_v + 1.0  

except Exception as e:
    print(f"  - Eroare la calculul dinamic al fazelor Lunii: {e}")

# Secțiunea calcul durate ore planetare (Zi / Noapte) cu Guvernatori dinamici
print("\n" + "=" * 60)
print("[DURATE CALENDARISTICE ȘI CRONOCRAȚI PLANETARI]")
dt_r = date_orizont_soare.get("Rasarit")
dt_a = date_orizont_soare.get("Apus")

if dt_r and dt_a:
    durata_zi_ore = (dt_a - dt_r).total_seconds() / 3600.0
    durata_noapte_ore = 24.0 - durata_zi_ore
    print(f"  - Durata zilei             : {format_durata(durata_zi_ore)}")
    print(f"  - Durata noptii            : {format_durata(durata_noapte_ore)}")
    
    ore_zi, ore_noapte = genereaza_ore_planetare(dt_r, dt_a)
    
    guvernator_zi = STAPAN_ZI[dt_r.weekday()]
    guvernator_ora = "Nedeterminat"
    interval_ora_curenta = ""
    
    # Identificăm dinamic guvernatorul și intervalul orar activ
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

    # PANOU CENTRALIZAT CURAT DE GUVERNATORI
    print("\n  --- GUVERNATORI TIMP REAL ---")
    print(f"    - GUVERNATORUL ZILEI     : {guvernator_zi.upper()}")
    print(f"    - GUVERNATORUL OREI ACUM : {guvernator_ora.upper():<7} | Interval active: {interval_ora_curenta}")
    
    # Tabelele de ore planetare se printează acum curat, fără indicatorul "<- ACUM" în listă
    print("\n[ORE PLANETARE DE ZI]")
    for numar, planeta, start, end in ore_zi:
        print(f"  Ora {numar:02d} ({planeta:<7}) : {start.strftime('%H:%M:%S')} - {end.strftime('%H:%M:%S')}")
        
    print("\n[ORE PLANETARE DE NOAPTE]")
    for numar, planeta, start, end in ore_noapte:
        print(f"  Ora {numar:02d} ({planeta:<7}) : {start.strftime('%H:%M:%S')} - {end.strftime('%H:%M:%S')}")



# Secțiunea Anotimpuri astronomice
print("\n" + "=" * 60)
print("[ANOTIMPURI ȘI PUNCTE CARDINALE SOARE]")
an_curent = acum_local.year
anotimp = calculeaza_anotimp_curent(lon_soare_acum)
print(f"  - Anotimpul curent (Nord)  : {anotimp} (Pozitie Soare: {format_grade(lon_soare_acum)})")

puncte_cardinale = {
    "Echinoptiu Primavara (0°)": 0.0,
    "Solstitiu Vara (90°)     ": 90.0,
    "Echinoptiu Toamna (180°) ": 180.0,
    "Solstitiu Iarna (270°)   ": 270.0
}

print("  Momentele exacte ale anului curent:")
for nume_pct, unghi in puncte_cardinale.items():
    jd_pct = gaseste_moment_cardinal(an_curent, unghi)
    dt_pct = jd_to_datetime(jd_pct)
    print(f"    - {nume_pct} : {dt_pct.strftime('%d-%m-%Y %H:%M:%S')}")

# Secțiunea Case Astrologice (Sistem Placidus)
print("\n" + "=" * 60)
print("[CASE ASTROLOGICE ȘI AXE - PLACIDUS]")
try:
    tabel_case = calculeaza_case_astrologice(jd_acum, b'P')
    
    for eticheta, pozitie_text in tabel_case.items():
        print(f"  - {eticheta:<15} : {pozitie_text}")
except Exception as e:
    print(f"  - Eroare la calculul caselor astrologice: {e}")


# Secțiunea Poziții Astrologice Complete
print("\n" + "=" * 60)
print("[POZIȚII ASTROLOGICE TROPICALE]")

# --- AICI ADAUGI LINIA ACEASTA CARE LIPSEȘTE ---
coordonate_totale = {}
# -----------------------------------------------

# 1. Planete Standard (Soare -> Pluto)
planete_standard = {
    "Soare": swe.SUN, "Luna": swe.MOON, "Mercur": swe.MERCURY, "Venus": swe.VENUS,
    "Marte": swe.MARS, "Jupiter": swe.JUPITER, "Saturn": swe.SATURN,
    "Uranus": swe.URANUS, "Neptun": swe.NEPTUNE, "Pluto": swe.PLUTO
}

print("\n--- PLANETE STANDARD ---")
for nume, corp_id in planete_standard.items():
    try:
        p = calculeaza_pozitie_astrologica(jd_et_planete, corp_id)
        numar_casa = determina_casa_planetei(p['lon_pura'], jd_ut_case)
        print(f"  - {nume:<15} : {p['pozitie_text']:<25} | Casa: {numar_casa:02d} | ({p['miscare']})")
        
        # LINIA DE SALVARE OBLIGATORIE:
        coordonate_totale[nume] = p['lon_pura']
    except Exception as e:
        print(f"  - {nume:<15} : Eroare la calcul: {e}")


# 2. Puncte Fictive ale Lunii (Înlocuit constantele absente cu ID-uri numerice)
puncte_fictive = {
    "Nod Nord (Mean)": swe.MEAN_NODE,
    "Nod Nord (True)": swe.TRUE_NODE,
    "Lilith (Mean)  ": swe.MEAN_APOG,  
    "Lilith (True)  ": swe.OSCU_APOG,  
    "Apogeu Interp. ": 21,  # ID-ul nativ pentru Apogeul Interpolat al Lunii
    "Perigeu Interp.": 22   # ID-ul nativ pentru Perigeul Interpolat al Lunii
}

print("\n--- NODURI ȘI PUNCTE FICTIVE ---")
for nume, corp_id in puncte_fictive.items():
    try:
        p = calculeaza_pozitie_astrologica(jd_et_planete, corp_id)
        numar_casa = determina_casa_planetei(p['lon_pura'], jd_ut_case)
        print(f"  - {nume:<15} : {p['pozitie_text']:<25} | Casa: {numar_casa:02d} | ({p['miscare']})")
        
        # LINIA DE SALVARE OBLIGATORIE:
        coordonate_totale[nume] = p['lon_pura']
        
        if "Nod Nord" in nume:
            tip_nod = "Mean" if "Mean" in nume else "True"
            lon_sud = (p['lon_pura'] + 180.0) % 360.0
            numar_casa_sud = determina_casa_planetei(lon_sud, jd_ut_case)
            print(f"  - Nod Sud ({tip_nod:<4}) : {format_pozitie_astrologica(lon_sud):<25} | Casa: {numar_casa_sud:02d} | ({p['miscare']})")
            
            # SALVARE NOD SUD:
            coordonate_totale[f"Nod Sud ({tip_nod})"] = lon_sud
    except Exception as e:
        print(f"  - {nume:<15} : Eroare la calcul: {e}")

# secțiunea 3 (Asteroizi) din Blocul 8 pentru a-l include pe PHOLUS (ID 16)
asteroizi = {
    "Ceres": swe.CERES,   # ID 17
    "Pallas": swe.PALLAS, # ID 18
    "Juno": swe.JUNO,     # ID 19
    "Vesta": swe.VESTA,   # ID 20
    "Chiron": swe.CHIRON, # ID 15
    "Pholus": 16          # ID 16 - Adăugat conform listei native
}

print("\n--- ASTEROIZI PRINCIPALI ---")
for nume, corp_id in asteroizi.items():
    try:
        p = calculeaza_pozitie_astrologica(jd_et_planete, corp_id)
        numar_casa = determina_casa_planetei(p['lon_pura'], jd_ut_case)
        print(f"  - {nume:<15} : {p['pozitie_text']:<25} | Casa: {numar_casa:02d} | ({p['miscare']})")
        
        # LINIA DE SALVARE OBLIGATORIE:
        coordonate_totale[nume] = p['lon_pura']
    except Exception as e:
        print(f"  - {nume:<15} : Eroare la calcul: {e}")

# secțiunea 4 (Uraniene) din Blocul 8 pentru a o include pe ISIS (ID 48)
uraniene = {
    "Cupido": 40, "Hades": 41, "Zeus": 42, "Kronos": 43,
    "Apollon": 44, "Admetos": 45, "Vulkanus": 46, "Poseidon": 47,
    "Isis": 48            # ID 48 - Adăugat conform listei native
}

print("\n--- PLANETE URANIENE (HAMBURG) & ESOTERICE ---")
for nume, corp_id in uraniene.items():
    try:
        p = calculeaza_pozitie_astrologica(jd_et_planete, corp_id)
        numar_casa = determina_casa_planetei(p['lon_pura'], jd_ut_case)
        print(f"  - {nume:<15} : {p['pozitie_text']:<25} | Casa: {numar_casa:02d} | ({p['miscare']})")
        
        # LINIA DE SALVARE OBLIGATORIE:
        coordonate_totale[nume] = p['lon_pura']
    except Exception as e:
        print(f"  - {nume:<15} : Eroare la calcul: {e}")

# =====================================================================
# 5. STELE FIXE MAJORE (MUTATE AICI PENTRU A POPULA DICȚIONARUL)
# =====================================================================
stele_fixe = {
    "Algol": "Algol",
    "Pleiades (Alcyone)": "Alcyone",
    "Aldebaran": "Aldebaran",
    "Rigel": "Rigel",
    "Betelgeuse": "Betelgeuse",
    "Sirius": "Sirius",
    "Regulus": "Regulus",
    "Spica": "Spica",
    "Arcturus": "Arcturus",
    "Antares": "Antares",
    "Vega": "Vega",
    "Altair": "Altair",
    "Fomalhaut": "Fomalhaut"
}

print("\n--- STELE FIXE MAJORE ---")
for nume_afisat, nume_se in stele_fixe.items():
    try:
        s = calculeaza_stea_fixa(jd_et_planete, nume_se)
        numar_casa = determina_casa_planetei(s['lon_pura'], jd_ut_case)
        
        print(f"  - {nume_afisat:<19} : {s['pozitie_text']:<25} | Casa: {numar_casa:02d}")
        
        # Le salvăm în dicționarul general ÎNAINTE ca aspectele să fie calculate
        coordonate_totale[nume_afisat] = s['lon_pura']
    except Exception as e:
        print(f"  - {nume_afisat:<19} : Eroare la calcul (Nume invalid în SE?): {e}")


# =====================================================================
# SECTIUNEA: EVALUAREA AUTOMATĂ A FORȚEI PLANETARE
# =====================================================================
print("\n" + "=" * 60)
print("[EVALUAREA DINAMICĂ A FORȚEI PLANETARE (SCORURI DE TRANZIT)]")

scoruri_planete_json = {}
total_eficienta_colectata = 0.0
numar_planete_evaluate = 0

l_soare_eval = coordonate_totale.get("Soare", 0.0)

for nume_p in ["Soare", "Luna", "Mercur", "Venus", "Marte", "Jupiter", "Saturn", "Uranus", "Neptun", "Pluto"]:
    if nume_p in coordonate_totale:
        lon_p = coordonate_totale[nume_p]
        # Preluăm casa și mișcarea din structura deja calculată în tabloul tău extins text
        casa_p = determina_casa_planetei(lon_p, jd_ut_case)
        
        # Extragem starea de retrogradare din motor
        p_stat = calculeaza_pozitie_astrologica(jd_et_planete, planete_standard[nume_p])
        miscare_p = p_stat['miscare']
        
        res_eval = evalueaza_forta_planeta(nume_p, lon_p, casa_p, miscare_p, l_soare_eval)
        
        # Afișare text curată pe ecran
        justificari_text = " | ".join(res_eval["justificari"])
        print(f"  - {nume_p:<10} : [{justificari_text}]")
        print(f"                 -> Scor: {res_eval['scor']:+2} | Eficiență: {res_eval['eficienta']:.1f}%")
        
        total_eficienta_colectata += res_eval['eficienta']
        numar_planete_evaluate += 1
        
        # Stocare pentru exportul JSON
        scoruri_planete_json[nume_p] = {
            "scor_numeric": res_eval['scor'],
            "procent_eficienta": f"{res_eval['eficienta']:.1f}%",
            "justificari": res_eval["justificari"]
        }

scor_cosmic_global = total_eficienta_colectata / numar_planete_evaluate if numar_planete_evaluate > 0 else 0.0

print("\n" + "=" * 60)
print("[SCORUL COSMIC GLOBAL AL MOMENTULUI]")
print(f"  - Indice de eficiență planetară totală: {scor_cosmic_global:.1f}%")


# =====================================================================
# SECȚIUNEA FINALĂ: AFIȘARE ASPECTE SORTATE (MUTATE LA CAPĂTUL SCRIPTULUI)
# =====================================================================
print("\n" + "=" * 60)
print("[ASPECTE PLANETARE ACTIVE - ORBĂ MAXIM 6° - SORTATE ASCENDENT]")
try:
    # Acum coordonate_totale conține absolut toate corpurile, inclusiv stelele fixe
    liste_imprimate = calculeaza_toate_aspectele(coordonate_totale, orba_maxima=6.0)
    
    if liste_imprimate:
        for linie_aspect in liste_imprimate:
            print(linie_aspect)
    else:
        print("  - Nu s-au găsit aspecte unghiulare strânse sub 6° între corpurile verificate.")
except Exception as e:
    print(f"  - Eroare la generarea matricei de aspecte: {e}")

# Închiderea corectă a resurselor Swiss Ephemeris la final de tot

# =====================================================================
# SECTIUNEA: PANOU EXTINS PENTRU PUNCTE ARABE (LOTS)
# =====================================================================
print("\n" + "=" * 60)
print("[PANOU FILOSOFIC / PUNCTE ARABE MAJORE]")

# REPARATIE: Extragem indexul 0 pentru Ascendent din tuplul returnat de swe.houses
case_brute, ascmc_brut = swe.houses(jd_ut_case, float(LATITUDINE), float(LONGITUDINE), b'P')
l_asc = ascmc_brut[0]

l_soare = coordonate_totale.get("Soare", 0.0)
l_luna = coordonate_totale.get("Luna", 0.0)
l_mercur = coordonate_totale.get("Mercur", 0.0)
l_venus = coordonate_totale.get("Venus", 0.0)
l_marte = coordonate_totale.get("Marte", 0.0)
l_jupiter = coordonate_totale.get("Jupiter", 0.0)

casa_soare = determina_casa_planetei(l_soare, jd_ut_case)
este_harta_diurna = casa_soare >= 7

print(f"  - Tipul Sectei (Harta)     : {'DIURNĂ (Zi)' if este_harta_diurna else 'NOCTURNĂ (Noapte)'}")
print("\n--- CELE 5 PUNCTE ARABE/ELENISTICE MAJORE ---")
try:
    # 1. Pars Fortunae (Trup, Noroc fizic, Sănătate)
    # Diurn = Asc + Luna - Soare | Nocturn = Asc + Soare - Luna
    fortuna = calculeaza_punct_arab(l_asc, l_luna, l_soare, este_harta_diurna, formula_diurna_fixa=True)
    casa_fortuna = determina_casa_planetei(fortuna['lon_pura'], jd_ut_case)
    print(f"  - Pars Fortunae (Noroc)   : {fortuna['pozitie_text']:<25} | Casa: {casa_fortuna:02d}")
    coordonate_totale["Pars Fortunae"] = fortuna['lon_pura']

    # 2. Pars Spiritus (Minte, Suflet, Intelect, Carieră)
    # Diurn = Asc + Soare - Luna | Nocturn = Asc + Luna - Soare
    spirit = calculeaza_punct_arab(l_asc, l_soare, l_luna, este_harta_diurna, formula_diurna_fixa=True)
    casa_spirit = determina_casa_planetei(spirit['lon_pura'], jd_ut_case)
    print(f"  - Pars Spiritus (Suflet)  : {spirit['pozitie_text']:<25} | Casa: {casa_spirit:02d}")
    coordonate_totale["Pars Spiritus"] = spirit['lon_pura']

    # 3. Pars Amoris / Eros (Iubire, Relații, Dorințe)
    # Diurn = Asc + Venus - Spirit | Nocturn = Asc + Spirit - Venus
    eros = calculeaza_punct_arab(l_asc, l_venus, spirit['lon_pura'], este_harta_diurna, formula_diurna_fixa=True)
    casa_eros = determina_casa_planetei(eros['lon_pura'], jd_ut_case)
    print(f"  - Pars Amoris (Eros)      : {eros['pozitie_text']:<25} | Casa: {casa_eros:02d}")
    coordonate_totale["Pars Eros"] = eros['lon_pura']

    # 4. Pars Necessitatis (Necesitate, Obligații, Lupte)
    # Diurn = Asc + Fortuna - Mercur | Nocturn = Asc + Mercur - Fortuna
    necesitate = calculeaza_punct_arab(l_asc, fortuna['lon_pura'], l_mercur, este_harta_diurna, formula_diurna_fixa=True)
    casa_necesitate = determina_casa_planetei(necesitate['lon_pura'], jd_ut_case)
    print(f"  - Pars Necessitatis       : {necesitate['pozitie_text']:<25} | Casa: {casa_necesitate:02d}")
    coordonate_totale["Pars Necesitate"] = necesitate['lon_pura']

    # 5. Pars Victoriae (Victorie, Curaj, Onoare, Încununare)
    # Diurn = Asc + Jupiter - Fortuna | Nocturn = Asc + Fortuna - Jupiter
    victorie = calculeaza_punct_arab(l_asc, l_jupiter, fortuna['lon_pura'], este_harta_diurna, formula_diurna_fixa=True)
    casa_victorie = determina_casa_planetei(victorie['lon_pura'], jd_ut_case)
    print(f"  - Pars Victoriae (Succes) : {victorie['pozitie_text']:<25} | Casa: {casa_victorie:02d}")
    coordonate_totale["Pars Victorie"] = victorie['lon_pura']

except Exception as e:
    print(f"  - Eroare la calculul complex al Punctelor Arabe: {e}")

# =====================================================================
# SECTIUNEA FINALA: EXPORTUL COMPLET IN FORMAT JSON PENTRU DASHBOARD
# =====================================================================
print("\n" + "=" * 60)
print("[EXPORT DATE - JSON EXTINS]")

# 1. Colectăm listele de ore planetare formatate curat ca text
ore_zi_json = []
for numar, planeta, start, end in ore_zi:
    ore_zi_json.append({"ora": numar, "planeta": planeta, "interval": f"{start.strftime('%H:%M:%S')} - {end.strftime('%H:%M:%S')}"})

ore_noapte_json = []
for numar, planeta, start, end in ore_noapte:
    ore_noapte_json.append({"ora": numar, "planeta": planeta, "interval": f"{start.strftime('%H:%M:%S')} - {end.strftime('%H:%M:%S')}"})

# 2. Re-colectăm textele formatate ale corpurilor (Zodii + Case + Mișcare)
# Pentru a nu strica nimic, interogăm rapid listele din memorie
corpuri_astrologice_text = {}
toate_grupurile_lucrate = [
    ("Planeta", planete_standard), 
    ("Punct Fictiv", puncte_fictive), 
    ("Asteroid", asteroizi), 
    ("Uraniana", uraniene),
    ("Stea Fixa", stele_fixe)
]

for tip, grup in toate_grupurile_lucrate:
    for nume, corp_id in grup.items():
        try:
            if tip == "Stea Fixa":
                p_data = calculeaza_stea_fixa(jd_et_planete, corp_id)
                numar_casa = determina_casa_planetei(p_data['lon_pura'], jd_ut_case)
                miscare_text = "Stabil"
            else:
                p_data = calculeaza_pozitie_astrologica(jd_et_planete, corp_id)
                numar_casa = determina_casa_planetei(p_data['lon_pura'], jd_ut_case)
                miscare_text = p_data['miscare']
                
            corpuri_astrologice_text[nume] = {
                "tip_obiect": tip,
                "text_zodiac": p_data['pozitie_text'],
                "numar_casa": f"{numar_casa:02d}",
                "miscare": miscare_text,
                "grad_brut": p_data['lon_pura']
            }
        except:
            pass

# Adăugăm Nodurile Sud și Punctele Arabe calculate manual în structura extinsă text
try:
    for n_nume in ["Nod Nord (Mean)", "Nod Nord (True)"]:
        if n_nume in coordonate_totale:
            tip_nod = "Mean" if "Mean" in n_nume else "True"
            lon_s = (coordonate_totale[n_nume] + 180.0) % 360.0
            corpuri_astrologice_text[f"Nod Sud ({tip_nod})"] = {
                "tip_obiect": "Punct Fictiv",
                "text_zodiac": format_pozitie_astrologica(lon_s),
                "numar_casa": f"{determina_casa_planetei(lon_s, jd_ut_case):02d}",
                "miscare": "Retrograd",
                "grad_brut": lon_s
            }
    
    puncte_arabe_nume = [
        ("Pars Fortunae", "Pars Fortunae (Noroc)"), 
        ("Pars Spiritus", "Pars Spiritus (Suflet)"), 
        ("Pars Eros", "Pars Amoris (Eros)"), 
        ("Pars Necesitate", "Pars Necessitatis"), 
        ("Pars Victorie", "Pars Victoriae (Succes)")
    ]
    for ch_json, nume_tinta_latina in puncte_arabe_nume:
        if ch_json in coordonate_totale:
            l_pure = coordonate_totale[ch_json]
            # Salvează direct cu numele curat în dicționarul JSON
            corpuri_astrologice_text[nume_tinta_latina] = {
                "tip_obiect": "Punct Arab",
                "text_zodiac": format_pozitie_astrologica(l_pure),
                "numar_casa": f"{determina_casa_planetei(l_pure, jd_ut_case):02d}",
                "miscare": "Direct",
                "grad_brut": l_pure
            }
except:
    pass

# 3. Structurăm MEGA-DICȚIONARUL complet pentru export
date_export_interfata = {
    "configurare": {
        "data_calcul_local": acum_local.strftime('%d-%m-%Y'),
        "ora_calcul_local": acum_local.strftime('%H:%M:%S'),
        "coordonate": {"lat": LATITUDINE, "lon": LONGITUDINE, "alt": ALTITUDINE}
    },
    "astronomice_baza": {
        "durata_zi": format_durata(durata_zi_ore),
        "durata_noapte": format_durata(durata_noapte_ore),
        "anotimp_nord": anotimp,
        "soare_pozitie_ecliptica": format_grade(lon_soare_acum)
    },
    "cronocrati": {
        "guvernator_zi": guvernator_zi.upper(),
        "guvernator_ora": guvernator_ora.upper(),
        "interval_ora_activa": interval_ora_curenta,
        "ore_zi_detaliat": ore_zi_json,
        "ore_noapte_detaliat": ore_noapte_json
    },
    "dinamica_luna": {
        "faza_curenta": date_luna_dinamica['faza'],
        "iluminare_procent": f"{date_luna_dinamica['iluminare']:.2f}%",
        "varsta_zile": f"{date_luna_dinamica['varsta']:.2f}",
        "arc_soli_lunar": format_grade(elongatie_act)
    },
    
    "axe_si_case_placidus": tabel_case,
    "obiecte_astrologice_detaliat": corpuri_astrologice_text,
    "aspecte_planetare_active": [linie.strip("- ") for linie in liste_imprimate],  # <- REPARAȚIE: Verifică să ai această virgulă aici!
    
    # Acestea se adaugă acum perfect în structura nativă
    "scoruri_forta_planete": scoruri_planete_json,
    "scor_cosmic_global": f"{scor_cosmic_global:.1f}%"
}


try:
    cale_fisier_json = os.path.join(cale_curenta, "date_dashboard.json")
    with open(cale_fisier_json, "w", encoding="utf-8") as f:
        json.dump(date_export_interfata, f, indent=4, ensure_ascii=False)
    print(f"  - Succes! Fișierul 'date_dashboard.json' extins a fost generat.")
except Exception as e:
    print(f"  - Eroare la scrierea fișierului JSON: {e}")

# Închiderea obligatorie a resurselor Swiss Ephemeris
swe.close()

