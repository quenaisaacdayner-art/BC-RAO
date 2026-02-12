# Plano Completo de Debug & Limpeza - BC-RAO

**Criado:** 2026-02-12
**Escopo:** Todas as 5 fases concluidas (backend + frontend)
**Objetivo:** Localizar bugs, remover codigo desnecessario, criar testes, validar integracao

---

## Estado Atual

### Bugs Conhecidos (Diagnosticados mas NAO Corrigidos)
| ID | Fase | Problema | Status |
|----|------|----------|--------|
| BUG-01 | 4 | SSE Event Name Mismatch - draft generation SSE nunca completa | Diagnosticado, NAO corrigido |
| BUG-02 | 4 | Stage 3 navega para /profiles ao inves de /analysis | Diagnosticado, NAO corrigido |
| BUG-03 | 4 | ISC forEach error (fix aplicado commit 2806c17) | Fix no codigo, precisa verificar |
| BUG-04 | 5 | `monitored_posts` vs `active_monitors` naming mismatch | Diagnosticado |
| BUG-05 | 5 | Scheduler periodico nao integrado no startup do app | Audit identificou |
| BUG-06 | 5 | Account status usa subscription.plan como proxy | Audit identificou |

### Tech Debt do Milestone Audit
- Celery workers usam asyncio ao inves de Celery + Redis real
- RLS nao verificado em todas as tabelas
- Email service (Resend) nao configurado
- Monitor slot limits nao enforced
- Documentacao incompleta (VERIFICATION.md faltando em fases 1, 2, 5)

### Testes
- **Zero testes** no backend e frontend

---

## Arquitetura do Plano de Debug

### Equipes de Agentes (4 Ondas Sequenciais)

```
ONDA 1: DIAGNOSTICO (Paralelo)
  ├── Equipe A: Backend Bug Scanner (fases 1-5)
  ├── Equipe B: Frontend Bug Scanner (fases 1-5)
  └── Equipe C: Dead Code Scanner (backend + frontend)

ONDA 2: CORRECAO (Paralelo apos Onda 1)
  ├── Equipe D: Backend Bug Fixer
  ├── Equipe E: Frontend Bug Fixer
  └── Equipe F: Dead Code Remover

ONDA 3: TESTES (Paralelo apos Onda 2)
  ├── Equipe G: Backend Test Writer (pytest)
  └── Equipe H: Frontend Test Writer (vitest/jest)

ONDA 4: VALIDACAO (Sequencial apos Onda 3)
  └── Equipe I: Integration Tester (E2E validation)
```

---

## ONDA 1: DIAGNOSTICO

### Equipe A: Backend Bug Scanner

**Missao:** Varrer todo o backend procurando bugs, inconsistencias, e problemas potenciais.

**Escopo por Fase:**

#### Fase 1 - Foundation (bc-rao-api/app/)
- [ ] A1.1: Verificar auth flow completo (signup → JWT → refresh → logout)
- [ ] A1.2: Verificar config.py - variaveis de ambiente faltando/defaults perigosos
- [ ] A1.3: Verificar dependencies.py - JWT validation edge cases
- [ ] A1.4: Verificar main.py - CORS configuration, middleware order
- [ ] A1.5: Verificar error handling (utils/errors.py) - respostas consistentes

#### Fase 2 - Collection (bc-rao-api/app/services/)
- [ ] A2.1: collection_service.py - error handling em chamadas Apify
- [ ] A2.2: regex_filter.py - regex injection, edge cases
- [ ] A2.3: collection_worker.py - task failure recovery, timeout handling
- [ ] A2.4: apify_client.py - connection timeout, retry logic
- [ ] A2.5: API v1/collection.py - SSE progress stream consistency

#### Fase 3 - Pattern Engine (bc-rao-api/app/analysis/)
- [ ] A3.1: nlp_pipeline.py - SpaCy model loading failures
- [ ] A3.2: pattern_extractor.py - empty data handling
- [ ] A3.3: scorers.py - division by zero, NaN propagation
- [ ] A3.4: analysis_service.py (23.6KB) - full review do maior service
- [ ] A3.5: analysis_worker.py - auto-trigger from collection reliability

#### Fase 4 - Draft Generation (bc-rao-api/app/generation/)
- [ ] A4.1: prompt_builder.py - prompt injection vulnerabilities
- [ ] A4.2: isc_gating.py - ISC threshold logic correctness
- [ ] A4.3: blacklist_validator.py - pattern matching edge cases
- [ ] A4.4: generation_service.py - LLM error handling
- [ ] A4.5: generation_worker.py - SSE event format (BUG-01 related)
- [ ] A4.6: v1/drafts.py (18.5KB) - full review do maior route file

