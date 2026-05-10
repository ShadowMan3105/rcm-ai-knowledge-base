# Blueprint: Dashboards Ejecutivos RCM desde SQLite hasta React — HF Multi-Clínica

## Summary
Pipeline completo de análisis de Revenue Cycle Management para Hispano Medical Group (12 clínicas DFW). Se transformaron datos crudos del vendor externo (PDFs + exports) en dashboards ejecutivos interactivos en React, con una base de datos SQLite de 45,000+ claims verificados. El resultado fue un informe ejecutivo accionable previo a la transición in-house de billing.

## Context
HF estaba operando con un vendor externo de billing en software propietario. Con la transición in-house en marcha (plataforma IKON), se necesitaba un análisis ejecutivo completo del estado actual: tasas de denegación por clínica, pérdidas por Timely Filing, rendimiento por aseguradora, y tendencias de mejora. El CEO (familiaridad moderada con billing) era la audiencia principal.

## Approach / Strategy

1. **Extracción de datos**: `pdftotext -layout` sobre PDFs del vendor → claim blocks delimitados por `"Claim #:"` → Python parsing → SQLite.
2. **Validación (reconciliación primero)**: verificar claim counts por clínica contra totales globales antes de cualquier análisis. Corregir errores de parsing antes de proceder.
3. **Exclusiones obligatorias**: Category II CPT codes (sufijo F), pacientes bajo capitation, manual postings para cálculos de payment cycle.
4. **Corrección de clasificación**: ~2,637 claims con patient balance (copay/deductible) estaban erróneamente marcados como "pending" — distinguir insurance-unresolved de paid-with-patient-balance.
5. **Análisis en capas**: por clínica + por aseguradora + por categoría de denegación simultáneamente.
6. **Dos artefactos diferenciados**: dashboard histórico completo (Oct 2024–Mar 2026) + reporte de tendencias de 12 meses (Abr 2025–Mar 2026).

## Final Blueprint

### Pipeline de datos
```
PDFs del vendor
  → pdftotext -layout (subprocess Python)
  → split por "Claim #:" delimiter
  → parse campos: fecha, CPT, aseguradora, monto, estado, denial_reason
  → exclusiones: Category II CPT (sufijo F), capitation flag
  → SQLite master_claims.db
  → Python aggregation scripts → DATA JSON objects embebidos en JSX
  → React + Recharts dashboards
```

### Dos dashboards React producidos
- **rcm_executive_report.jsx**: KPIs globales, sección por clínica con KPIs + gráficas mensual + tabla de aseguradoras + causas de denegación + resumen ejecutivo en prosa. Periodo Oct 2024–Mar 2026.
- **rcm_trends_report.jsx**: Comparativa inicio vs últimos 3 meses por clínica, evolución de causas de denegación por mes (área chart apilada), drill-down por causa individual. Periodo Abr 2025–Mar 2026.

### Métricas globales verificadas
| Métrica | Valor |
|---|---|
| Total claims | 15,517 |
| Total facturado | $3,330,100 |
| Total cobrado | $995,884 (29.9%) |
| Claims denegados | 2,279 (14.7%) |
| Perdido Timely Filing | $97,908 — 363 claims irrecuperables |
| Clínicas analizadas | 12 (excl. Garland como caso especial) |

### Top causas de denegación por monto
1. Out of Network: $98,924 (Premier el más afectado: $72,272)
2. Timely Filing: $97,908 (único 100% irrecuperable)
3. Patient Responsibility: $58,136
4. Eligibility/Membership: $47,452

### Clínicas prioritarias
| Clínica | Denial Rate | Nota crítica |
|---|---|---|
| Garland | 85.7% | Solo 7 claims, $0 cobrado, todos Baylor |
| Coit | 27.8% | Peor tasa estructural, 17.2% collection rate |
| Josey Lane | 18.7% | $19,460 en Timely Filing |
| Premier | 11.0% | Mayor volumen; repunte Mar 2026 al triplicar claims |

### Tendencias confirmadas (12 meses)
- Timely Filing: 77–156 claims/mes (Abr 2025) → 0 en Mar 2026 ✅
- Authorization/Referral: 119 en Jun 2025 → 0 desde Nov 2025 ✅
- Premier: 66.3% denial rate → 2.6% (volumen ×16) ✅
- Codificación: emergió como nuevo problema (pico 58 claims Dic 2025) ⚠️

## Results / Verification
- Reconciliación ejecutada: claim counts por clínica suman exactamente al total global (15,517).
- Corrección de ~2,637 claims mal clasificados validada contra fuente.
- Dashboards renderizados y revisados por Billing Director (Seidel Delgado) antes de presentación ejecutiva.
- Datos etiquetados como "Base de datos v2 verificada" en el dashboard.

## Reusable Components
- Patrón de exclusión de Category II CPT codes (aplicable a cualquier análisis RCM USA)
- Estructura de doble dashboard (histórico + tendencias) para grupos médicos multi-clínica
- Categorías de denegación estandarizadas con action items por categoría (ver ACTIONS dict en JSX)
- Pipeline SQLite → JSON embebido en JSX (evita dependencia de backend para dashboards ejecutivos)

## Related Entries
- `rcm-operations/denial-tracker-monday-board/` — Board de seguimiento de denials en Monday.com
- `rcm-operations/cpt-gap-analysis/` — Análisis de oportunidades CPT vs competidores
- `billing-config/dual-architecture-ikon-ecw/` — Plan de transición in-house

## Tags
rcm, revenue-cycle, denial-management, claims-analytics, sqlite, react-dashboard, recharts, multi-clinic, timely-filing, cpt-analysis, hispano-medical, dfw, executive-report, billing-transition, category-ii-cpt, capitation, 835-remittance

## Date
2026-05

## Status
verified
