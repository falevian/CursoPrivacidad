# Datasets sintéticos — Curso de Privacidad, Anonimidad y Riesgos Ciber asociados a IA

**UC3M — Sistemas de la Sociedad Digital · Rafael Vida**

Este paquete contiene 4 datasets sintéticos diseñados específicamente para las prácticas del curso (3 h). Los datos no son reales: están generados a partir de distribuciones reales del INE (España, 2023-2024) — frecuencias de nombres y apellidos, pirámide poblacional, distribución por provincias, alturas/pesos por sexo (ENSE 2017), salario medio por ocupación (EES 2023), etc.

---

## 📁 Ficheros

| Fichero | Filas | Cols | Propósito |
|---|---|---|---|
| `01_dataset_principal.csv` | 5.000 | 43 | Base de clientes ficticia. Contiene identificadores directos, cuasi-identificadores e información sensible. Es el dataset "atacante con todo a la vista" — sirve para entender qué hay que proteger. |
| `02_dataset_hospital.csv` | 2.500 | 10 | Datos hospitalarios "anonimizados" (sin nombre/DNI), con cuasi-identificadores (edad, sexo, CP) y diagnóstico. Diseñado para ataques de **singularización** y aplicación de **k-anonimidad / l-diversidad**. |
| `03_dataset_red_social.csv` | 3.750 | 13 | Perfiles públicos de una red social ficticia con valoraciones de películas (estilo Netflix/IMDB). Diseñado para ataques de **vinculabilidad** (Narayanan-Shmatikov 2008). |
| `04_dataset_movilidad.csv` | 251.445 | 9 | Trazas de localización (CDR) de 1.500 usuarios durante 2 meses. Diseñado para ataques de **unicidad** (Montjoye et al. 2013: 4 puntos = 95% identificación). |
| `SOLUCION_vinculacion_red_social.csv` | 3.750 | 4 | **Solo profesor.** Mapeo `username` → `id_cliente` real para verificar los ataques. |

---

## ✅ Garantías de los datos

- **Distribuciones realistas**: nombres siguen la frecuencia INE (Antonio, José, Manuel… ; García, López, Rodríguez…).
- **DNIs válidos**: letra de control calculada con el algoritmo oficial.
- **IBANs con dígito de control coherente** (mod 97).
- **Alturas/pesos por sexo**: H 173,1 ± 7,5 cm · M 160,4 ± 6,5 cm (ENSE 2017).
- **Salarios correlacionados** con ocupación, nivel educativo, sexo (brecha 18%), provincia y edad.
- **Códigos postales coherentes** con la provincia (rangos reales).
- **Estado civil correlacionado con edad**, hijos correlacionados con edad y estado civil.
- **Comorbilidades correlacionadas**: diabetes ↔ IMC, hipertensión ↔ edad/IMC, etc.
- **Patrones de movilidad realistas**: cada usuario tiene 3 ubicaciones recurrentes (casa/trabajo/ocio) con horarios coherentes.

### Verificación tras la generación
```
Dataset hospital · k-anonimidad = 1 al 100%   ← ataque trivial antes de proteger
Dataset movilidad · unicidad con 4 puntos = 97,3%   ← replica Montjoye 2013
```

---

## 🎯 Plan de prácticas (3 horas)

### Bloque 1 (45 min) — Identificación, singularización y vinculabilidad

**Objetivo:** experimentar los tres ataques canónicos del curso.

#### Práctica 1.1 · Singularización (15 min) — usar `02_dataset_hospital.csv`
> *"Si supieras que tu vecina, mujer de 47 años con CP 28041, está en este dataset, ¿podrías saber su diagnóstico?"*

- Cargar el dataset.
- Contar combinaciones únicas de (edad, sexo, código_postal).
- Verificar k-anonimidad inicial (debe salir ~100% k=1).
- **Reflexión:** quitar nombre y DNI no anonimiza.

#### Práctica 1.2 · Vinculabilidad (20 min) — `03_dataset_red_social.csv` + `01_dataset_principal.csv`
> *Ataque estilo Netflix/IMDB de Narayanan-Shmatikov.*

- Asumir que el atacante tiene `01_dataset_principal.csv` (filtrado al perfil objetivo: nombre, ciudad, edad).
- Buscar coincidencias en la red social usando: ciudad + edad±2 + iniciales/nombre extraído del `username`.
- Comparar con `SOLUCION_vinculacion_red_social.csv` para medir tasa de éxito.

#### Práctica 1.3 · Inferencia (10 min) — `02_dataset_hospital.csv`
- Calcular % de mujeres 56-60 con cáncer de mama: si es muy alto, hay revelación de atributos sin identificación (ejemplo del curso).

