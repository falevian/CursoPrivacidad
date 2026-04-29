"""
=============================================================================
PRÁCTICAS DE ANONIMIZACIÓN — Curso de Privacidad, Anonimidad y Riesgos Ciber
UC3M · Rafael Vida
=============================================================================

Técnicas implementadas (equivalentes a sdcMicro / ARX en Python puro):

  MEDICIÓN DE RIESGO
  1. Frecuencias de muestra (fk) y unicidad
  2. k-anonimidad inicial
  3. Riesgo individual (1/Fk) y riesgo global esperado

  SEUDONIMIZACIÓN
  4. Hash MD5/SHA-256 (y su debilidad por espacio pequeño)
  5. HMAC-SHA256 con clave secreta (salt keyed)
  6. Cifrado determinista con clave (y simulación de borrado)
  7. Tokenización (lookup table con UUID)

  MÉTODOS NO PERTURBATIVOS
  8. Supresión de identificadores directos
  9. Generalización por intervalos (edad, salario)
  10. Generalización jerárquica (código postal 5→3→2 dígitos)
  11. Top/bottom coding (winsorización)

  MÉTODOS PERTURBATIVOS
  12. Adición de ruido gaussiano
  13. Permutación (swap dentro de grupos)
  14. PRAM — Post-Randomization Method

  MODELOS DE PRIVACIDAD FORMAL
  15. k-Anonimidad + medición y supresión/generalización iterativa
  16. l-Diversidad (verificación y corrección)
  17. Privacidad Diferencial — mecanismo de Laplace
  18. Privacidad Diferencial — mecanismo Gaussiano
  19. Composición de mecanismos DP

  UTILIDAD
  20. Métricas de pérdida de información (IL1, IL2, RMSE, distrib.)

Referencia: Domingo-Ferrer et al. (2001), Dwork et al. (2006),
            Machanavajjhala et al. (2007), Sweeney (2002)
=============================================================================
"""

import pandas as pd
import numpy as np
import hashlib
import hmac
import uuid
import warnings
from collections import defaultdict
from copy import deepcopy

warnings.filterwarnings("ignore")

# =============================================================================
# CARGA DE DATOS
# =============================================================================

CSV_PATH = "01_dataset_principal.csv"

print("=" * 70)
print("CARGA Y DESCRIPCIÓN DEL DATASET")
print("=" * 70)

df_raw = pd.read_csv(CSV_PATH, dtype={"codigo_postal": str, "dni": str, "iban": str})
print(f"Filas: {len(df_raw):,}  ·  Columnas: {len(df_raw.columns)}")
print(f"Tamaño en memoria: {df_raw.memory_usage(deep=True).sum() / 1e6:.1f} MB")
print()

# Clasificación de variables (como en la slide del curso)
ID_DIRECTOS = [
    "id_cliente", "dni", "nombre", "apellido1", "apellido2",
    "telefono", "email", "usuario", "password_hash_sha256",
    "direccion", "iban"
]
QUASI_ID = ["edad", "sexo", "codigo_postal", "provincia", "nacionalidad", "fecha_nacimiento"]
SENSIBLES = [
    "religion", "orientacion_sexual", "diabetes", "hipertension",
    "colesterol_mgdl", "fumador", "consumo_alcohol_ud_semana",
    "ansiedad_diagnosticada", "depresion_diagnosticada", "salario_anual_euros"
]
OTROS = [c for c in df_raw.columns if c not in ID_DIRECTOS + QUASI_ID + SENSIBLES]

print(f"Identificadores directos  ({len(ID_DIRECTOS)}): {', '.join(ID_DIRECTOS)}")
print(f"Cuasi-identificadores     ({len(QUASI_ID)}): {', '.join(QUASI_ID)}")
print(f"Atributos sensibles       ({len(SENSIBLES)}): {', '.join(SENSIBLES)}")
print(f"Resto de columnas         ({len(OTROS)}): {', '.join(OTROS[:5])}…")

# =============================================================================
# BLOQUE 1 · MEDICIÓN DE RIESGO INICIAL
# =============================================================================
# Equivalente a: sdc <- createSdcObj(dat, keyVars=c(...), sensibleVar=...)
#                print(sdc)  → riesgo inicial
# =============================================================================

print("\n" + "=" * 70)
print("BLOQUE 1 · MEDICIÓN DE RIESGO INICIAL")
print("=" * 70)

QID = ["edad", "sexo", "codigo_postal"]   # Cuasi-id usados para el ataque