#### Fase 5 - Monitoring (bc-rao-api/app/)
- [ ] A5.1: monitoring_service.py - dual-check logic correctness
- [ ] A5.2: monitoring_worker.py (15.8KB) - scheduler, audit task
- [ ] A5.3: reddit_client.py - auth vs anon request handling
- [ ] A5.4: email_service.py - Resend integration readiness
- [ ] A5.5: v1/monitoring.py - endpoint consistency

#### Cross-Phase Backend
- [ ] AX.1: Supabase client - connection pooling, error recovery
- [ ] AX.2: Inference client - cost tracking accuracy, retry logic
- [ ] AX.3: Task runner - Redis state management edge cases
- [ ] AX.4: Security utils - input sanitization completeness

### Equipe B: Frontend Bug Scanner

**Missao:** Varrer todo o frontend procurando bugs de UI, state management, e API integration.

#### Fase 1 - Foundation (bc-rao-frontend/)
- [ ] B1.1: middleware.ts - auth redirect logic, edge cases
- [ ] B1.2: lib/supabase/client.ts + server.ts - session handling
- [ ] B1.3: login-form.tsx + signup-form.tsx - validation, error display
- [ ] B1.4: app-sidebar.tsx - navigation state, active page highlight
- [ ] B1.5: layout.tsx (root + dashboard) - theme provider, font loading

#### Fase 2 - Collection
- [ ] B2.1: collect/page.tsx - SSE connection handling, error recovery
- [ ] B2.2: ProgressTracker.tsx - progress state accuracy
- [ ] B2.3: PostGrid.tsx + PostFilters.tsx - filter state, empty states
- [ ] B2.4: PostDetailModal.tsx - data loading, close behavior
- [ ] B2.5: FunnelStats.tsx - number formatting, zero data

#### Fase 3 - Pattern Engine
- [ ] B3.1: profiles/page.tsx - data loading, empty state
- [ ] B3.2: profiles/[subreddit]/page.tsx - ISCGauge, ArchetypePie
- [ ] B3.3: analysis/page.tsx - scoring breakdown display
- [ ] B3.4: blacklist/page.tsx - CRUD operations, validation
- [ ] B3.5: ManualAnalysisTrigger.tsx - trigger reliability

#### Fase 4 - Draft Generation
- [ ] B4.1: drafts/new/page.tsx - SSE mismatch (BUG-01), ISC loading (BUG-03)
- [ ] B4.2: GenerationForm.tsx - form validation, ISC gating UI
- [ ] B4.3: DraftEditor.tsx - edit, save, approve flow
- [ ] B4.4: DraftActions.tsx - copy, discard, approve handlers
- [ ] B4.5: StageIndicator.tsx - stage 3 URL (BUG-02), visual states
- [ ] B4.6: campaign-stages.ts - stage URL mapping correctness

#### Fase 5 - Monitoring
- [ ] B5.1: monitoring/page.tsx - stats loading, naming mismatch (BUG-04)
- [ ] B5.2: MonitoringStats.tsx - stat calculation accuracy
- [ ] B5.3: PostCard.tsx + StatusFilter.tsx - filter/display consistency
- [ ] B5.4: ShadowbanAlert.tsx - alert trigger conditions
- [ ] B5.5: "I posted this" button on draft editor - URL registration flow

#### Cross-Phase Frontend
- [ ] BX.1: lib/api.ts - error handling, token refresh
- [ ] BX.2: lib/sse.ts - SSE utility consistency across all uses
- [ ] BX.3: All API proxy routes (26 files) - error propagation, timeouts
- [ ] BX.4: hooks/ - debounce, mobile detection correctness
- [ ] BX.5: TypeScript types - any/unknown usage, missing types

### Equipe C: Dead Code Scanner

**Missao:** Identificar codigo morto, imports nao usados, funcoes/componentes orfaos.

#### Backend Dead Code
- [ ] C1.1: Imports nao usados em todos os .py files
- [ ] C1.2: Funcoes/metodos definidos mas nunca chamados
- [ ] C1.3: Modelos Pydantic nao usados em nenhum endpoint
- [ ] C1.4: Rotas definidas mas nao registradas no router
- [ ] C1.5: Variaveis de configuracao definidas mas nunca lidas
- [ ] C1.6: Workers/tasks definidos mas nunca invocados

