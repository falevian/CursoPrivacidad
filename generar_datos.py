"""
Generador de datasets sintéticos para prácticas del curso de Privacidad y Anonimización.
Datos basados en distribuciones reales del INE (España).

Genera 4 datasets diseñados para ilustrar los ataques y técnicas del curso:
1. dataset_principal.csv: Dataset central con muchos atributos para anonimización
2. dataset_hospital.csv: Datos sanitarios para ataques de inferencia (estilo k-anonimidad)
3. dataset_red_social.csv: Perfiles públicos para ataques de vinculabilidad
4. dataset_movilidad.csv: Trazas de localización (estilo Montjoye, 4 puntos)
"""

import numpy as np
import pandas as pd
import random
from datetime import datetime, timedelta
import string

# Semilla reproducible
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

N = 5000  # Tamaño del dataset principal

# =============================================================================
# DISTRIBUCIONES REALES (INE - España, 2023-2024)
# =============================================================================

# Nombres masculinos más frecuentes (INE - Top nombres España)
NOMBRES_HOMBRE = [
    ("Antonio", 660000), ("Manuel", 568000), ("José", 538000), ("Francisco", 491000),
    ("David", 392000), ("Juan", 367000), ("Javier", 320000), ("José Antonio", 252000),
    ("Daniel", 241000), ("Francisco Javier", 226000), ("José Luis", 224000),
    ("Carlos", 223000), ("Jesús", 219000), ("Alejandro", 217000), ("Miguel", 192000),
    ("Rafael", 175000), ("Pedro", 175000), ("Miguel Ángel", 174000), ("Ángel", 162000),
    ("Pablo", 158000), ("Sergio", 152000), ("José Manuel", 144000), ("Fernando", 138000),
    ("Jorge", 130000), ("Luis", 130000), ("Alberto", 126000), ("Álvaro", 121000),
    ("Adrián", 120000), ("Diego", 117000), ("Iván", 114000), ("Rubén", 102000),
    ("Mohamed", 98000), ("Andrés", 91000), ("Raúl", 89000), ("Enrique", 88000),
    ("Joaquín", 84000), ("Ramón", 79000), ("Vicente", 76000), ("Jaime", 73000),
    ("Roberto", 71000), ("Eduardo", 70000), ("Marcos", 68000), ("Víctor", 67000),
    ("Mario", 65000), ("Hugo", 64000), ("Ignacio", 62000), ("Gonzalo", 58000),
    ("Óscar", 57000), ("Cristian", 55000), ("Salvador", 53000),
]

NOMBRES_MUJER = [
    ("María Carmen", 590000), ("María", 553000), ("Carmen", 358000), ("Josefa", 274000),
    ("Ana María", 257000), ("Isabel", 251000), ("María Dolores", 247000), ("Laura", 246000),
    ("María Pilar", 232000), ("María Teresa", 220000), ("Ana", 220000), ("Cristina", 211000),
    ("Marta", 207000), ("Francisca", 199000), ("Antonia", 197000), ("María Ángeles", 195000),
    ("Dolores", 195000), ("María José", 184000), ("Lucía", 184000), ("Elena", 178000),
    ("Sara", 178000), ("Pilar", 174000), ("Paula", 168000), ("Raquel", 164000),
    ("Manuela", 162000), ("Rosa María", 160000), ("Mercedes", 158000), ("Concepción", 152000),
    ("Patricia", 152000), ("Beatriz", 145000), ("Andrea", 140000), ("Rosario", 138000),
    ("Sandra", 130000), ("Silvia", 126000), ("Inmaculada", 124000), ("Nuria", 116000),
    ("Yolanda", 110000), ("Eva", 109000), ("Alba", 108000), ("Rosa", 107000),
    ("Mónica", 104000), ("Julia", 102000), ("Natalia", 100000), ("Sofía", 96000),
    ("Irene", 95000), ("Fátima", 94000), ("Celia", 65000), ("Aitana", 60000),
    ("Daniela", 58000), ("Claudia", 57000),
]

# Apellidos más frecuentes (INE)
APELLIDOS = [
    ("García", 1462000), ("Rodríguez", 921000), ("González", 906000), ("Fernández", 879000),
    ("López", 874000), ("Martínez", 822000), ("Sánchez", 800000), ("Pérez", 776000),
    ("Gómez", 481000), ("Martín", 466000), ("Jiménez", 416000), ("Ruiz", 392000),
    ("Hernández", 376000), ("Díaz", 366000), ("Moreno", 357000), ("Muñoz", 314000),
    ("Álvarez", 309000), ("Romero", 251000), ("Alonso", 235000), ("Gutiérrez", 234000),
    ("Navarro", 231000), ("Torres", 226000), ("Domínguez", 217000), ("Vázquez", 215000),
    ("Ramos", 212000), ("Gil", 198000), ("Ramírez", 192000), ("Serrano", 190000),
    ("Blanco", 184000), ("Suárez", 174000), ("Molina", 172000), ("Morales", 168000),
    ("Ortega", 162000), ("Delgado", 161000), ("Castro", 153000), ("Ortiz", 152000),
    ("Rubio", 148000), ("Marín", 144000), ("Sanz", 140000), ("Núñez", 134000),
    ("Iglesias", 132000), ("Medina", 132000), ("Garrido", 130000), ("Cortés", 124000),
    ("Castillo", 124000), ("Santos", 124000), ("Lozano", 119000), ("Guerrero", 116000),
    ("Cano", 115000), ("Prieto", 113000), ("Méndez", 111000), ("Cruz", 110000),
    ("Calvo", 109000), ("Gallego", 108000), ("Vidal", 105000), ("León", 104000),
    ("Márquez", 102000), ("Herrera", 101000), ("Peña", 99000), ("Flores", 99000),
    ("Cabrera", 96000), ("Campos", 93000), ("Vega", 91000), ("Fuentes", 89000),
    ("Carrasco", 87000), ("Diez", 87000), ("Caballero", 86000), ("Reyes", 84000),
    ("Nieto", 82000), ("Aguilar", 80000), ("Pascual", 78000), ("Santana", 76000),
]