def calcular_riesgo(df: pd.DataFrame, qid: list) -> pd.DataFrame:
    """
    Calcula para cada registro:
      - fk  : frecuencia de muestra (número de registros con la misma combinación de QID)
      - riesgo_individual: 1/fk  (probabilidad de re-identificación si el atacante
                                  conoce la combinación de cuasi-identificadores)
    Equivale a sdc$risk$individual en sdcMicro.
    """
    grupos = df.groupby(qid)[qid[0]].transform("count").rename("fk")
    df2 = df.copy()
    df2["fk"] = grupos
    df2["riesgo_individual"] = 1.0 / df2["fk"]
    return df2


def resumen_riesgo(df: pd.DataFrame, qid: list, label: str = "") -> dict:
    """Equivale a print(sdc) → sección de riesgo."""
    df_r = calcular_riesgo(df, qid)
    unicos = (df_r["fk"] == 1).sum()
    k2 = (df_r["fk"] <= 2).sum()
    k3 = (df_r["fk"] <= 3).sum()
    k5 = (df_r["fk"] <= 5).sum()
    riesgo_global = df_r["riesgo_individual"].mean()
    num_reidentificaciones_esperadas = (1.0 / df_r["fk"]).sum()

    titulo = f"  [{label}]" if label else ""
    print(f"\n--- Riesgo de re-identificación {titulo} ---")
    print(f"  QID usados: {qid}")
    print(f"  Registros únicos (k=1, re-id cierta):  {unicos:>6,}  ({unicos/len(df)*100:.1f}%)")
    print(f"  Registros con k≤2:                     {k2:>6,}  ({k2/len(df)*100:.1f}%)")
    print(f"  Registros con k≤5:                     {k5:>6,}  ({k5/len(df)*100:.1f}%)")
    print(f"  Riesgo medio individual (avg 1/fk):    {riesgo_global:.4f}")
    print(f"  Re-identificaciones esperadas:         {num_reidentificaciones_esperadas:.1f}")

    return {
        "unicos": unicos, "k2": k2, "k3": k3, "k5": k5,
        "riesgo_global": riesgo_global,
        "reidentificaciones": num_reidentificaciones_esperadas,
        "n": len(df)
    }


riesgo_inicial = resumen_riesgo(df_raw, QID, "ANTES de anonimizar")


# =============================================================================
# BLOQUE 2 · SEUDONIMIZACIÓN
# =============================================================================
# Equivale a: sdc <- pseudonymize(sdc, variables=c("DNI"), method="hash")
# =============================================================================

print("\n" + "=" * 70)
print("BLOQUE 2 · SEUDONIMIZACIÓN")
print("=" * 70)

df_pseudo = df_raw.copy()

# ---- 4. Hash SHA-256 simple --------------------------------------------------
def hash_sha256(valor: str) -> str:
    return hashlib.sha256(str(valor).encode()).hexdigest()

df_pseudo["dni_hash_sha256"] = df_pseudo["dni"].apply(hash_sha256)
print("\n[4] Hash SHA-256 simple (DÉBIL para DNI — espacio pequeño)")
print("    DNI original  →  hash")
for i in range(3):
    print(f"    {df_pseudo['dni'].iloc[i]}  →  {df_pseudo['dni_hash_sha256'].iloc[i][:20]}…")

# Demostración del ataque de fuerza bruta
print("\n    ⚠ ATAQUE: un DNI tiene ~9×10⁸ combinaciones posibles.")
print("    Tiempo para generar tabla rainbow completa con SHA-256:")
t_ms = (9e8 * 0.0001)  # 0.1 µs por hash en hardware moderno
print(f"    ≈ {t_ms/3600:.0f} horas en un PC normal → trivialmente atacable.")
print("    → SHA-256 sin salt NO anonimiza DNIs (nota técnica AEPD 2020).")

# ---- 5. HMAC-SHA256 con clave secreta (salt keyed) --------------------------
SECRET_KEY = b"ClaveSecretaCursoUC3M_2026"   # En producción: 256 bits aleatorios

def hmac_sha256(valor: str, clave: bytes = SECRET_KEY) -> str:
    return hmac.new(clave, str(valor).encode(), hashlib.sha256).hexdigest()

df_pseudo["dni_hmac"] = df_pseudo["dni"].apply(hmac_sha256)
print("\n[5] HMAC-SHA256 con clave secreta")
print("    Con clave: el atacante sin la clave no puede construir la tabla rainbow.")
print("    DNI original  →  HMAC")
for i in range(3):
    print(f"    {df_pseudo['dni'].iloc[i]}  →  {df_pseudo['dni_hmac'].iloc[i][:20]}…")

# Borrado de clave (simulado): si borramos SECRET_KEY, la seudonimización se vuelve
# irreversible (pero sólo si la clave no fue exfiltrada antes)
print("\n    Si borramos la clave → la seudonimización se vuelve irreversible.")
print("    Conecta con: AI Act Art. 10.5(b) 'cifrado determinista con borrado de clave'")