---

### Bloque 2 (60 min) — Técnicas de protección

**Objetivo:** aplicar y medir el coste de las técnicas perturbativas y no perturbativas.

#### Práctica 2.1 · Generalización + supresión → k-anonimidad (25 min)
- En `02_dataset_hospital.csv`:
  - Generalizar `edad` en intervalos de 10 años.
  - Generalizar `código_postal` truncando a 3 dígitos.
  - Suprimir registros con QID únicos (cell suppression).
- Medir k mínimo, k mediano, % registros suprimidos.
- Repetir con k=5, k=10, k=20. Trazar curva **k vs. utilidad perdida**.

#### Práctica 2.2 · l-diversidad (15 min)
- Tras k=5, comprobar si todas las clases de equivalencia tienen al menos l=2 valores distintos de `diagnostico`.
- Detectar grupos donde, a pesar de k≥5, el atributo sensible es homogéneo (revelación de atributos).

#### Práctica 2.3 · Privacidad diferencial básica (20 min)
- Sobre `01_dataset_principal.csv`: calcular salario medio por provincia con DP.
- Aplicar mecanismo de Laplace con ε ∈ {0.1, 1, 10}.
- Comparar el coste en utilidad (RMSE vs. valor real).
- Discutir composición: si hago 100 consultas con ε=0.1 cada una, ¿cuál es el ε total?

---

### Bloque 3 (45 min) — Riesgo, utilidad y movilidad

#### Práctica 3.1 · Unicidad en movilidad (25 min) — `04_dataset_movilidad.csv`
- Para cada usuario, tomar sus N primeros eventos.
- Construir tuplas (antena_id, fecha) y medir cuántos usuarios quedan únicos con N = 1, 2, 3, 4, 5 puntos.
- Replicar la curva del paper de Montjoye: ¿cuántos puntos hacen falta para identificar al 95%?
- Probar con resoluciones temporales y espaciales degradadas.

#### Práctica 3.2 · Funciones hash y seudonimización (20 min)
- Aplicar SHA-256 a la columna `dni` en `01_dataset_principal.csv`.
- Mostrar que el espacio de DNIs es pequeño (~10⁹) → ataque de fuerza bruta trivial.
- Repetir con HMAC-SHA256 + secret key (clave salt). Comparar.
- Conectar con la nota técnica AEPD sobre k-anonimidad y hash referenciada en el curso.

---

### Bloque 4 (30 min) — IA y privacidad (caso LLM)

**Discusión guiada (sin código):** usando los datos generados, plantear:
1. Si entrenara un modelo de scoring crediticio sobre `01_dataset_principal.csv`, ¿qué riesgos del Art. 10 del AI Act aplicarían?
2. ¿Qué memorización podría tener un modelo entrenado sobre `02_dataset_hospital.csv`? ¿Qué pasaría con el ataque de divergencia tipo "poem poem poem"?
3. Listar las defensas aplicables: DP-SGD, deduplicación, federated learning, machine unlearning, datos sintéticos.

---

## 🔑 Columnas del dataset principal

**Identificadores directos:** `id_cliente`, `dni`, `nombre`, `apellido1`, `apellido2`, `telefono`, `email`, `iban`, `direccion`, `usuario`, `password_hash_sha256`.

**Cuasi-identificadores:** `fecha_nacimiento`, `edad`, `sexo`, `codigo_postal`, `ciudad`, `provincia`, `pais`, `nacionalidad`.

**Atributos sensibles (Art. 9 RGPD):** `religion`, `orientacion_sexual`, `diabetes`, `hipertension`, `colesterol_mgdl`, `fumador`, `consumo_alcohol_ud_semana`, `ansiedad_diagnosticada`, `depresion_diagnosticada`.

**Atributos no sensibles:** `estado_civil`, `num_hijos`, `altura_cm`, `peso_kg`, `imc`, `nivel_educativo`, `situacion_laboral`, `ocupacion`, `salario_anual_euros`, `tiene_hipoteca`, `deuda_total_euros`, `tiene_coche`, `horas_internet_dia`, `gasto_mensual_online_euros`, `fecha_alta_cliente`.

---

## ⚖️ Sobre los datos

Estos datos son **completamente sintéticos**. Cualquier coincidencia con personas reales es estadísticamente esperable (los nombres son los más comunes de España) pero no real: los DNIs, IBANs, direcciones y combinaciones son inventados.

Aún así, **trate los ficheros como si fueran reales** durante las prácticas — esa es buena parte del valor pedagógico del curso.

---

## 🛠️ Reproducir / regenerar

```bash
python generar_datos.py
```

Semilla fija (`SEED=42`). Modificable en el script para generar variaciones.