# Provincias y población (INE 2024)
PROVINCIAS = [
    ("Madrid", 6871903, "M"), ("Barcelona", 5714730, "B"), ("Valencia", 2683307, "V"),
    ("Sevilla", 1947852, "SE"), ("Alicante", 1948844, "A"), ("Málaga", 1750134, "MA"),
    ("Murcia", 1551692, "MU"), ("Cádiz", 1245960, "CA"), ("Vizcaya", 1162407, "BI"),
    ("A Coruña", 1120134, "C"), ("Las Palmas", 1180858, "GC"), ("Asturias", 1011792, "O"),
    ("Zaragoza", 988528, "Z"), ("Pontevedra", 945860, "PO"),
    ("Santa Cruz de Tenerife", 1052588, "TF"), ("Granada", 921472, "GR"),
    ("Tarragona", 832436, "T"), ("Girona", 786596, "GI"), ("Córdoba", 776819, "CO"),
    ("Toledo", 740534, "TO"), ("Almería", 743435, "AL"), ("Badajoz", 668023, "BA"),
    ("Jaén", 619544, "J"), ("Navarra", 671193, "NA"), ("Cantabria", 588387, "S"),
    ("Castellón", 597452, "CS"), ("Huelva", 526123, "H"), ("Valladolid", 519546, "VA"),
    ("Ciudad Real", 492591, "CR"), ("León", 446418, "LE"), ("Lleida", 449993, "L"),
    ("Cáceres", 387375, "CC"), ("Albacete", 388270, "AB"), ("Lugo", 326013, "LU"),
    ("Burgos", 358436, "BU"), ("La Rioja", 320667, "LO"), ("Salamanca", 326984, "SA"),
    ("Guipúzcoa", 729020, "SS"), ("Álava", 339180, "VI"), ("Ourense", 304934, "OR"),
    ("Huesca", 226270, "HU"), ("Zamora", 167215, "ZA"), ("Palencia", 158087, "P"),
    ("Ávila", 158421, "AV"), ("Cuenca", 196139, "CU"), ("Segovia", 159686, "SG"),
    ("Teruel", 134176, "TE"), ("Soria", 88884, "SO"), ("Ceuta", 83517, "CE"),
    ("Melilla", 86487, "ML"), ("Baleares", 1209906, "PM"),
]

# Códigos postales por provincia (rango aprox.) – simplificado
CP_PROVINCIA = {
    "Madrid": (28000, 28999), "Barcelona": (8000, 8999), "Valencia": (46000, 46999),
    "Sevilla": (41000, 41999), "Alicante": (3000, 3999), "Málaga": (29000, 29999),
    "Murcia": (30000, 30999), "Cádiz": (11000, 11999), "Vizcaya": (48000, 48999),
    "A Coruña": (15000, 15999), "Las Palmas": (35000, 35999), "Asturias": (33000, 33999),
    "Zaragoza": (50000, 50999), "Pontevedra": (36000, 36999),
    "Santa Cruz de Tenerife": (38000, 38999), "Granada": (18000, 18999),
    "Tarragona": (43000, 43999), "Girona": (17000, 17999), "Córdoba": (14000, 14999),
    "Toledo": (45000, 45999), "Almería": (4000, 4999), "Badajoz": (6000, 6999),
    "Jaén": (23000, 23999), "Navarra": (31000, 31999), "Cantabria": (39000, 39999),
    "Castellón": (12000, 12999), "Huelva": (21000, 21999), "Valladolid": (47000, 47999),
    "Ciudad Real": (13000, 13999), "León": (24000, 24999), "Lleida": (25000, 25999),
    "Cáceres": (10000, 10999), "Albacete": (2000, 2999), "Lugo": (27000, 27999),
    "Burgos": (9000, 9999), "La Rioja": (26000, 26999), "Salamanca": (37000, 37999),
    "Guipúzcoa": (20000, 20999), "Álava": (1000, 1999), "Ourense": (32000, 32999),
    "Huesca": (22000, 22999), "Zamora": (49000, 49999), "Palencia": (34000, 34999),
    "Ávila": (5000, 5999), "Cuenca": (16000, 16999), "Segovia": (40000, 40999),
    "Teruel": (44000, 44999), "Soria": (42000, 42999), "Ceuta": (51000, 51999),
    "Melilla": (52000, 52999), "Baleares": (7000, 7999),
}

# Nivel educativo (INE - población 25-64 años)
NIVEL_EDUCATIVO = [
    ("Sin estudios", 0.04),
    ("Primaria", 0.10),
    ("ESO/Secundaria obligatoria", 0.27),
    ("Bachillerato", 0.13),
    ("FP Grado Medio", 0.09),
    ("FP Grado Superior", 0.11),
    ("Grado universitario", 0.18),
    ("Máster/Posgrado", 0.07),
    ("Doctorado", 0.01),
]

# Estado civil (INE)
ESTADO_CIVIL = [
    ("Soltero/a", 0.42),
    ("Casado/a", 0.43),
    ("Divorciado/a", 0.08),
    ("Viudo/a", 0.06),
    ("Pareja de hecho", 0.01),
]

# Situación laboral
SITUACION_LABORAL = [
    ("Empleado por cuenta ajena", 0.62),
    ("Autónomo", 0.13),
    ("Desempleado", 0.10),
    ("Estudiante", 0.07),
    ("Jubilado", 0.06),
    ("Labores del hogar", 0.02),
]

