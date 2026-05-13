# Lessons Learned — Multi-Clinic Paid Claims Consolidation

**Entry ID**: `KB-2026-0005-multi-clinic-paid-claims-consolidation-pdf`
**Date**: 2026-05-12
**Author**: claude-opus-4-7

Errores que costaron tiempo y patrones que SÍ funcionaron.

---

## 1. Formato drift de eCW — **el bug más caro de la sesión**

eCW v12 emite la misma "PAYMENT DETAIL REPORT" con **headers distintos** según el mes. APRIL 2026 usa un set de labels, FEBRUARY 2026 usa otro. Si el parser hardcodea un solo set, falla silenciosamente con 0 service lines extraídas.

| Concepto | Formato APR 2026 | Formato FEB 2026 |
|---|---|---|
| Título PDF | `PAYMENT DETAIL REPORT` | `PAYMENTS REPORT DETAILS` |
| Claim header | `Ins:` `Copay:` | `Insurance:` `Copayment:` |
| Column header | `DOS` `DOB` `Co-Ins` | `D.O.S` `D.O.B` `CO-Ins` |
| Curr Bal label | `Curr Bal:` | `Current Bal:` |
| Insurance summary | `WLPNT, WELLPOINT Trans N Insurance Summary` | `WLPNT, WELLPOINT Transactions N Insurance Summary` |
| Provider summary | `{PROVIDER} Trans N Provider Summary` | `Transactions N REPORT SUMMARY` (sin nombre) |
| Provider line | `Provider Name: X` | `Provider: X` (en filter page) |
| Insurance name en summary | full `BLUECROSS BLUESHIELD OF TEXAS` | a veces truncado `BLUECROSS BLUESHIELD OF` |
| Footer time | `04:00 PM` (zero-padded) | `7:38:24 PM` (sin zero pad, con segundos) |

**Lección — patrón a aplicar siempre**:
- Cuando se parsea un PDF emitido por un sistema empresarial (eCW, NextGen, Athena, etc.) sobre múltiples períodos, **probar el parser contra al menos 2 meses distintos** antes de declararlo correcto.
- Construir todos los regex con **alternancia** desde el inicio: `r'(?:Trans|Transactions)'`, `r'(?:Ins|Insurance):'`, `r'(?:Curr|Current)\s+Bal:'`.
- Validar con un **smoke test**: `len(service_lines) > 0` y `provider_summary['trans'] == len(service_lines)`.

---

## 2. Provider name viene **del nombre de archivo**, NO del PDF body

El PDF body puede:
- Truncar el nombre (`FORT H WORTH` en lugar de `FORT WORTH`).
- Faltar en filter pages.
- Aparecer con casing inconsistente.

**Lección**: la inventario step usa regex sobre filename y eso es la fuente canónica. Después del parse, **sobrescribir** el `provider` en el dict parseado con el del filename. Si no se hace, los GROUP BY agregaciones se rompen silenciosamente.

```python
# En orchestrator después de parse_one()
if parsed.get('provider') != item['provider']:
    parsed['provider'] = item['provider']
    for k in ('rows', 'service_lines'):
        for r in parsed.get(k, []):
            r['provider'] = item['provider']
```

---

## 3. PDF escaneado vs PDF text-based — detección **antes** de parsear

3 PDFs de Premier FEB 2026 son imágenes (sin capa de texto). El parser pdfplumber se tarda **5+ minutos** intentando extraer nada antes de timeout. Esto bloqueó la corrida completa el primer intento.

**Patrón**: pre-check de la página 2 (no la 1, que suele ser filter page):

```python
def is_scanned_pdf(path):
    with pdfplumber.open(path) as pdf:
        if len(pdf.pages) < 2:
            return False
        text = pdf.pages[1].extract_text() or ''
        return len(text.strip()) < 20
```

Si `True`, registrar en `missing` y **persistir el estado missing en el caché** para que reruns no re-intenten.

---

## 4. **Insurance summaries** del PDF están infladas vs **provider summary**

Cuando un claim tiene secuencia PRI + SEC, o un check fue procesado en múltiples páginas, el **insurance summary** los cuenta múltiples veces. El **provider summary** los deduplica.

**Lección**: para totales por aseguradora, **NO** usar `Σ insurance_summary.bill_amt` como ground truth. Es más confiable agregar desde `service_lines` y luego comparar contra `provider_summary` (que es la única fuente verificada por eCW).

---

## 5. **InsuranceCode** > InsuranceName como join key

`InsuranceName` aparece truncado en summaries (`BLUECROSS BLUESHIELD OF` sin `TEXAS`) y a veces con espacios diferentes. `InsuranceCode` (BCBSTX, OSCAR, etc.) es estable.

**Patrón**: cuando construyas pivots o haces JOIN, **siempre** usa `insurance_code`. Trata `insurance_name` como display-only.

---