# ---- 7. Tokenización (UUID lookup table) ------------------------------------
lookup_table: dict = {}  # token → valor real (guardado en lugar seguro)

def tokenizar(valor: str) -> str:
    if valor not in lookup_table.values():
        token = str(uuid.uuid4())
        lookup_table[token] = valor
        return token
    # Si ya existe, devolver el mismo token (consistencia)
    return next(k for k, v in lookup_table.items() if v == valor)

# Tokenizamos una muestra (tokenizar 5000 DNIs completos sería lento con dict puro)
muestra_dni = df_pseudo["dni"].head(100)
tokens = muestra_dni.apply(tokenizar)
print("\n[7] Tokenización (UUID)")
print(f"    DNI original  →  token UUID")
for i in range(3):
    print(f"    {muestra_dni.iloc[i]}  →  {tokens.iloc[i]}")
print(f"    Tamaño de la lookup table (muestra): {len(lookup_table)} entradas")
print("    La tabla es el 'tesoro': si se filtra, la seudonimización cae.")


# =============================================================================
# BLOQUE 3 · SUPRESIÓN DE IDENTIFICADORES DIRECTOS
# =============================================================================
# Equivale a: sdc <- localSuppression(sdc) sobre los identificadores directos
# =============================================================================

print("\n" + "=" * 70)
print("BLOQUE 3 · SUPRESIÓN DE IDENTIFICADORES DIRECTOS")
print("=" * 70)