# Ocupaciones (CNO simplificado) con salario medio (INE EES 2023)
OCUPACIONES = [
    ("Director/Gerente", 65000, 0.04),
    ("Profesional científico/intelectual", 38000, 0.16),
    ("Técnico", 32000, 0.12),
    ("Empleado contable/administrativo", 24000, 0.10),
    ("Trabajador servicios/comercio", 19000, 0.22),
    ("Trabajador agrario", 18000, 0.04),
    ("Artesano/industria", 22000, 0.09),
    ("Operador maquinaria/conductor", 23000, 0.08),
    ("Ocupación elemental", 16000, 0.13),
    ("Fuerzas armadas", 28000, 0.02),
]

# Nacionalidad (INE - extranjeros más frecuentes)
NACIONALIDAD = [
    ("Española", 0.875),
    ("Marroquí", 0.018),
    ("Rumana", 0.013),
    ("Colombiana", 0.010),
    ("Británica", 0.006),
    ("Italiana", 0.006),
    ("Venezolana", 0.006),
    ("Ucraniana", 0.005),
    ("China", 0.005),
    ("Ecuatoriana", 0.004),
    ("Búlgara", 0.003),
    ("Argentina", 0.003),
    ("Peruana", 0.003),
    ("Alemana", 0.003),
    ("Francesa", 0.003),
    ("Portuguesa", 0.002),
    ("Brasileña", 0.002),
    ("Polaca", 0.002),
    ("Otra", 0.031),
]

# Religión
RELIGION = [
    ("Católica", 0.55),
    ("No creyente/Ateo", 0.18),
    ("Agnóstico", 0.13),
    ("Otra cristiana", 0.04),
    ("Musulmana", 0.04),
    ("Otras", 0.03),
    ("Indiferente", 0.03),
]

# Orientación sexual (estimaciones FELGTBI+ y CIS)
ORIENTACION = [
    ("Heterosexual", 0.92),
    ("Homosexual", 0.03),
    ("Bisexual", 0.04),
    ("Otra", 0.01),
]

# =============================================================================
# FUNCIONES DE GENERACIÓN
# =============================================================================

def calcular_letra_dni(numero):
    """Calcula la letra de control del DNI."""
    letras = "TRWAGMYFPDXBNJZSQVHLCKE"
    return letras[int(numero) % 23]

def generar_dni():
    """Genera un DNI español válido (con letra de control correcta)."""
    numero = random.randint(10000000, 99999999)
    letra = calcular_letra_dni(numero)
    return f"{numero:08d}{letra}"

def generar_iban(banco_codigo=None):
    """Genera un IBAN español sintético con dígitos de control coherentes."""
    if banco_codigo is None:
        banco_codigo = random.choice(["0049", "2100", "0081", "0182", "1465", "0075", "2038", "3025"])
    sucursal = f"{random.randint(0, 9999):04d}"
    cuenta = f"{random.randint(0, 9999999999):010d}"
    bban = banco_codigo + sucursal + cuenta
    # Dígitos de control IBAN (mod 97)
    # ES = 142814 (E=14, S=28 -> 1428)
    rearranged = bban + "142800"
    check = 98 - (int(rearranged) % 97)
    return f"ES{check:02d}{banco_codigo} {sucursal} {cuenta[:2]} {cuenta[2:]}"

def generar_telefono():
    """Genera un teléfono móvil/fijo español."""
    if random.random() < 0.75:
        # Móvil
        prefijo = random.choice(["6", "7"])
        return f"+34 {prefijo}{random.randint(10, 99)} {random.randint(100, 999)} {random.randint(100, 999)}"
    else:
        # Fijo
        prefijo = random.choice(["91", "93", "96", "94", "95", "98", "97"])
        return f"+34 {prefijo}{random.randint(1000000, 9999999)}"

def generar_email(nombre, apellido):
    """Genera un email plausible."""
    dominios = ["gmail.com", "gmail.com", "gmail.com", "hotmail.com", "hotmail.com",
                "yahoo.es", "outlook.com", "outlook.es", "telefonica.net", "movistar.es", "icloud.com"]
    nombre_limpio = nombre.lower().replace(" ", "").replace("ñ", "n").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    apellido_limpio = apellido.lower().replace(" ", "").replace("ñ", "n").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    formatos = [
        f"{nombre_limpio}.{apellido_limpio}",
        f"{nombre_limpio}{apellido_limpio}",
        f"{nombre_limpio[0]}{apellido_limpio}",
        f"{nombre_limpio}.{apellido_limpio}{random.randint(1, 99)}",
        f"{nombre_limpio}_{apellido_limpio}",
    ]
    usuario = random.choice(formatos)
    return f"{usuario}@{random.choice(dominios)}"

def muestrear(opciones):
    """Muestrea una opción según pesos."""
    items = [x[0] for x in opciones]
    pesos = np.array([x[1] for x in opciones], dtype=float)
    pesos = pesos / pesos.sum()
    return np.random.choice(items, p=pesos)

def muestrear_multi(opciones, n):
    """Muestreo masivo."""
    items = [x[0] for x in opciones]
    pesos = np.array([x[1] for x in opciones], dtype=float)
    pesos = pesos / pesos.sum()
    return np.random.choice(items, size=n, p=pesos)

def generar_altura(sexo):
    """Altura siguiendo distribución real (INE/ENSE 2017). Hombres: 173.1±7.5; Mujeres: 160.4±6.5."""
    if sexo == "M":
        return round(np.clip(np.random.normal(173.1, 7.5), 145, 210), 1)
    else:
        return round(np.clip(np.random.normal(160.4, 6.5), 140, 195), 1)

