# Lessons Learned — Blueprint Dashboards Ejecutivos RCM HF Multi-Clínica

## Mistakes Made

### Mistake 1: Pending claims inflados con balances de paciente
- **What happened:** ~2,637 claims pagados por el seguro fueron clasificados como "pending" porque tenían un balance restante.
- **Root cause:** El parser asumió que `balance > 0` equivalía a claim sin resolver, sin distinguir entre balance de aseguradora y balance de paciente (copay/deductible).
- **How it was caught:** Discrepancia entre paid_claims count y volumen de pagos recibidos; revisión manual de registros individuales.
- **Fix applied:** Agregar campo `patient_responsibility_flag`; claim se clasifica como paid si el seguro pagó, independientemente de si queda saldo de paciente.
- **Rule extracted:** Nunca asumir que `remaining_balance > 0` equivale a claim pendiente de aseguradora. Siempre distinguir `insurance-unresolved` de `paid-with-patient-balance` antes de reportar pending claims.

### Mistake 2: Años capturados como CPT codes falsos positivos
- **What happened:** El regex `\b\d{5}\b` para extraer CPT codes capturaba años ("2025", "2024") de campos de fecha en el texto del PDF.
- **Root cause:** Los años de 4 dígitos no aplican, pero fechas en formatos como "01/01/2025" o años solos en ciertos campos sí generaban strings de 5 dígitos al estar concatenados o mal separados.
- **How it was caught:** CPTs inválidos (e.g., "20250", "20241") aparecieron en el dataset.
- **Fix applied:** Strip de patrones de fecha (MM/DD/YYYY, YYYY-MM-DD, standalone YYYY) antes de aplicar el regex CPT.
- **Rule extracted:** Siempre limpiar patrones de fecha del texto ANTES de correr cualquier regex de extracción de CPT codes. Nunca asumir que todos los números de 5 dígitos en un PDF médico son CPTs válidos.

### Mistake 3: Category II CPT codes incluidos en análisis financiero
- **What happened:** CPT codes con sufijo `F` (e.g., `3074F`, `1000F`) — quality measure codes — fueron incluidos en conteos de CPTs y proyecciones de revenue.
- **Root cause:** El extractor no filtraba por formato; tomaba todos los códigos que matcheaban el patrón alfanumérico.
- **How it was caught:** Códigos con sufijo F aparecieron en el análisis con montos de $0.01.
- **Fix applied:** Filtro explícito: `if code.endswith('F'): mark as informational_skip`.
- **Rule extracted:** Siempre filtrar Category II CPT codes (sufijo F) antes de cualquier análisis financiero. Se facturan a $0.01, son informativos/quality measures, y no representan revenue real.

### Mistake 4: Manual postings mezclados en análisis de payment cycle
- **What happened:** Se incluyeron registros de posting manual (cheques físicos) en el cálculo de días-hasta-pago.
- **Root cause:** No se distinguía el campo `posting_type` al construir las queries de payment cycle time.
- **How it was caught:** Payment cycle times anómalos (outliers de 0 días o muy cortos) que no correspondían a comportamiento real de aseguradoras.
- **Fix applied:** Filtro `WHERE posting_type = '835'` en todas las queries de cycle time.
- **Rule extracted:** Para análisis de payment cycle time, usar exclusivamente registros 835 (electronic remittance). Nunca mezclar 835 con manual postings — los postings manuales reflejan fecha de registro interno, no fecha real de emisión del pago.

### Mistake 5: Pacientes capitated no excluidos de métricas fee-for-service
- **What happened:** Pacientes bajo capitation en Hispano (vía MSO Practice Choice) fueron incluidos en collection rates estándar, deprimiendo artificialmente las métricas de esa clínica.
- **Root cause:** No había un flag de capitation en el schema inicial.
- **How it was caught:** Collection rate de Hispano anormalmente bajo vs volumen de claims pagados observado.
- **Fix applied:** Agregar `capitation_flag` al schema; excluir de análisis fee-for-service estándar.
- **Rule extracted:** Siempre identificar y flaggear pacientes bajo capitation antes del análisis. Hispano conecta vía MSO Practice Choice con posting manual — ningún registro de ese flujo tiene 835. Excluir de comparativas estándar entre clínicas.

### Mistake 6: openpyxl falló repetidamente en ClaimsAnaliticPremier.xlsx
- **What happened:** Múltiples intentos de leer el archivo con openpyxl fallaron con errores de compatibilidad de formato.
- **Root cause:** El archivo tenía formato interno incompatible con la versión de openpyxl disponible en el entorno.
- **How it was caught:** Excepción en runtime en cada intento.
- **Fix applied:** No se resolvió definitivamente en esta sesión — archivo requirió re-upload o conversión externa.
- **Rule extracted:** Si openpyxl falla en un .xlsx, intentar en orden: (1) engine='xlrd', (2) conversión a CSV vía libreoffice --headless, (3) solicitar re-upload. Nunca iterar sobre el mismo método que ya falló.

### Mistake 7: Status columns de Monday.com con >5 labels o colores no estándar
- **What happened:** Se crearon status columns con 6+ labels o nombres de colores no estándar; la API aceptaba el request sin error pero los labels se creaban incorrectos.
- **Root cause:** La API de Monday.com falla silenciosamente en este caso — no retorna error, simplemente ignora labels extras o usa el color más cercano.
- **How it was caught:** Verificación manual post-creación de la columna.
- **Fix applied:** Limitar a máximo 5 labels y usar únicamente color names documentados.
- **Rule extracted:** Siempre leer la columna después de crearla vía API para verificar que los labels coincidan con los enviados. Nunca asumir éxito por ausencia de error en la respuesta de Monday.com.