#### Frontend Dead Code
- [ ] C2.1: Imports nao usados em todos os .ts/.tsx files
- [ ] C2.2: Componentes exportados mas nunca importados
- [ ] C2.3: API proxy routes sem pagina correspondente
- [ ] C2.4: Hooks definidos mas nunca usados
- [ ] C2.5: CSS/Tailwind classes duplicadas ou conflitantes
- [ ] C2.6: Tipos/interfaces definidos mas nunca referenciados

---

## ONDA 2: CORRECAO

### Equipe D: Backend Bug Fixer

**Prioridade de correcao:**

| Prioridade | Bug | Impacto |
|------------|-----|---------|
| P0 (Critico) | SSE backend events format (BUG-01) | Geracao de drafts nao funciona |
| P0 (Critico) | Scheduler startup integration (BUG-05) | Monitoring nao roda automaticamente |
| P1 (Alto) | Monitor slot limits (ORCH-07) | Sem controle de uso |
| P1 (Alto) | RLS verification (INFR-01) | Seguranca de dados |
| P2 (Medio) | Account status proxy (BUG-06) | Logica fragil |
| P2 (Medio) | Todos os bugs novos da Onda 1 | Varia |

**Processo por bug:**
1. Ler diagnostico completo
2. Implementar fix minimo (sem over-engineering)
3. Testar fix localmente
4. Commitar com mensagem `fix(phaseN): descricao`

### Equipe E: Frontend Bug Fixer

**Prioridade de correcao:**

| Prioridade | Bug | Impacto |
|------------|-----|---------|
| P0 (Critico) | SSE frontend event listeners (BUG-01) | Geracao de drafts quebrada |
| P0 (Critico) | Stage 3 URL navigation (BUG-02) | Navegacao errada |
| P1 (Alto) | ISC forEach verification (BUG-03) | Pode ainda falhar |
| P1 (Alto) | monitored_posts naming (BUG-04) | Stage 5 nao ativa |
| P2 (Medio) | Todos os bugs novos da Onda 1 | Varia |

**Processo por bug:**
1. Ler diagnostico completo
2. Implementar fix minimo
3. Verificar no browser (dev server)
4. Commitar com mensagem `fix(phaseN): descricao`

### Equipe F: Dead Code Remover

**Regras:**
- So remover codigo que tem 100% certeza que e morto
- Nunca remover codigo que "talvez" seja usado
- Commitar remocoes em batches por fase
- Mensagem: `refactor(phaseN): remove dead code`

---

## ONDA 3: TESTES

### Equipe G: Backend Test Writer (pytest)

**Setup necessario:**
```
pip install pytest pytest-asyncio httpx
```

**Estrutura de testes:**
```
bc-rao-api/tests/
├── conftest.py              # Fixtures: mock supabase, mock redis, test client
├── test_auth.py             # Auth endpoints (signup, login, refresh, logout)
├── test_campaigns.py        # Campaign CRUD
├── test_collection.py       # Collection trigger, SSE progress
├── test_analysis.py         # Analysis trigger, profiles, scoring
├── test_drafts.py           # Generation, ISC gating, blacklist
├── test_monitoring.py       # Monitor registration, dual-check, alerts
├── test_services/
│   ├── test_collection_service.py
│   ├── test_analysis_service.py
│   ├── test_generation_service.py
│   └── test_monitoring_service.py
├── test_generation/
│   ├── test_isc_gating.py
│   ├── test_blacklist_validator.py
│   └── test_prompt_builder.py
└── test_utils/
    ├── test_regex_filter.py
    └── test_security.py
```

**Testes prioritarios (por risco):**
1. `test_isc_gating.py` - ISC > 7.5 bloqueia archetypes arriscados
2. `test_blacklist_validator.py` - Patterns proibidos sao rejeitados
3. `test_auth.py` - JWT validation, token refresh, unauthorized access
4. `test_regex_filter.py` - Regex pre-filter accuracy
5. `test_monitoring_service.py` - Dual-check logic, shadowban detection

### Equipe H: Frontend Test Writer (vitest)

**Setup necessario:**
```
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

**Estrutura de testes:**
```
bc-rao-frontend/__tests__/
├── setup.ts                 # Test setup, mocks
├── components/
│   ├── GenerationForm.test.tsx
│   ├── StageIndicator.test.tsx
│   ├── ISCGauge.test.tsx
│   ├── MonitoringStats.test.tsx
│   └── PostGrid.test.tsx
├── lib/
│   ├── campaign-stages.test.ts
│   ├── sse.test.ts
│   └── api.test.ts
└── hooks/
    └── use-debounce.test.ts