def generar_peso(altura, sexo, edad):
    """Peso correlacionado con altura, sexo y edad. IMC medio España: 26.1 H, 25.0 M."""
    altura_m = altura / 100
    if sexo == "M":
        imc_base = 23.5 + 0.05 * (edad - 18)
    else:
        imc_base = 22.0 + 0.06 * (edad - 18)
    imc = np.clip(np.random.normal(imc_base, 3.5), 16, 45)
    peso = imc * altura_m ** 2
    return round(peso, 1)

def generar_edad(n):
    """Pirámide poblacional España (aproximación INE 2024)."""
    grupos = [
        ((0, 14), 0.135),
        ((15, 24), 0.103),
        ((25, 34), 0.118),
        ((35, 44), 0.155),
        ((45, 54), 0.165),
        ((55, 64), 0.137),
        ((65, 74), 0.106),
        ((75, 84), 0.060),
        ((85, 99), 0.021),
    ]
    edades = []
    pesos = np.array([g[1] for g in grupos])
    pesos = pesos / pesos.sum()
    for _ in range(n):
        idx = np.random.choice(len(grupos), p=pesos)
        rango = grupos[idx][0]
        edades.append(random.randint(rango[0], rango[1]))
    return edades

def generar_fecha_nacimiento(edad):
    """Genera fecha de nacimiento dada una edad."""
    hoy = datetime(2026, 4, 29)
    año = hoy.year - edad
    dias_offset = random.randint(0, 364)
    fecha = datetime(año, 1, 1) + timedelta(days=dias_offset)
    if fecha > hoy.replace(year=año):
        fecha = fecha - timedelta(days=365)
    return fecha.strftime("%Y-%m-%d")

# =============================================================================
# DATASET 1: PRINCIPAL (clientes de una empresa ficticia)
# =============================================================================