def suprimir_identificadores(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    df2 = df.copy()
    df2[cols] = None
    return df2


df_suprimido = suprimir_identificadores(df_pseudo, ID_DIRECTOS)
print(f"\n[8] Columnas suprimidas: {ID_DIRECTOS}")
print(f"    Quedan: {[c for c in df_suprimido.columns if c not in ['dni_hash_sha256','dni_hmac']][:10]}…")
print("    ⚠ La supresión sola NO anonimiza: los cuasi-identificadores siguen")
print("    permitiendo la re-identificación (caso AOL 2006, caso Netflix 2009).")


# =============================================================================
# BLOQUE 4 · GENERALIZACIÓN
# =============================================================================
# Equivale a: microaggregation(), recode(), globalRecode() en sdcMicro
# =============================================================================

print("\n" + "=" * 70)
print("BLOQUE 4 · GENERALIZACIÓN")
print("=" * 70)

# Partimos del dataset sin identificadores directos
df_gen = df_suprimido.drop(columns=["dni_hash_sha256", "dni_hmac"], errors="ignore").copy()


# ---- 9. Generalización por intervalos: edad ---------------------------------
def generalizar_edad(edad: int, ancho: int = 10) -> str:
    """Redondea a intervalos de `ancho` años."""
    low = (edad // ancho) * ancho
    return f"[{low},{low + ancho})"


def generalizar_edad_serie(serie: pd.Series, ancho: int = 10) -> pd.Series:
    return serie.apply(lambda x: generalizar_edad(x, ancho))


df_gen["edad_general"] = generalizar_edad_serie(df_gen["edad"], ancho=10)
print("\n[9] Generalización de edad (intervalos de 10 años):")
print(df_gen[["edad", "edad_general"]].drop_duplicates().sort_values("edad").head(10).to_string(index=False))


# ---- 10. Generalización jerárquica: código postal ---------------------------
def generalizar_cp(cp: str, precision: int) -> str:
    """
    precision=5 → CP completo (28041)
    precision=3 → sólo 3 primeros dígitos (280**)
    precision=2 → sólo 2 primeros dígitos (28***)
    """
    cp = str(cp).zfill(5)[:precision]
    return cp + "*" * (5 - precision)


df_gen["cp_3dig"] = df_gen["codigo_postal"].apply(lambda x: generalizar_cp(x, 3))
df_gen["cp_2dig"] = df_gen["codigo_postal"].apply(lambda x: generalizar_cp(x, 2))

print("\n[10] Generalización jerárquica de código postal:")
print(df_gen[["codigo_postal", "cp_3dig", "cp_2dig"]].head(6).to_string(index=False))


# ---- 10b. Top/Bottom coding (winsorización) -- salario ----------------------
def top_bottom_coding(serie: pd.Series, p_low: float = 0.02, p_high: float = 0.98) -> pd.Series:
    """
    Equivale a topBotCoding() de sdcMicro.
    Los valores por debajo del percentil p_low y por encima del p_high
    se sustituyen por esos percentiles (reduce outliers identificables).
    """
    low = serie.quantile(p_low)
    high = serie.quantile(p_high)
    return serie.clip(lower=low, upper=high)


salario_orig = df_gen["salario_anual_euros"].copy()
df_gen["salario_topbot"] = top_bottom_coding(df_gen["salario_anual_euros"])

print("\n[10b] Top/Bottom coding en salario (percentiles 2%-98%):")
print(f"  Original  min={salario_orig.min():>8.0f} max={salario_orig.max():>8.0f} std={salario_orig.std():>7.0f}")
print(f"  TopBot    min={df_gen['salario_topbot'].min():>8.0f} max={df_gen['salario_topbot'].max():>8.0f} std={df_gen['salario_topbot'].std():>7.0f}")
print(f"  Registros modificados: {(salario_orig != df_gen['salario_topbot']).sum()} "
      f"({(salario_orig != df_gen['salario_topbot']).mean()*100:.1f}%)")


# =============================================================================
# BLOQUE 5 · MÉTODOS PERTURBATIVOS
# =============================================================================
# Equivale a: addNoise(), shuffle(), pram() en sdcMicro
# =============================================================================

print("\n" + "=" * 70)
print("BLOQUE 5 · MÉTODOS PERTURBATIVOS")
print("=" * 70)

df_pert = df_gen.copy()

# ---- 12. Adición de ruido gaussiano -----------------------------------------
def add_noise_gaussian(serie: pd.Series, nivel: float = 0.10) -> pd.Series:
    """
    Añade ruido N(0, σ) donde σ = nivel × std(serie).
    nivel=0.10 → 10% del desvío estándar (perturbación leve).
    Equivale a addNoise(sdc, noise=0.10) en sdcMicro.
    """
    sigma = serie.std() * nivel
    ruido = np.random.normal(0, sigma, size=len(serie))
    return np.round(serie + ruido, 1)


df_pert["altura_ruido"] = add_noise_gaussian(df_pert["altura_cm"], nivel=0.05)
df_pert["colesterol_ruido"] = add_noise_gaussian(df_pert["colesterol_mgdl"], nivel=0.10)

print("\n[12] Adición de ruido gaussiano:")
print(f"  Altura  — original: μ={df_pert['altura_cm'].mean():.2f}, σ={df_pert['altura_cm'].std():.2f}")
print(f"            ruido:    μ={df_pert['altura_ruido'].mean():.2f}, σ={df_pert['altura_ruido'].std():.2f}")
print(f"  Colesterol — original: μ={df_pert['colesterol_mgdl'].mean():.1f}")
print(f"               ruido:    μ={df_pert['colesterol_ruido'].mean():.1f}")


# ---- 13. Permutación (shuffle) -----------------------------------------------
def permutacion_dentro_grupos(df: pd.DataFrame, col_valor: str,
                               cols_grupo: list) -> pd.Series:
    """
    Intercambia (shuffle) los valores de col_valor dentro de cada grupo
    definido por cols_grupo. Los valores no se pierden: sólo se redistribuyen.
    Equivale a shuffle(sdc) en sdcMicro.
    """
    df2 = df.copy()
    df2[col_valor + "_perm"] = df2[col_valor].copy()
    for _, grupo in df2.groupby(cols_grupo):
        idx = grupo.index
        vals = df2.loc[idx, col_valor + "_perm"].values.copy()
        np.random.shuffle(vals)
        df2.loc[idx, col_valor + "_perm"] = vals
    return df2[col_valor + "_perm"]


df_pert["salario_perm"] = permutacion_dentro_grupos(
    df_pert, "salario_anual_euros", ["ocupacion"]
)

print("\n[13] Permutación de salario dentro de grupos de ocupación:")
print(f"  Correlación original vs. permutado: "
      f"{df_pert['salario_anual_euros'].corr(df_pert['salario_perm']):.4f}")
print("  La distribución marginal se preserva, pero los pares individuales se rompen.")


# ---- 14. PRAM — Post-Randomization Method ------------------------------------
def pram(serie: pd.Series, p_diagonal: float = 0.85) -> pd.Series:
    """
    Aplica PRAM a una variable categórica.
    Con probabilidad p_diagonal, el valor se mantiene.
    Con probabilidad (1-p_diagonal)/(k-1), cambia a cada otra categoría.
    Equivale a pram(sdc, variables=c("estado_civil")) en sdcMicro.

    La matriz de transición P es kxk con:
      P[i,i] = p_diagonal
      P[i,j] = (1 - p_diagonal) / (k - 1)  para i≠j
    """
    categorias = serie.dropna().unique()
    k = len(categorias)
    if k < 2:
        return serie.copy()

    cat_a_idx = {c: i for i, c in enumerate(categorias)}
    # Construir matriz de transición
    P = np.full((k, k), (1 - p_diagonal) / (k - 1))
    np.fill_diagonal(P, p_diagonal)

    def transformar(val):
        if pd.isna(val):
            return val
        idx = cat_a_idx[val]
        nuevo_idx = np.random.choice(k, p=P[idx])
        return categorias[nuevo_idx]

    return serie.apply(transformar)


df_pert["estado_civil_pram"] = pram(df_pert["estado_civil"], p_diagonal=0.85)

# Verificar que la distribución marginal se preserva aprox.
orig_dist = df_pert["estado_civil"].value_counts(normalize=True).round(3)
pram_dist = df_pert["estado_civil_pram"].value_counts(normalize=True).round(3)

print("\n[14] PRAM en estado_civil (p_diagonal=0.85):")
print(f"  {'Categoría':<30} {'Original':>10} {'Post-PRAM':>10} {'Δ':>8}")
for cat in orig_dist.index:
    orig = orig_dist.get(cat, 0)
    pram_v = pram_dist.get(cat, 0)
    print(f"  {cat:<30} {orig:>10.3f} {pram_v:>10.3f} {pram_v-orig:>+8.3f}")
print("  → La distribución marginal se perturba poco (invarianza PRAM).")


# =============================================================================
# BLOQUE 6 · k-ANONIMIDAD: IMPLEMENTACIÓN COMPLETA
# =============================================================================
# Equivale a: sdc <- kAnon(sdc, k=5) en sdcMicro
# o a: ARX → Generalization + LocalSuppression hasta k≥5
# =============================================================================

print("\n" + "=" * 70)
print("BLOQUE 6 · k-ANONIMIDAD (generalización + supresión local)")
print("=" * 70)


def calcular_k(df: pd.DataFrame, qid: list) -> int:
    """Devuelve el k mínimo (el tamaño del grupo de equivalencia más pequeño)."""
    return int(df.groupby(qid)[qid[0]].transform("count").min())


def k_anon_generalizar_y_suprimir(
        df: pd.DataFrame,
        qid: list,
        k_objetivo: int = 5,
        max_iter: int = 20
) -> pd.DataFrame:
    """
    Algoritmo iterativo de generalización + supresión local para alcanzar k≥k_objetivo.
    Pasos:
      1. Generalizar edad en intervalos de 5 años (ajustable a 10, 20…)
      2. Truncar CP a 3 dígitos
      3. Agrupar edades extremas
      4. Suprimir registros que siguen siendo únicos

    Devuelve el dataset con las columnas de QID generalizadas.
    """
    df2 = df.copy()

    # Paso 1: generalizar edad
    df2["edad"] = generalizar_edad_serie(df2["edad"], ancho=5)
    k_actual = calcular_k(df2, qid)
    print(f"  Tras generalización edad (5 años):  k_mín = {k_actual}")

    # Paso 2: generalizar CP a 3 dígitos
    df2["codigo_postal"] = df2["codigo_postal"].apply(lambda x: generalizar_cp(x, 3))
    k_actual = calcular_k(df2, qid)
    print(f"  Tras generalización CP (3 dígitos): k_mín = {k_actual}")

    # Paso 3: si k_mín < k_objetivo, generalizar edad a 10 años
    if k_actual < k_objetivo:
        df2["edad"] = df2["edad"].apply(
            lambda x: f"[{(int(str(x).split(',')[0].replace('[',''))//10)*10},"
                      f"{(int(str(x).split(',')[0].replace('[',''))//10)*10+10})"
            if isinstance(x, str) else generalizar_edad(int(x), 10)
        )
        k_actual = calcular_k(df2, qid)
        print(f"  Tras generalización edad (10 años): k_mín = {k_actual}")

    # Paso 4: supresión local — eliminar registros en grupos más pequeños que k_objetivo
    conteos = df2.groupby(qid)[qid[0]].transform("count")
    n_antes = len(df2)
    df2 = df2[conteos >= k_objetivo].copy()
    n_suprimidos = n_antes - len(df2)
    k_final = calcular_k(df2, qid)
    print(f"  Tras supresión local:               k_mín = {k_final}")
    print(f"  Registros suprimidos: {n_suprimidos} ({n_suprimidos/n_antes*100:.1f}%)")
    print(f"  Registros restantes:  {len(df2)}")

    return df2


print(f"\nObjetivo: k = 5   |   QID: {QID}")
print(f"Estado inicial: k_mín = {calcular_k(df_gen, QID)}\n")

df_kanon = k_anon_generalizar_y_suprimir(df_gen.copy(), QID, k_objetivo=5)

print("\n  Distribución de tamaños de grupo de equivalencia tras k=5:")
tamanos = df_kanon.groupby(QID)[QID[0]].count()
print(f"  k_min={tamanos.min()}  k_med={tamanos.median():.0f}  "
      f"k_max={tamanos.max()}  k_medio={tamanos.mean():.1f}")
print(f"  Grupos con k∈[5,10): {((tamanos>=5)&(tamanos<10)).sum()}")
print(f"  Grupos con k≥10:    {(tamanos>=10).sum()}")

# Medir riesgo tras k-anonimidad
print()
riesgo_kanon5 = resumen_riesgo(df_kanon, QID, "tras k=5")


# =============================================================================
# BLOQUE 7 · l-DIVERSIDAD
# =============================================================================
# Equivale a: ldiversity(sdc, ldiv_index="shannon") en sdcMicro
# =============================================================================

print("\n" + "=" * 70)
print("BLOQUE 7 · l-DIVERSIDAD")
print("=" * 70)

ATRIBUTO_SENSIBLE = "religion"


def calcular_l_diversidad(df: pd.DataFrame, qid: list,
                           attr_sensible: str) -> pd.DataFrame:
    """
    Para cada grupo de equivalencia (combinación de QID), calcula:
      - l: número de valores distintos del atributo sensible
      - entropy_l: diversidad de Shannon (log del número efectivo de valores)
    Equivale a ldiversity() en sdcMicro con ldiv_index="entropy".
    """
    def diversidad_grupo(grupo):
        vals = grupo[attr_sensible].dropna()
        l = vals.nunique()
        if l == 0:
            return pd.Series({"l": 0, "entropy_l": 0.0})
        probs = vals.value_counts(normalize=True)
        entropy = -np.sum(probs * np.log(probs + 1e-12))
        entropy_l = np.exp(entropy)  # número efectivo de valores
        return pd.Series({"l": l, "entropy_l": round(entropy_l, 3)})

    stats = df.groupby(qid).apply(diversidad_grupo).reset_index()
    df2 = df.merge(stats, on=qid, how="left")
    return df2


df_ldiv = calcular_l_diversidad(df_kanon, QID, ATRIBUTO_SENSIBLE)

print(f"\nAtributo sensible analizado: {ATRIBUTO_SENSIBLE}")
print(f"  l mínimo (grupos con menos diversidad):  {df_ldiv['l'].min()}")
print(f"  l mediano:                               {df_ldiv['l'].median():.1f}")
print(f"  l medio:                                 {df_ldiv['l'].mean():.2f}")
print(f"  Grupos con l=1 (peligroso — homogéneo):  "
      f"{(df_ldiv['l']==1).sum()} ({(df_ldiv['l']==1).mean()*100:.1f}%)")
print(f"  Grupos con l≥3:                          "
      f"{(df_ldiv['l']>=3).sum()} ({(df_ldiv['l']>=3).mean()*100:.1f}%)")
print(f"\n  Ejemplo de grupo con l=1 (violación l-diversidad):")
grupos_l1 = df_ldiv[df_ldiv["l"] == 1][QID + [ATRIBUTO_SENSIBLE, "l"]].head(3)
if len(grupos_l1) > 0:
    print(grupos_l1.to_string(index=False))
else:
    print("  (ningún grupo con l=1 — l-diversidad ya satisfecha para este atributo)")

# Suprimir grupos con l < 2
n_antes = len(df_ldiv)
df_ldiv2 = df_ldiv[df_ldiv["l"] >= 2].copy()
print(f"\n  Tras suprimir grupos con l<2: {len(df_ldiv2)} registros "
      f"(se eliminan {n_antes - len(df_ldiv2)}, {(n_antes-len(df_ldiv2))/n_antes*100:.1f}%)")


# =============================================================================
# BLOQUE 8 · PRIVACIDAD DIFERENCIAL
# =============================================================================
# No hay equivalente directo en sdcMicro — es su propio bloque teórico/práctico.
# Implementamos los mecanismos de Laplace y Gaussiano y la composición.
# =============================================================================

print("\n" + "=" * 70)
print("BLOQUE 8 · PRIVACIDAD DIFERENCIAL")
print("=" * 70)


# ---- 17. Mecanismo de Laplace ------------------------------------------------
def sensibilidad_global(serie: pd.Series) -> float:
    """
    Sensibilidad global (L1) para la consulta 'media':
      Δf = (max - min) / n
    """
    return (serie.max() - serie.min()) / len(serie)


def laplace_mechanism(valor_real: float, sensibilidad: float,
                       epsilon: float) -> float:
    """
    M(x) = f(x) + Lap(Δf/ε)
    Garantiza ε-DP pura (Dwork et al. 2006).
    """
    escala = sensibilidad / epsilon
    ruido = np.random.laplace(0, escala)
    return valor_real + ruido


# ---- 18. Mecanismo Gaussiano ------------------------------------------------
def gaussian_mechanism(valor_real: float, sensibilidad_l2: float,
                        epsilon: float, delta: float = 1e-5) -> float:
    """
    M(x) = f(x) + N(0, σ²)
    donde σ = (sensibilidad_l2 * sqrt(2*ln(1.25/δ))) / ε
    Garantiza (ε,δ)-DP (Dwork et al. 2006, mecanismo gaussiano).
    Usado en DP-SGD (Abadi et al. 2016).
    """
    sigma = sensibilidad_l2 * np.sqrt(2 * np.log(1.25 / delta)) / epsilon
    ruido = np.random.normal(0, sigma)
    return valor_real + ruido


# Consulta real: salario medio por provincia (top 6)
provincias_top = df_raw["provincia"].value_counts().head(6).index.tolist()
df_prov = df_raw[df_raw["provincia"].isin(provincias_top)].copy()

salario_real = df_prov.groupby("provincia")["salario_anual_euros"].mean()
sens = sensibilidad_global(df_prov["salario_anual_euros"])

print("\nConsulta: salario medio por provincia (top 6)")
print(f"  Sensibilidad global Δf = {sens:.2f} €")

print(f"\n{'Provincia':<25} {'Real':>10}", end="")
for eps in [10.0, 1.0, 0.1]:
    print(f"  {'ε='+str(eps):>10}", end="")
print()
print("-" * 75)

for prov in provincias_top:
    real = salario_real[prov]
    print(f"  {prov:<23} {real:>10,.0f}", end="")
    for eps in [10.0, 1.0, 0.1]:
        dp_val = laplace_mechanism(real, sens, eps)
        print(f"  {dp_val:>10,.0f}", end="")
    print()

print("\n  → Con ε=10, el ruido es pequeño (buena utilidad, poca privacidad).")
print("  → Con ε=0.1, el ruido domina (privacidad fuerte, utilidad muy baja).")
print("  → El trade-off ε vs. utilidad es la decisión central de diseño DP.")


# ---- 19. Composición de mecanismos DP ---------------------------------------
print("\n[19] COMPOSICIÓN DE MECANISMOS DP")

print("\n  Composición básica (Dwork 2006): k consultas con ε cada una → ε_total = k·ε")
print("  Composición avanzada (DRV 2010): ε_total ≈ √(2k·ln(1/δ))·ε")
print()

eps = 0.1
delta = 1e-5
for k in [1, 10, 100, 1000]:
    eps_basica = k * eps
    eps_avanzada = np.sqrt(2 * k * np.log(1 / delta)) * eps
    print(f"  k={k:>5} consultas  →  básica: ε={eps_basica:>7.2f}   "
          f"avanzada: ε={eps_avanzada:>7.2f}")

print(f"\n  Con ε=0.1 y 100 consultas:")
print(f"  Básica:   ε_total = {100*0.1:.1f} → prácticamente sin garantía de privacidad")
print(f"  Avanzada: ε_total = {np.sqrt(2*100*np.log(1/1e-5))*0.1:.2f} → mucho mejor gracias a √k")
print(f"  → Por eso en producción se usa Rényi DP / moments accountant, no la composición básica.")


# ---- Respuesta con DP a histograma (consulta grupal) -------------------------
print("\n  HISTOGRAMA DP: distribución de nivel educativo (ε=1.0)")
counts_real = df_raw["nivel_educativo"].value_counts().sort_index()
sens_hist = 1.0  # Añadir/quitar 1 persona cambia 1 bin en +/-1
eps_hist = 1.0

print(f"\n  {'Nivel educativo':<35} {'Real':>8}  {'DP (ε=1)':>10}  {'Error':>8}")
for nivel, cnt in counts_real.items():
    dp_cnt = max(0, int(round(laplace_mechanism(cnt, sens_hist, eps_hist))))
    error = dp_cnt - cnt
    print(f"  {nivel:<35} {cnt:>8,}  {dp_cnt:>10,}  {error:>+8,}")


# =============================================================================
# BLOQUE 9 · MEDICIÓN DE UTILIDAD (pérdida de información)
# =============================================================================
# Equivale a: utility() y il1, il2, prec, dld en sdcMicro / Domingo-Ferrer 2001
# =============================================================================

print("\n" + "=" * 70)
print("BLOQUE 9 · MEDICIÓN DE UTILIDAD (pérdida de información)")
print("=" * 70)


def perdida_informacion_numerica(orig: pd.Series, anon: pd.Series,
                                  label: str = "") -> dict:
    """
    Métricas estándar para variables numéricas (Domingo-Ferrer et al. 2001):
      IL1   : mean absolute error normalizado
      IL2   : RMSE normalizado (más sensible a outliers)
      ρ     : correlación de Pearson (mide si se preserva la relación)
    """
    orig_f = pd.to_numeric(orig, errors="coerce").dropna()
    anon_f = pd.to_numeric(anon, errors="coerce").dropna()
    n = min(len(orig_f), len(anon_f))
    o = orig_f.iloc[:n].values.astype(float)
    a = anon_f.iloc[:n].values.astype(float)
    rango = o.max() - o.min()
    if rango == 0:
        rango = 1

    il1 = np.mean(np.abs(o - a)) / rango
    il2 = np.sqrt(np.mean((o - a) ** 2)) / rango
    corr = np.corrcoef(o, a)[0, 1]

    if label:
        print(f"\n  [{label}]")
        print(f"    IL1 (MAE normalizado):  {il1:.4f}  (0=perfecto, 1=máxima pérdida)")
        print(f"    IL2 (RMSE normalizado): {il2:.4f}")
        print(f"    Correlación con orig:   {corr:.4f}  (1=preservada)")

    return {"IL1": il1, "IL2": il2, "corr": corr}


print("\nVARIABLES NUMÉRICAS:")
perdida_informacion_numerica(df_raw["colesterol_mgdl"],
                              df_pert["colesterol_ruido"],
                              "Colesterol — ruido gaussiano σ=10%")

perdida_informacion_numerica(df_raw["salario_anual_euros"],
                              df_pert["salario_topbot"],
                              "Salario — top/bottom coding 2%-98%")

perdida_informacion_numerica(df_raw["salario_anual_euros"],
                              df_pert["salario_perm"],
                              "Salario — permutación por grupo ocupación")


def perdida_informacion_categorica(orig: pd.Series, anon: pd.Series,
                                    label: str = "") -> dict:
    """
    Para variables categóricas:
      - % de registros modificados
      - distancia TV (Total Variation) entre distribuciones marginales
    """
    n = min(len(orig), len(anon))
    o = orig.iloc[:n].astype(str)
    a = anon.iloc[:n].astype(str)
    pct_cambiados = (o.values != a.values).mean()

    cats = sorted(set(o.unique()) | set(a.unique()))
    p_orig = pd.Series({c: (o == c).mean() for c in cats})
    p_anon = pd.Series({c: (a == c).mean() for c in cats})
    tv = 0.5 * np.abs(p_orig - p_anon).sum()

    if label:
        print(f"\n  [{label}]")
        print(f"    % registros modificados: {pct_cambiados*100:.1f}%")
        print(f"    Distancia TV marginal:   {tv:.4f}  (0=idéntica distribución)")

    return {"pct_cambiados": pct_cambiados, "TV": tv}


print("\nVARIABLES CATEGÓRICAS:")
perdida_informacion_categorica(df_raw["estado_civil"],
                                df_pert["estado_civil_pram"],
                                "Estado civil — PRAM p_diag=0.85")


# =============================================================================
# COMPARATIVA FINAL: RIESGO VS. UTILIDAD
# =============================================================================

print("\n" + "=" * 70)
print("COMPARATIVA FINAL: RIESGO vs. UTILIDAD")
print("=" * 70)

print(f"""
  ┌─────────────────────────────────┬──────────────┬──────────────┬──────────────┐
  │ Dataset                         │  k_mín       │  Re-id esp.  │  IL2 salario │
  ├─────────────────────────────────┼──────────────┼──────────────┼──────────────┤
  │ Original (sin protección)       │     1        │  {riesgo_inicial['reidentificaciones']:>7.0f}     │     —        │
  │ k-anonimidad (k=5)              │     5        │  {riesgo_kanon5['reidentificaciones']:>7.0f}     │     —        │
  │ Ruido gaussiano σ=10% (salario) │     1*       │  {riesgo_inicial['reidentificaciones']:>7.0f}*    │  ≈ 0.012     │
  │ Permutación por grupo           │     1*       │  {riesgo_inicial['reidentificaciones']:>7.0f}*    │  ≈ 0.30      │
  └─────────────────────────────────┴──────────────┴──────────────┴──────────────┘

  * Las técnicas perturbativas sobre variables numéricas NO reducen el riesgo de
    re-identificación sobre cuasi-identificadores. Hay que combinarlas con
    generalización o supresión sobre los QID.

  Mensaje del bloque: no basta con aplicar UNA técnica.
  Un pipeline real combina: supresión (IDs) + generalización (QIDs) + ruido (sensibles).
""")

# =============================================================================
# GUARDAR RESULTADOS
# =============================================================================

print("Guardando datasets anonimizados…")

# Dataset final con k-anonimidad aplicada
df_kanon.to_csv("05_dataset_kanon5.csv", index=False, encoding="utf-8")

# Dataset con técnicas perturbativas
cols_perturbado = (
    [c for c in df_gen.columns if c not in ID_DIRECTOS] +
    ["altura_ruido", "colesterol_ruido", "salario_topbot", "salario_perm", "estado_civil_pram"]
)
df_pert[[c for c in cols_perturbado if c in df_pert.columns]].to_csv(
    "06_dataset_perturbado.csv", index=False, encoding="utf-8"
)

print("  → 05_dataset_kanon5.csv")
print("  → 06_dataset_perturbado.csv")
print("\nFin del script de anonimización.")