### Mistake 8: GraphQL mutations sin aliases en batch a Monday.com
- **What happened:** Se enviaron múltiples mutations en un solo query GraphQL sin aliases; la operación falló completamente.
- **Root cause:** GraphQL no permite múltiples operaciones del mismo tipo sin aliases en un solo request.
- **How it was caught:** Error de GraphQL en la respuesta.
- **Fix applied:** Agregar aliases (g1:, g2:, c1:, c2:) a cada mutation.
- **Rule extracted:** Siempre usar aliases para batch mutations en Monday.com GraphQL. Una sola mutation sin alias funciona; múltiples sin alias fallan completamente sin ejecutar ninguna.

### Mistake 9: Caracteres acentuados en nombres de columna de Monday.com
- **What happened:** Nombres con tildes/acentos en columnas de Monday.com vía API resultaron en nombres corrompidos o columnas que fallaban en crearse.
- **Root cause:** Encoding issue en la API de Monday.com con caracteres no-ASCII en nombres de columna.
- **How it was caught:** Nombres de columna en el board no coincidían con los enviados.
- **Fix applied:** Usar versión sin acento o inglés en nombres de columna.
- **Rule extracted:** Nunca usar caracteres acentuados, ñ, o símbolos especiales en nombres de columnas de Monday.com vía API.

### Mistake 10: PageNumber no disponible en versión instalada de docx (Node.js)
- **What happened:** Se intentó usar el export `PageNumber` de la librería `docx` en Node.js; el import falló en runtime.
- **Root cause:** `PageNumber` no está disponible en todas las versiones de la librería `docx`.
- **How it was caught:** Error de runtime al generar el documento.
- **Fix applied:** Usar `TextRun` con texto estático como placeholder.
- **Rule extracted:** Verificar exports disponibles de `docx` con `require('docx')` antes de usar cualquier export no documentado. Usar `new TextRun({ text: "Página 1" })` como fallback para numeración.

### Mistake 11: IKON posicionado como decisión downstream
- **What happened:** En versiones tempranas del plan de transición, IKON aparecía como "plataforma a evaluar" en fases posteriores.
- **Root cause:** Confusión entre el momento de implementación y su rol arquitectónico.
- **How it was caught:** El modelo dual (telemedicina + clínicas físicas) no tiene camino viable sin IKON ya en operación.
- **Fix applied:** Repositionar IKON como prerequisito técnico fundacional en todos los documentos ejecutivos.
- **Rule extracted:** IKON es infraestructura fundacional, no opción downstream. Siempre posicionarlo como prerequisito de la transición in-house en cualquier documento ejecutivo o plan de implementación.

### Mistake 12: Análisis ejecutado antes de reconciliación de datos
- **What happened:** En iteraciones tempranas se procedió a análisis de tendencias sin verificar que los claim counts por clínica sumaran correctamente al total.
- **Root cause:** Urgencia por llegar al análisis; la reconciliación se trató como un paso opcional.
- **How it was caught:** Totales no cuadraban en la vista consolidada.
- **Fix applied:** Ejecutar reconciliación completa antes de cualquier visualización o reporte.
- **Rule extracted:** Siempre ejecutar reconciliación (suma por clínica vs total global, validación de fechas y montos) ANTES de cualquier análisis o visualización. La reconciliación no es un paso opcional — es la puerta de entrada al análisis.

---

## Assumptions That Were Wrong

- **"Balance restante = claim pendiente"** — Falso. Un claim puede estar pagado por el seguro y tener saldo de paciente pendiente. Son conceptos distintos.
- **"Todos los 5 dígitos en PDFs médicos son CPTs"** — Falso. Años, códigos de lugar, y otros números de 5 dígitos aparecen en los textos.
- **"La API de Monday.com retorna error cuando algo falla"** — Falso. Varios casos fallan silenciosamente (status labels, caracteres especiales).
- **"IKON puede implementarse después de la transición"** — Falso. Es prerequisito, no consecuencia.

---

## What to Do Differently Next Time

1. Reconciliar datos ANTES de cualquier análisis — sin excepciones.
2. Definir schema de exclusiones (Category II, capitation, manual postings) al inicio del pipeline, no como corrección posterior.
3. Leer siempre el resultado de operaciones en Monday.com después de ejecutarlas para verificar.
4. Probar el regex de CPT extraction con texto que incluya fechas antes de correrlo sobre el dataset completo.
5. Verificar versión exacta de librerías (docx, openpyxl) antes de planificar su uso.

---

## Warnings for Future AI Agents

- **No asumir que `pending_claims` del vendor equivale a claims sin pago de aseguradora** — verificar si incluye patient balance.
- **No asumir que Monday.com API retorna error cuando falla** — siempre hacer GET después de PUT/POST para verificar.
- **No incluir registros de Hispano en análisis de payment cycle time con 835** — Hispano usa capitation vía Practice Choice con posting manual, no tiene 835.
- **ClaimsAnaliticPremier.xlsx tiene problemas de compatibilidad con openpyxl** — intentar alternativas desde el inicio.
- **Premier tiene contrato directo 835 con Oscar; Hispano conecta vía MSO Practice Choice (manual)** — son flujos de pago fundamentalmente distintos.
- **Al crear batch mutations en Monday.com, siempre incluir aliases** — sin alias, el batch completo falla sin error descriptivo.