def generar_dataset_principal(n=N):
    print(f"Generando dataset principal con {n} registros...")
    
    edades = generar_edad(n)
    sexos = np.random.choice(["M", "F"], size=n, p=[0.49, 0.51])
    
    # Provincias ponderadas por población
    prov_items = [p[0] for p in PROVINCIAS]
    prov_pesos = np.array([p[1] for p in PROVINCIAS], dtype=float)
    prov_pesos = prov_pesos / prov_pesos.sum()
    provincias = np.random.choice(prov_items, size=n, p=prov_pesos)
    
    registros = []
    for i in range(n):
        edad = edades[i]
        sexo = sexos[i]
        provincia = provincias[i]
        
        # Nombre según sexo (frecuencia real)
        if sexo == "M":
            nombre = muestrear(NOMBRES_HOMBRE)
        else:
            nombre = muestrear(NOMBRES_MUJER)
        
        apellido1 = muestrear(APELLIDOS)
        apellido2 = muestrear(APELLIDOS)
        
        altura = generar_altura(sexo)
        peso = generar_peso(altura, sexo, edad)
        imc = round(peso / ((altura/100) ** 2), 2)
        
        nivel_edu = muestrear(NIVEL_EDUCATIVO)
        
        # Estado civil correlacionado con edad
        if edad < 20:
            ec = "Soltero/a"
        elif edad < 30:
            ec = np.random.choice(["Soltero/a", "Casado/a", "Pareja de hecho"], p=[0.78, 0.18, 0.04])
        elif edad < 50:
            ec = np.random.choice(["Soltero/a", "Casado/a", "Divorciado/a", "Pareja de hecho"], p=[0.30, 0.55, 0.13, 0.02])
        elif edad < 70:
            ec = np.random.choice(["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a"], p=[0.12, 0.65, 0.15, 0.08])
        else:
            ec = np.random.choice(["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a"], p=[0.05, 0.50, 0.10, 0.35])
        
        # Situación laboral correlacionada con edad
        if edad < 16:
            sit_lab = "Estudiante"
            ocupacion = "N/A"
            salario = 0
        elif edad < 25:
            sit_lab = np.random.choice(["Estudiante", "Empleado por cuenta ajena", "Desempleado"], p=[0.55, 0.30, 0.15])
        elif edad < 65:
            sit_lab = muestrear(SITUACION_LABORAL)
            if sit_lab == "Estudiante":
                sit_lab = "Empleado por cuenta ajena"
        else:
            sit_lab = np.random.choice(["Jubilado", "Empleado por cuenta ajena", "Labores del hogar"], p=[0.85, 0.05, 0.10])
        
        # Ocupación y salario
        if sit_lab in ["Empleado por cuenta ajena", "Autónomo"]:
            ocup_idx = np.random.choice(len(OCUPACIONES), p=[o[2] for o in OCUPACIONES])
            ocupacion, salario_base, _ = OCUPACIONES[ocup_idx]
            # Salario con variabilidad lognormal
            salario = round(np.random.lognormal(np.log(salario_base), 0.3), 0)
            # Ajuste por nivel educativo
            mult_edu = {"Doctorado": 1.6, "Máster/Posgrado": 1.3, "Grado universitario": 1.15,
                       "FP Grado Superior": 1.0, "FP Grado Medio": 0.9, "Bachillerato": 0.85,
                       "ESO/Secundaria obligatoria": 0.75, "Primaria": 0.65, "Sin estudios": 0.55}
            salario = round(salario * mult_edu.get(nivel_edu, 1.0), 0)
            # Ajuste por provincia (Madrid/BCN +20%, otras zonas)
            if provincia in ["Madrid", "Barcelona"]:
                salario = round(salario * 1.20, 0)
            elif provincia in ["Vizcaya", "Guipúzcoa", "Navarra"]:
                salario = round(salario * 1.10, 0)
            elif provincia in ["Cádiz", "Huelva", "Badajoz", "Almería", "Ceuta", "Melilla"]:
                salario = round(salario * 0.85, 0)
            # Ajuste por sexo (brecha salarial INE 2023: ~18%)
            if sexo == "F":
                salario = round(salario * 0.82, 0)
            # Ajuste por edad (curva de carrera)
            if edad < 30:
                salario = round(salario * 0.75, 0)
            elif edad > 50:
                salario = round(salario * 1.15, 0)
        elif sit_lab == "Jubilado":
            ocupacion = "Jubilado"
            salario = round(np.random.normal(15500, 4500), 0)
            salario = max(8000, salario)
        elif sit_lab == "Desempleado":
            ocupacion = "Desempleado"
            salario = round(np.random.normal(7200, 2000), 0) if random.random() < 0.6 else 0
            salario = max(0, salario)
        else:
            ocupacion = sit_lab
            salario = 0
        
        # Nacionalidad
        nacionalidad = muestrear(NACIONALIDAD)
        
        # CP
        cp_min, cp_max = CP_PROVINCIA.get(provincia, (28000, 28999))
        cp = f"{random.randint(cp_min, cp_max):05d}"
        
        # Información sensible adicional
        religion = muestrear(RELIGION)
        orientacion = muestrear(ORIENTACION)
        
        # DNI/teléfono/email/IBAN
        dni = generar_dni() if nacionalidad == "Española" else f"X{random.randint(1000000, 9999999):07d}{random.choice(string.ascii_uppercase)}"
        telefono = generar_telefono()
        email = generar_email(nombre.split()[0], apellido1)
        iban = generar_iban()
        
        # Datos de salud (correlacionados)
        diabetes = 1 if (imc > 30 and random.random() < 0.18) or (edad > 60 and random.random() < 0.12) or random.random() < 0.04 else 0
        hipertension = 1 if (edad > 50 and random.random() < 0.40) or (imc > 28 and random.random() < 0.20) or random.random() < 0.06 else 0
        colesterol = round(np.random.normal(195 + 0.5 * edad, 35), 0)
        tabaquismo = 1 if random.random() < (0.32 if sexo == "M" else 0.22) else 0
        alcohol_semana = max(0, round(np.random.exponential(5 if sexo == "M" else 2.5), 1))
        
        # Salud mental
        ansiedad = 1 if random.random() < (0.085 if sexo == "F" else 0.045) else 0
        depresion = 1 if random.random() < (0.07 if sexo == "F" else 0.035) else 0
        
        # Comportamiento (uso digital, hábitos)
        horas_internet_dia = round(np.clip(np.random.normal(4.5, 1.8), 0, 16), 1)
        if edad > 65:
            horas_internet_dia = round(horas_internet_dia * 0.4, 1)
        elif edad < 25:
            horas_internet_dia = round(horas_internet_dia * 1.4, 1)
        
        gasto_mensual_online = round(np.random.lognormal(np.log(150), 0.8), 2)
        if salario < 15000:
            gasto_mensual_online = round(gasto_mensual_online * 0.4, 2)
        
        # Variables financieras
        tiene_hipoteca = 1 if (edad > 28 and salario > 18000 and random.random() < 0.45) else 0
        deuda_total = round(max(0, np.random.lognormal(np.log(8000), 1.5)) if random.random() < 0.5 else 0, 0)
        if tiene_hipoteca:
            deuda_total += round(np.random.normal(120000, 50000), 0)
            deuda_total = max(20000, deuda_total)
        
        # Vehículo
        tiene_coche = 1 if random.random() < (0.35 if edad < 25 else 0.78) else 0
        
        # Hijos
        if edad < 22:
            num_hijos = 0
        elif edad < 35:
            num_hijos = np.random.choice([0, 1, 2], p=[0.55, 0.30, 0.15])
        elif edad < 55:
            num_hijos = np.random.choice([0, 1, 2, 3, 4], p=[0.18, 0.27, 0.40, 0.12, 0.03])
        else:
            num_hijos = np.random.choice([0, 1, 2, 3, 4, 5], p=[0.10, 0.18, 0.45, 0.18, 0.06, 0.03])
        
        # Cuenta de usuario y contraseña
        usuario = email.split("@")[0]
        # Hash de contraseña simulado (no real, sólo para que tenga aspecto)
        password_hash = ''.join(random.choices(string.hexdigits.lower(), k=64))
        
        registros.append({
            "id_cliente": f"C{i+1:06d}",
            "dni": dni,
            "nombre": nombre,
            "apellido1": apellido1,
            "apellido2": apellido2,
            "sexo": sexo,
            "fecha_nacimiento": generar_fecha_nacimiento(edad),
            "edad": edad,
            "nacionalidad": nacionalidad,
            "estado_civil": ec,
            "num_hijos": int(num_hijos),
            "telefono": telefono,
            "email": email,
            "usuario": usuario,
            "password_hash_sha256": password_hash,
            "direccion": f"C/ {muestrear(APELLIDOS)} {random.randint(1, 200)}, {random.randint(1,7)}º{random.choice('ABCDE')}",
            "codigo_postal": cp,
            "ciudad": provincia,
            "provincia": provincia,
            "pais": "España" if nacionalidad == "Española" else nacionalidad,
            "altura_cm": altura,
            "peso_kg": peso,
            "imc": imc,
            "nivel_educativo": nivel_edu,
            "situacion_laboral": sit_lab,
            "ocupacion": ocupacion,
            "salario_anual_euros": int(salario),
            "iban": iban,
            "tiene_hipoteca": tiene_hipoteca,
            "deuda_total_euros": int(deuda_total),
            "tiene_coche": tiene_coche,
            "religion": religion,
            "orientacion_sexual": orientacion,
            "diabetes": diabetes,
            "hipertension": hipertension,
            "colesterol_mgdl": int(colesterol),
            "fumador": tabaquismo,
            "consumo_alcohol_ud_semana": alcohol_semana,
            "ansiedad_diagnosticada": ansiedad,
            "depresion_diagnosticada": depresion,
            "horas_internet_dia": horas_internet_dia,
            "gasto_mensual_online_euros": gasto_mensual_online,
            "fecha_alta_cliente": (datetime(2018, 1, 1) + timedelta(days=random.randint(0, 2700))).strftime("%Y-%m-%d"),
        })
    
    df = pd.DataFrame(registros)
    return df