## 6. **Check# discrepancias** — siempre descomponer antes de declarar bug

Las dos discrepancias del proyecto (Premier MAR +$2,599.72 y Josey FEB −$106.99) parecían parser bugs al principio. Después de descomponer por check#:

- Premier MAR: 1 OSCAR check de $2,599.72 aparece solo en PAYMENT (probable cutoff de posting date entre los dos reportes), y un wash de $99.02 donde el mismo check tiene id distinto en cada reporte (`RC-` placeholder vs `6084270093`).
- Josey FEB: 1 reversal de OSCAR −$106.99 que RECEIVABLES no lista (no hubo cash recibido).

**Lección — heurística contable**:
> `Σ PMT.payment − Σ REC.posting_amt ≠ 0` casi siempre se explica por: (a) reversals/takebacks (negativos en PMT, ausentes en REC), (b) checks aplicados en mes distinto de posting, (c) identificadores faltantes en uno de los dos reports (`RC-` placeholder).

Antes de tocar el parser, **siempre** correr una agregación por check# y comparar ambos sets.

---

## 7. **Mismo cheque, identificador truncado distinto**

eCW a veces emite el mismo check# con longitud distinta entre PDFs (`DINIEDUNITED043` vs `DINIEDUNITED0430`). Un parse-time fuzzy match (`startswith` en ambas direcciones) es necesario para no contar el mismo check dos veces como "orphan" + "missing".

---

## 8. PAYMENT incluye claims de **meses anteriores**

El filtro de PAYMENT es Posting Date, no Bill Date. Un check posteado en marzo puede aplicarse a un claim facturado en enero. Esto significa:
- **No esperar 1:1** entre service-lines de ALL_CLAIM y de PAYMENT en el mismo mes.
- El Master_Enriched LEFT JOIN tiene status `UNRESOLVED` (~1.8%) y `OVERPAID` (~7.1%) precisamente por esto. **No son errores, son la realidad operacional.**

---

## 9. **Receivables.Amt ≠ Receivables.PostingAmt** = pagos no posteados aún

REC tiene dos columnas de dinero: `Amt` (recibido) y `Posting Amt` (aplicado a claims). La diferencia es **dinero en suspenso** — ERA recibida pero no posteada aún. Es un KPI de salud del workflow de posteo.

**Lección**: exponer ese delta como columna `NotPostedDiff` y conditional-format en amarillo cuando ≠ 0. Es una señal accionable para el equipo de posteo.

---

## 10. **Pickle cache con persistencia de errores**

El primer instinto es cachear solo successes. Pero los PDFs scanned pueden re-aparecer en cada run y volver a colgar 5 min. Lección: el caché **también** persiste el estado `missing` (con `{'_missing': {...}}` como sentinel). Permite re-runs idempotentes y rápidos.

---

## 11. **autosize** en openpyxl es lento — limitar max_width

Iterar todas las celdas para calcular ancho es O(rows × cols). En 10K rows × 26 cols se notaba. Solución: `max_width=22` como cap, y limit pass a sample de primeras N rows. (Aquí mantuvimos full pass porque 10s es aceptable; documentar el trade-off.)

---

## 12. **Provider summary del PDF = ground truth absoluto**

eCW imprime un footer con totals que **eCW mismo calculó**. Eso es el ground truth. Si tu agregación desde service-lines no cuadra contra ese footer, tu parser tiene bug. Siempre validar:

```python
sum(sl['bill_amt'] for sl in parsed['service_lines']) == parsed['provider_summary']['bill_amt']  # debería pasar
```

Si no pasa, hay parser bug o falta extraer alguna page.

---

## Anti-patrones que NO hacer

- **NO** hardcodear un único formato de header. Siempre alternancia de regex.
- **NO** trustear `provider` ni `insurance_name` del PDF body — usar filename + insurance_code.
- **NO** dejar que pdfplumber re-intente PDFs sin capa de texto.
- **NO** mezclar agregación desde insurance summary con agregación desde service lines como si fueran equivalentes.
- **NO** declarar bug del parser sin descomponer por check#.
- **NO** correr el parser sin smoke test (`len(service_lines) > 0`).

---

## Patrones que SÍ funcionaron

- **ProcessPoolExecutor con workers=6** en máquina de 8 cores: óptimo para parsing pdfplumber-bound.
- **Pickle por (type, provider, month)** como cache granular: re-runs surgicalmente borrando solo el affected slot.
- **Status enum en Master_Enriched** (PAID_FULL/PARTIAL/NOT_PAID/OVERPAID/UNRESOLVED): suficiente para que Dr. Seidel filtre y actúe sin pivotar.
- **Conditional formatting con `CellIsRule(notEqual, 0)`** sobre las columnas `Diff_*`: visual signal inmediata sin "ver todos los flags".
- **README sheet como primera tab** con diccionario + reglas contables: nuevos usuarios entienden el workbook en 2 min sin tocar al autor.