```

**Testes prioritarios:**
1. `campaign-stages.test.ts` - URLs corretos para cada stage
2. `sse.test.ts` - SSE connection, event handling, reconnection
3. `GenerationForm.test.tsx` - ISC gating UI, form validation
4. `StageIndicator.test.tsx` - Stage progression, click navigation
5. `api.test.ts` - Error handling, auth token inclusion

---

## ONDA 4: VALIDACAO

### Equipe I: Integration Tester

**Testes E2E (manual ou automatizado):**

| # | Fluxo | Passos | Validacao |
|---|-------|--------|-----------|
| E2E-1 | Onboarding | Signup → Dashboard → Create Campaign | User criado, campaign salva |
| E2E-2 | Collection | Campaign → Trigger Collection → View Posts | Posts coletados, progress funciona |
| E2E-3 | Analysis | Posts → Trigger Analysis → View Profiles | Profiles gerados, ISC scores |
| E2E-4 | Generation | Profile → Select Subreddit → Generate Draft | Draft criado, SSE completa |
| E2E-5 | Monitoring | Draft → "I Posted This" → URL Registration | Monitor ativo, stats atualizados |
| E2E-6 | Full Loop | E2E-1 → E2E-5 em sequencia | Todo o pipeline funciona |

**Checklist de Integracao Cross-Phase:**
- [ ] Collection auto-triggers analysis
- [ ] Analysis profiles load in generation form
- [ ] ISC gating blocks correctly when ISC > 7.5
- [ ] Draft editor shows scores from analysis
- [ ] Stage indicator progresses correctly (1→2→3→4→5)
- [ ] Monitoring stats update on dashboard
- [ ] Blacklist feedback loop (removal → pattern → blacklist)

---

## Cronograma de Execucao

```
ONDA 1: DIAGNOSTICO (~45 min com agentes paralelos)
  ├── Equipe A (Backend Scanner)  ──────▶ RELATORIO-A.md
  ├── Equipe B (Frontend Scanner) ──────▶ RELATORIO-B.md
  └── Equipe C (Dead Code Scanner) ─────▶ RELATORIO-C.md

ONDA 2: CORRECAO (~60 min com agentes paralelos)
  ├── Equipe D (Backend Fixer)  ────────▶ commits fix()
  ├── Equipe E (Frontend Fixer) ────────▶ commits fix()
  └── Equipe F (Dead Code Remover) ─────▶ commits refactor()

ONDA 3: TESTES (~45 min com agentes paralelos)
  ├── Equipe G (Backend Tests)  ────────▶ pytest passing
  └── Equipe H (Frontend Tests) ────────▶ vitest passing

ONDA 4: VALIDACAO (~30 min)
  └── Equipe I (Integration) ──────────▶ VALIDATION-REPORT.md
```

---

## Criterios de Sucesso

### Onda 1 Completa Quando:
- [ ] Todos os bugs catalogados com severidade e fase
- [ ] Todo o dead code identificado com justificativa
- [ ] Relatorios escritos em .planning/debug/

### Onda 2 Completa Quando:
- [ ] Todos os bugs P0 corrigidos e commitados
- [ ] Todos os bugs P1 corrigidos e commitados
- [ ] Dead code removido e commitado
- [ ] Nenhum bug P0/P1 remanescente

### Onda 3 Completa Quando:
- [ ] Backend: pytest roda com 0 falhas
- [ ] Frontend: vitest roda com 0 falhas
- [ ] Cobertura minima nos paths criticos (ISC gating, auth, SSE)

### Onda 4 Completa Quando:
- [ ] 6 fluxos E2E validados
- [ ] Cross-phase integration confirmada
- [ ] Validation report escrito

---

## Como Executar Este Plano

Para iniciar, confirme a onda que deseja executar:

1. **`/gsd:debug onda-1`** - Iniciar diagnostico com 3 agentes paralelos
2. **`/gsd:debug onda-2`** - Iniciar correcoes (requer Onda 1)
3. **`/gsd:debug onda-3`** - Iniciar testes (requer Onda 2)
4. **`/gsd:debug onda-4`** - Iniciar validacao (requer Onda 3)
5. **`Executar tudo`** - Rodar ondas 1→4 sequencialmente

---
*Plano criado: 2026-02-12*
*Baseado em: ROADMAP.md, v1-MILESTONE-AUDIT.md, 3 debug sessions existentes*