# =============================================================================
# DATASET 2: HOSPITAL (para k-anonimidad y l-diversidad)
# =============================================================================

ENFERMEDADES = [
    ("Gripe", 0.20),
    ("Hipertensión", 0.13),
    ("Diabetes tipo 2", 0.09),
    ("Asma", 0.07),
    ("Depresión", 0.07),
    ("Ansiedad", 0.07),
    ("Cáncer de mama", 0.04),
    ("Cáncer de próstata", 0.03),
    ("Cáncer colorrectal", 0.03),
    ("VIH", 0.015),
    ("Hepatitis C", 0.01),
    ("Esquizofrenia", 0.012),
    ("Trastorno bipolar", 0.012),
    ("Alzheimer", 0.025),
    ("Parkinson", 0.015),
    ("Artritis", 0.04),
    ("Migraña", 0.05),
    ("Dermatitis", 0.04),
    ("Bronquitis", 0.03),
    ("Trastorno alimentario", 0.018),
    ("Adicción al alcohol", 0.022),
    ("Adicción a sustancias", 0.012),
    ("Infección urinaria", 0.04),
    ("Embarazo", 0.025),
    ("ITS - Clamidia", 0.013),
    ("ITS - Gonorrea", 0.008),
]

def generar_dataset_hospital(df_principal):
    """Subset de pacientes para ataques de inferencia tipo k-anonimidad."""
    print("Generando dataset hospital...")
    df = df_principal.sample(n=2500, random_state=SEED).copy()
    
    # Sólo cuasi-identificadores y atributo sensible
    enfermedades = []
    for _, row in df.iterrows():
        edad = row["edad"]
        sexo = row["sexo"]
        
        # Probabilidades condicionadas
        if sexo == "F" and 30 <= edad <= 50 and random.random() < 0.06:
            enf = "Embarazo"
        elif sexo == "F" and edad >= 45 and random.random() < 0.07:
            enf = "Cáncer de mama"
        elif sexo == "M" and edad >= 55 and random.random() < 0.08:
            enf = "Cáncer de próstata"
        elif edad >= 70 and random.random() < 0.20:
            enf = np.random.choice(["Alzheimer", "Parkinson", "Hipertensión", "Diabetes tipo 2"], p=[0.25, 0.15, 0.30, 0.30])
        elif edad < 30 and random.random() < 0.15:
            enf = np.random.choice(["Gripe", "Asma", "Migraña", "Ansiedad", "Dermatitis", "ITS - Clamidia"], p=[0.30, 0.20, 0.15, 0.15, 0.10, 0.10])
        else:
            enf = muestrear(ENFERMEDADES)
        enfermedades.append(enf)
    
    df_hosp = pd.DataFrame({
        "id_paciente": [f"P{i+1:05d}" for i in range(len(df))],
        "fecha_nacimiento": df["fecha_nacimiento"].values,
        "edad": df["edad"].values,
        "sexo": df["sexo"].values,
        "codigo_postal": df["codigo_postal"].values,
        "nacionalidad": df["nacionalidad"].values,
        "fecha_ingreso": [(datetime(2024, 1, 1) + timedelta(days=random.randint(0, 700))).strftime("%Y-%m-%d") for _ in range(len(df))],
        "diagnostico": enfermedades,
        "dias_hospitalizacion": [int(np.clip(np.random.exponential(3.5), 0, 60)) for _ in range(len(df))],
        "coste_tratamiento_euros": [int(np.random.lognormal(np.log(800), 1.1)) for _ in range(len(df))],
    })
    
    return df_hosp

# =============================================================================
# DATASET 3: RED SOCIAL (para vinculabilidad estilo Netflix/IMDB)
# =============================================================================

def generar_dataset_red_social(df_principal):
    """Perfiles públicos parciales — muchos campos del principal en clave para vincular.
    
    IMPORTANTE PARA EL CURSO:
    - El fichero PÚBLICO (03_dataset_red_social.csv) NO incluye id_cliente.
    - El fichero SOLUCIÓN (03b_solucion_vinculacion.csv) SÍ incluye el mapeo
      username -> id_cliente para que el profesor pueda verificar los ataques.
    """
    print("Generando dataset red social...")
    
    # Solo el 75% de los usuarios del principal tienen perfil en la red
    df = df_principal.sample(frac=0.75, random_state=SEED+1).copy().reset_index(drop=True)
    
    # Generar usernames y datos visibles
    usernames = []
    for _, row in df.iterrows():
        n = row["nombre"].split()[0].lower().replace(" ", "")
        a = row["apellido1"].lower()
        formato = random.choice([
            f"{n}{a}{random.randint(1, 999)}",
            f"{n}_{a}",
            f"{n[0]}{a}{random.randint(70, 99)}",
            f"{a}.{n}",
            f"{n}{random.randint(1980, 2010)}",
        ])
        for c in "áéíóúñ":
            formato = formato.replace(c, {"á":"a","é":"e","í":"i","ó":"o","ú":"u","ñ":"n"}[c])
        usernames.append(formato)
    
    # Películas favoritas (ataque estilo Netflix prize)
    peliculas = ["El Padrino", "Pulp Fiction", "El Señor de los Anillos", "Matrix", "Forrest Gump",
                 "Casablanca", "Ciudadano Kane", "Vértigo", "Psicosis", "Interestelar",
                 "El Club de la Lucha", "Origen", "Gladiator", "Titanic", "Shrek",
                 "Toy Story", "Buscando a Nemo", "El Rey León", "Frozen", "Coco",
                 "Avengers", "Star Wars", "Harry Potter", "El Hobbit", "Mad Max",
                 "Joker", "Parásitos", "El laberinto del fauno", "Mar adentro", "Volver",
                 "Campeones", "Ocho apellidos vascos", "Padre no hay más que uno", "La piel que habito",
                 "Roma", "Amélie", "La la land", "Whiplash", "Scarface", "Goodfellas"]
    
    registros = []
    for idx, (_, row) in enumerate(df.iterrows()):
        # Películas valoradas (5 a 30, con sesgo)
        n_pelis = random.randint(5, 30)
        seleccion = random.sample(peliculas, min(n_pelis, len(peliculas)))
        valoraciones = []
        for p in seleccion:
            rating = round(np.clip(np.random.normal(7.5, 1.5), 1, 10), 1)
            fecha = (datetime(2023, 1, 1) + timedelta(days=random.randint(0, 1000))).strftime("%Y-%m-%d")
            valoraciones.append(f"{p}|{rating}|{fecha}")
        
        # Posts revelando ubicación aproximada y edad
        ciudad = row["provincia"]
        
        registros.append({
            "username": usernames[idx],
            "nombre_publico": row["nombre"].split()[0] + " " + row["apellido1"][0] + ".",
            "ciudad": ciudad,
            "edad_aprox": row["edad"] + random.randint(-2, 2),  # ruido en edad
            "sexo": row["sexo"],
            "biografia": random.choice([
                f"Apasionado de {random.choice(['cine', 'música', 'deportes', 'viajes', 'lectura'])}",
                f"{ciudad} | {row['ocupacion'][:20] if row['ocupacion'] != 'N/A' else 'estudiante'}",
                f"Vivo en {ciudad}",
                "🎬 📚 ✈️",
                f"Nacido en {row['fecha_nacimiento'][:4]}",
                "",
            ]),
            "fecha_registro": (datetime(2015, 1, 1) + timedelta(days=random.randint(0, 3500))).strftime("%Y-%m-%d"),
            "num_seguidores": int(np.random.lognormal(np.log(150), 1.5)),
            "num_siguiendo": int(np.random.lognormal(np.log(200), 1.2)),
            "num_posts": random.randint(0, 5000),
            "peliculas_valoradas": "; ".join(valoraciones),
            "perfil_verificado": 1 if random.random() < 0.03 else 0,
            "perfil_publico": 1 if random.random() < 0.78 else 0,
        })
    
    return pd.DataFrame(registros)

# =============================================================================
# DATASET 4: MOVILIDAD (CDR - estilo Montjoye, 4 puntos para identificar)
# =============================================================================

def generar_dataset_movilidad(df_principal, n_users=1500):
    """Trazas de localización para ataques de unicity (4 puntos identifican al 95%)."""
    print("Generando dataset movilidad...")
    
    df = df_principal.sample(n=n_users, random_state=SEED+2).copy()
    
    # Coordenadas aproximadas de provincias (centro)
    coords_prov = {
        "Madrid": (40.42, -3.70), "Barcelona": (41.39, 2.17), "Valencia": (39.47, -0.38),
        "Sevilla": (37.39, -5.99), "Alicante": (38.35, -0.49), "Málaga": (36.72, -4.42),
        "Murcia": (37.99, -1.13), "Cádiz": (36.53, -6.30), "Vizcaya": (43.26, -2.93),
        "A Coruña": (43.36, -8.41), "Las Palmas": (28.12, -15.43), "Asturias": (43.36, -5.85),
        "Zaragoza": (41.65, -0.89), "Pontevedra": (42.43, -8.65),
        "Santa Cruz de Tenerife": (28.47, -16.25), "Granada": (37.18, -3.60),
        "Tarragona": (41.12, 1.25), "Girona": (41.98, 2.82), "Córdoba": (37.88, -4.78),
        "Toledo": (39.86, -4.02), "Almería": (36.84, -2.46), "Badajoz": (38.88, -6.97),
        "Jaén": (37.77, -3.79), "Navarra": (42.81, -1.65), "Cantabria": (43.46, -3.81),
        "Castellón": (39.99, -0.05), "Huelva": (37.26, -6.95), "Valladolid": (41.65, -4.73),
        "Ciudad Real": (38.99, -3.93), "León": (42.60, -5.57), "Lleida": (41.62, 0.62),
        "Cáceres": (39.47, -6.37), "Albacete": (38.99, -1.85), "Lugo": (43.01, -7.56),
        "Burgos": (42.34, -3.70), "La Rioja": (42.46, -2.45), "Salamanca": (40.97, -5.66),
        "Guipúzcoa": (43.32, -1.98), "Álava": (42.85, -2.67), "Ourense": (42.34, -7.86),
        "Huesca": (42.14, -0.41), "Zamora": (41.50, -5.75), "Palencia": (42.01, -4.53),
        "Ávila": (40.66, -4.68), "Cuenca": (40.07, -2.13), "Segovia": (40.95, -4.12),
        "Teruel": (40.34, -1.11), "Soria": (41.76, -2.47), "Ceuta": (35.89, -5.32),
        "Melilla": (35.29, -2.94), "Baleares": (39.57, 2.65),
    }
    
    todas_filas = []
    for _, row in df.iterrows():
        prov = row["provincia"]
        lat0, lon0 = coords_prov.get(prov, (40.42, -3.70))
        
        # 3 ubicaciones recurrentes (casa, trabajo, otra)
        casa = (lat0 + np.random.normal(0, 0.03), lon0 + np.random.normal(0, 0.03))
        trabajo = (lat0 + np.random.normal(0, 0.05), lon0 + np.random.normal(0, 0.05))
        ocio = (lat0 + np.random.normal(0, 0.04), lon0 + np.random.normal(0, 0.04))
        
        # 2 meses de datos, 1 punto cada hora aprox.
        n_eventos = random.randint(80, 250)
        fecha_base = datetime(2025, 9, 1)
        
        for ev in range(n_eventos):
            ts = fecha_base + timedelta(hours=ev*random.randint(2,8), minutes=random.randint(0, 59))
            hora = ts.hour
            
            # Probabilidad de ubicación según hora
            if 0 <= hora < 8 or hora >= 22:
                lat, lon = casa
                lugar = "casa"
            elif 9 <= hora < 18 and ts.weekday() < 5:
                lat, lon = trabajo
                lugar = "trabajo"
            else:
                lat, lon = ocio
                lugar = "ocio"
            
            # Añadir ruido (precisión de antena ~300m)
            lat += np.random.normal(0, 0.003)
            lon += np.random.normal(0, 0.003)
            
            todas_filas.append({
                "id_anonimo": row["id_cliente"],  # mismo ID que principal (para vincular)
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "fecha": ts.strftime("%Y-%m-%d"),
                "hora": hora,
                "latitud": round(lat, 5),
                "longitud": round(lon, 5),
                "tipo_evento": random.choice(["llamada", "sms", "datos", "datos", "datos"]),
                "duracion_seg": random.randint(0, 600) if random.random() < 0.3 else 0,
                "antena_id": f"BTS_{abs(hash(f'{round(lat,2)}_{round(lon,2)}')) % 10000:04d}",
            })
    
    return pd.DataFrame(todas_filas)

# =============================================================================
# EJECUCIÓN
# =============================================================================

if __name__ == "__main__":
    df_main = generar_dataset_principal(N)
    df_hosp = generar_dataset_hospital(df_main)
    df_social = generar_dataset_red_social(df_main)
    df_mov = generar_dataset_movilidad(df_main, 1500)
    
    out = "/home/claude/datos_curso"
    df_main.to_csv(f"{out}/01_dataset_principal.csv", index=False, encoding="utf-8")
    df_hosp.to_csv(f"{out}/02_dataset_hospital.csv", index=False, encoding="utf-8")
    df_social.to_csv(f"{out}/03_dataset_red_social.csv", index=False, encoding="utf-8")
    df_mov.to_csv(f"{out}/04_dataset_movilidad.csv", index=False, encoding="utf-8")
    
    # Fichero de solución (mapeo username -> id_cliente para que el profesor verifique ataques)
    df_main_subset = df_main.sample(frac=0.75, random_state=SEED+1).reset_index(drop=True)
    df_solucion = pd.DataFrame({
        "username": df_social["username"].values,
        "id_cliente_real": df_main_subset["id_cliente"].values,
        "dni_real": df_main_subset["dni"].values,
        "nombre_completo_real": df_main_subset["nombre"] + " " + df_main_subset["apellido1"] + " " + df_main_subset["apellido2"],
    })
    df_solucion.to_csv(f"{out}/SOLUCION_vinculacion_red_social.csv", index=False, encoding="utf-8")
    
    print("\n=== RESUMEN ===")
    print(f"Dataset principal: {len(df_main)} registros, {len(df_main.columns)} columnas")
    print(f"Dataset hospital:  {len(df_hosp)} registros, {len(df_hosp.columns)} columnas")
    print(f"Dataset red social:{len(df_social)} registros, {len(df_social.columns)} columnas")
    print(f"Dataset movilidad: {len(df_mov)} registros, {len(df_mov.columns)} columnas")
    print(f"Solución vinculación: {len(df_solucion)} registros")
    print(f"\nEdad media (principal): {df_main['edad'].mean():.1f}")
    print(f"% Mujeres: {(df_main['sexo']=='F').mean()*100:.1f}%")
    print(f"Salario medio (empleados): {df_main[df_main['situacion_laboral'].isin(['Empleado por cuenta ajena','Autónomo'])]['salario_anual_euros'].mean():,.0f} €")
    print(f"\nAltura media H: {df_main[df_main['sexo']=='M']['altura_cm'].mean():.1f} cm")
    print(f"Altura media F: {df_main[df_main['sexo']=='F']['altura_cm'].mean():.1f} cm")
    print(f"\nTop 5 nombres:")
    print(df_main['nombre'].value_counts().head().to_string())
    print(f"\nTop 5 apellidos:")
    print(df_main['apellido1'].value_counts().head().to_string())
    print(f"\nTop 5 diagnósticos:")
    print(df_hosp['diagnostico'].value_counts().head().to_string())
    
    # Verificar k-anonimidad sobre cuasi-identificadores en hospital
    print("\n=== ANÁLISIS k-ANONIMIDAD (Hospital) ===")
    qid = ["edad", "sexo", "codigo_postal"]
    grupos = df_hosp.groupby(qid).size()
    print(f"Combinaciones únicas de QID: {len(grupos)}")
    print(f"Registros con k=1 (identificables): {(grupos == 1).sum()} ({(grupos == 1).sum() / len(grupos) * 100:.1f}%)")
    print(f"Registros con k<=3: {(grupos <= 3).sum()}")
    print(f"k mediano: {grupos.median()}")
    
    # Verificar unicidad por movilidad (4 puntos como Montjoye)
    print("\n=== ANÁLISIS UNICITY (Movilidad) ===")
    df_mov_sample = df_mov.copy()
    df_mov_sample["punto"] = df_mov_sample["antena_id"].astype(str) + "_" + df_mov_sample["fecha"]
    puntos_por_user = df_mov_sample.groupby("id_anonimo")["punto"].apply(lambda x: tuple(sorted(set(x))[:4]))
    unicos = puntos_por_user.duplicated(keep=False) == False
    print(f"Usuarios identificables con 4 puntos: {unicos.sum()} de {len(puntos_por_user)} ({unicos.sum()/len(puntos_por_user)*100:.1f}%)")
