# BC-RAO: System Specification & Architectural Defense

---

# PARTE 1: DEFESA ARQUITETURAL (Português)

## 1. Lógica do Schema

O schema foi desenhado ao redor de um princípio central: **cada módulo do BC-RAO é um produtor e consumidor de dados, e a integridade entre eles depende de contratos explícitos no banco**.

### Por que essas tabelas existem

**`users` + `subscriptions`**: Separadas intencionalmente. O Supabase Auth gerencia identidade, mas a lógica de billing (trial, planos, limites) vive em `subscriptions` controlada pelo nosso backend. Isso evita acoplamento entre autenticação e monetização — se migrarmos de Stripe para outro processador, a tabela `users` não é afetada.

**`campaigns`**: É a unidade organizacional do usuário. Um founder pode estar validando 2-3 ideias simultaneamente. Cada campanha tem suas próprias keywords, subreddits alvo, e contexto de produto. Sem essa separação, o Módulo 2 (Pattern Engine) misturaria sinais de comunidades diferentes, corrompendo o ISC.

**`raw_posts`**: O coração do Módulo 1. A coluna `raw_text` é **mandatória e imutável** — é o snapshot de segurança do PRD. Quando o Reddit deleta um post, o link retorna 404, mas nosso sistema ainda tem o texto original para alimentar o aprendizado negativo do Módulo 4. A coluna `embedding` (pgvector) existe para busca semântica futura, mas no MVP ela é populada apenas para o Top 10% dos posts processados por IA, controlando custo.

**`shadow_table`**: É o sistema nervoso do Módulo 4 (Orchestrator). Cada post publicado pelo usuário é registrado aqui com `isc_at_post` — o índice de sensibilidade da comunidade **no momento exato da postagem**. Isso permite correlação temporal: "posts publicados quando ISC > 8 têm 3x mais chance de remoção". Sem essa coluna, perderíamos a capacidade de aprendizado contextual.

**`syntax_blacklist`**: A memória de longo prazo do sistema. Quando um post é removido, os termos e padrões que causaram a remoção são injetados aqui **por subreddit**. O Módulo 3 consulta esta tabela antes de cada geração, garantindo que erros passados nunca se repitam na mesma comunidade.

**`generated_drafts`**: Rastreabilidade completa. Cada draft gerado pelo Módulo 3 é salvo com o `archetype` usado, o `model_used` (via OpenRouter), e o `token_cost`. Isso permite auditoria de custos e análise de qual arquétipo gera melhor engajamento por comunidade.

**`usage_tracking`**: Enforcement de limites em tempo real. O campo `action_type` categoriza cada ação contável (collect, analyze, generate, monitor), e o backend verifica contra os limites do plano antes de executar qualquer operação.

### Como se relacionam

O fluxo de dados segue a pipeline dos 4 módulos:

```
campaigns → raw_posts → (Pattern Engine scores) → generated_drafts → shadow_table
                                                                          ↓
                                                                   syntax_blacklist
                                                                   (feedback loop)
```

Cada tabela tem `user_id` como foreign key para `auth.users`, e Row Level Security (RLS) do Supabase garante isolamento total entre tenants.

---

## 2. Camada de Inference

### Por que OpenRouter e não chamadas diretas

O BC-RAO tem **três tipos distintos de chamada de IA**, cada um com requisitos diferentes de custo e qualidade:

1. **Classificação de arquétipo** (Módulo 2): Tarefa simples, alto volume → modelo barato (Haiku, Gemini Flash)
2. **Análise de ritmo sintático** (Módulo 2): Processamento local via SpaCy → **zero custo de API**
3. **Geração condicionada** (Módulo 3): Tarefa complexa, criativa → modelo mais capaz (Sonnet, GPT-4o-mini)

OpenRouter permite **trocar o modelo por endpoint sem alterar código**. Se amanhã sair um modelo 50% mais barato para classificação, alteramos uma variável de ambiente, não uma classe Python. Isso é crítico para um produto onde o custo de IA é o principal componente variável do COGS.

### Arquitetura anti-lock-in

```python
# O código nunca faz isso:
from openai import OpenAI  # ❌ Lock-in direto

# O código sempre faz isso:
from app.inference import InferenceClient  # ✅ Abstração interna
client = InferenceClient(task="classification")  # Router decide o modelo
```

O `InferenceClient` interno resolve qual modelo usar baseado na tarefa, tracked automaticamente em `usage_tracking`. Se OpenRouter ficar fora do ar, o fallback é chamada direta ao provider — mas isso é exceção, não regra.

---

## 3. Riscos Críticos

### Risco 1: Custo descontrolado de Apify + LLM

O maior gargalo financeiro é a combinação de créditos Apify (coleta) + tokens LLM (geração). Um usuário no plano Starter com 5 subreddits e 50 drafts/mês pode facilmente consumir $15-25 em custos variáveis contra uma receita de $49.

**Mitigação arquitetural:**
- A Camada B (Regex) do Módulo 1 filtra localmente **antes** de qualquer chamada de IA, reduzindo volume de tokens em ~80%
- Apenas o Top 10% dos posts vai para processamento LLM
- SpaCy roda localmente para análise sintática (ritmo, formalidade) — custo zero
- `usage_tracking` impõe hard limits por billing cycle, não por dia, permitindo uso flexível dentro do mês

### Risco 2: Detecção tardia de Shadowban

Conforme o próprio PRD identifica, o shadowban é o inimigo silencioso. O post aparece normal para o autor, mas é invisível para a comunidade. Se o Módulo 4 só verificar via HTTP 200, nunca detectará shadowbans.

**Mitigação arquitetural:**
- O worker de monitoramento faz **duas verificações**: uma autenticada (perspectiva do autor) e uma anônima (perspectiva pública)
- Se o post retorna 200 na sessão autenticada mas não aparece na busca anônima por 2 verificações consecutivas, o status muda para `Shadowbanned`
- Alerta de emergência é disparado imediatamente, com instrução de pausar postagens por 48h
- Para contas novas (primeiros 3 posts), o intervalo de verificação é reduzido de 4h para 1h

---

# PART 2: SYSTEM SPECIFICATION (English)

---

## 1. System Role

You are a Senior Python Product Engineer building the BC-RAO system — an infrastructure for social intelligence that automates market validation and organic user acquisition in sensitive digital communities. You write production-ready systems. You make final decisions and do not defer responsibility.

---

## 2. Tech Stack (Locked)

| Layer | Technology | Justification |
|-------|-----------|---------------|
| Frontend | Next.js 15 (TypeScript) + Tailwind CSS + Shadcn/UI | Dashboard, onboarding, draft editor |
| Backend | Python 3.11+ / FastAPI (async-first) | API layer, business logic, module orchestration |
| Database | Supabase (PostgreSQL + pgvector + Auth + RLS) | Multi-tenant data, semantic search, auth |
| AI Orchestration | LangChain + OpenRouter | Model abstraction, chain composition |
| NLP Local | SpaCy (en_core_web_md) | Syntax rhythm analysis, zero API cost |
| Data Collection | Apify SDK (Python) | Reddit scraping with managed actors |
| Task Queue | Celery + Redis | Async jobs: collection, monitoring, auditing |
| Scheduling | Inngest or Celery Beat | Periodic monitoring (4h/1h cycles) |
| Payments | Stripe | Subscriptions, trial management, webhooks |
| Email | Resend or SendGrid | Transactional alerts (Module 4) |
| Hosting | Vercel (frontend) + Railway/Render (backend) | Cloud-agnostic, easy scaling |

---

## 3. Product Overview

**What it does:** BC-RAO is a social intelligence platform that reads the behavioral DNA of online communities (starting with Reddit), conditions content generation to match community norms, and monitors post survival — transforming founders from "obvious marketers" into "legitimate collaborators."

**Who it's for:** Early-stage SaaS founders, indie hackers, and idea validators who need real market validation without ad spend.

**Core value:** Replaces intuition-driven community posting with a scientific process of behavioral mimicry, vulnerability injection, and negative reinforcement learning.

### Pricing (Locked)

| | Trial | Starter | Growth |
|---|---|---|---|
| Price | $0 (7 days) | $49/month | $99/month |
| Credit card required | No | Yes | Yes |
| Subreddits monitored | 3 | 5 | 10 |
| Drafts/month | 10 | 50 | Unlimited |
| Campaigns | 1 | 3 | 10 |
| Monitoring slots | 5 | 20 | 50 |
| Email alerts | ✓ | ✓ | ✓ |
| Onboarding guiado | ✓ | — | — |
| Priority support | — | — | ✓ |

---

## 4. Database Schema

### Extensions

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
```

### Core Tables

```sql
-- ============================================================
-- PROFILES (extends Supabase Auth)
-- ============================================================
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    avatar_url TEXT,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    onboarding_step INT DEFAULT 0,
    timezone TEXT DEFAULT 'UTC',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- SUBSCRIPTIONS
-- ============================================================
CREATE TYPE plan_tier AS ENUM ('trial', 'starter', 'growth');
CREATE TYPE subscription_status AS ENUM ('active', 'trial', 'past_due', 'cancelled', 'expired');

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    plan plan_tier NOT NULL DEFAULT 'trial',
    status subscription_status NOT NULL DEFAULT 'trial',
    stripe_customer_id TEXT UNIQUE,
    stripe_subscription_id TEXT UNIQUE,
    trial_starts_at TIMESTAMPTZ DEFAULT NOW(),
    trial_ends_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- ============================================================
-- CAMPAIGNS (organizational unit per user)
-- ============================================================
CREATE TYPE campaign_status AS ENUM ('active', 'paused', 'archived');

CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    product_context TEXT NOT NULL,
    product_url TEXT,
    keywords TEXT[] NOT NULL DEFAULT '{}',
    target_subreddits TEXT[] NOT NULL DEFAULT '{}',
    status campaign_status DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_campaigns_user ON campaigns(user_id);

-- ============================================================
-- RAW POSTS (Module 1 output -> Module 2 input)
-- ============================================================
CREATE TYPE post_archetype AS ENUM ('Journey', 'ProblemSolution', 'Feedback', 'Unclassified');

CREATE TABLE raw_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    subreddit TEXT NOT NULL,
    reddit_post_id TEXT NOT NULL,
    reddit_url TEXT,
    author TEXT,
    author_karma INT,
    title TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    comment_count INT DEFAULT 0,
    upvote_ratio FLOAT,
    embedding vector(1536),
    archetype post_archetype DEFAULT 'Unclassified',
    rhythm_metadata JSONB DEFAULT '{}',
    success_score FLOAT,
    engagement_score FLOAT,
    is_ai_processed BOOLEAN DEFAULT FALSE,
    reddit_created_at TIMESTAMPTZ,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(campaign_id, reddit_post_id)
);

CREATE INDEX idx_raw_posts_campaign ON raw_posts(campaign_id);
CREATE INDEX idx_raw_posts_subreddit ON raw_posts(subreddit);
CREATE INDEX idx_raw_posts_archetype ON raw_posts(archetype);
CREATE INDEX idx_raw_posts_score ON raw_posts(success_score DESC);

-- ============================================================
-- COMMUNITY PROFILES (Module 2 aggregated output)
-- ============================================================
CREATE TABLE community_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    subreddit TEXT NOT NULL,
    isc_score FLOAT NOT NULL DEFAULT 5.0,
    avg_sentence_length FLOAT,
    dominant_tone TEXT,
    formality_level FLOAT,
    top_success_hooks JSONB DEFAULT '[]',
    forbidden_patterns JSONB DEFAULT '[]',
    archetype_distribution JSONB DEFAULT '{}',
    sample_size INT DEFAULT 0,
    last_analyzed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(campaign_id, subreddit)
);

-- ============================================================
-- GENERATED DRAFTS (Module 3 output)
-- ============================================================
CREATE TYPE draft_status AS ENUM ('generated', 'edited', 'approved', 'posted', 'discarded');

CREATE TABLE generated_drafts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    subreddit TEXT NOT NULL,
    archetype post_archetype NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    vulnerability_score FLOAT,
    rhythm_match_score FLOAT,
    blacklist_violations INT DEFAULT 0,
    model_used TEXT NOT NULL,
    token_count INT,
    token_cost_usd FLOAT,
    generation_params JSONB DEFAULT '{}',
    status draft_status DEFAULT 'generated',
    user_edits TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_drafts_campaign ON generated_drafts(campaign_id);
CREATE INDEX idx_drafts_user ON generated_drafts(user_id);
CREATE INDEX idx_drafts_status ON generated_drafts(status);

-- ============================================================
-- SHADOW TABLE (Module 4 - Orchestrator)
-- ============================================================
CREATE TYPE post_lifecycle AS ENUM ('Ativo', 'Removido', '404', 'Shadowbanned', 'Auditado');

CREATE TABLE shadow_table (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    draft_id UUID REFERENCES generated_drafts(id) ON DELETE SET NULL,
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    post_url TEXT UNIQUE NOT NULL,
    subreddit TEXT NOT NULL,
    status_vida post_lifecycle DEFAULT 'Ativo',
    conversational_depth INT DEFAULT 0,
    isc_at_post FLOAT NOT NULL,
    account_status TEXT DEFAULT 'Established' CHECK (account_status IN ('New', 'WarmingUp', 'Established')),
    check_interval_hours INT DEFAULT 4,
    total_checks INT DEFAULT 0,
    last_check_status INT,
    last_check_at TIMESTAMPTZ DEFAULT NOW(),
    audit_result TEXT CHECK (audit_result IN ('SocialSuccess', 'Rejection', 'Inertia')),
    audit_completed_at TIMESTAMPTZ,
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    audit_due_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_shadow_campaign ON shadow_table(campaign_id);
CREATE INDEX idx_shadow_status ON shadow_table(status_vida);
CREATE INDEX idx_shadow_audit_due ON shadow_table(audit_due_at) WHERE audit_result IS NULL;

-- ============================================================
-- SYNTAX BLACKLIST (Negative Reinforcement Memory)
-- ============================================================
CREATE TYPE failure_category AS ENUM ('AdminRemoval', 'SocialRejection', 'Shadowban', 'Inertia');

CREATE TABLE syntax_blacklist (
    id SERIAL PRIMARY KEY,
    subreddit TEXT NOT NULL,
    forbidden_pattern TEXT NOT NULL,
    failure_type failure_category NOT NULL,
    source_post_id UUID REFERENCES shadow_table(id) ON DELETE SET NULL,
    confidence FLOAT DEFAULT 0.5,
    is_global BOOLEAN DEFAULT FALSE,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(subreddit, forbidden_pattern)
);

CREATE INDEX idx_blacklist_subreddit ON syntax_blacklist(subreddit);

-- ============================================================
-- USAGE TRACKING
-- ============================================================
CREATE TYPE usage_action AS ENUM ('collect', 'analyze', 'generate', 'monitor_register');

CREATE TABLE usage_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    action_type usage_action NOT NULL,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    token_count INT DEFAULT 0,
    cost_usd FLOAT DEFAULT 0.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_usage_user_action ON usage_tracking(user_id, action_type);
CREATE INDEX idx_usage_created ON usage_tracking(created_at);

-- ============================================================
-- EMAIL ALERT LOG
-- ============================================================
CREATE TYPE alert_type AS ENUM ('emergency', 'success', 'adjustment', 'trial_reminder', 'onboarding');

CREATE TABLE email_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    shadow_id UUID REFERENCES shadow_table(id) ON DELETE SET NULL,
    alert_type alert_type NOT NULL,
    subject TEXT NOT NULL,
    body_preview TEXT,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    delivered BOOLEAN DEFAULT FALSE
);

-- ============================================================
-- AUDIT LOG
-- ============================================================
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_action ON audit_log(action);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE raw_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE community_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE shadow_table ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_alerts ENABLE ROW LEVEL SECURITY;
```

---

## 5. API Design

### Base URL: `https://api.bcrao.app/v1`

All endpoints require JWT Bearer token from Supabase Auth, except `/auth/*` and `/billing/webhooks/*`.

### 5.1 Auth Endpoints

```
POST /auth/signup
  Body: { email, password, full_name }
  Response: { user_id, access_token, refresh_token }
  Side effects: Creates profile, subscription (trial), starts onboarding

POST /auth/login
  Body: { email, password }
  Response: { access_token, refresh_token, user: { id, plan, trial_ends_at } }

POST /auth/refresh
  Body: { refresh_token }
  Response: { access_token, refresh_token }

GET /auth/me
  Response: { user, subscription, usage_summary }
```

### 5.2 Campaign Endpoints

```
POST /campaigns
  Body: {
    name: string,
    description?: string,
    product_context: string,
    product_url?: string,
    keywords: string[],              // 5-15 items
    target_subreddits: string[]      // max per plan
  }
  Response: 201 { campaign }
  Validation: keywords min 5 max 15, subreddits max per tier, campaigns max per tier

GET /campaigns
  Response: { campaigns: Campaign[], total: int }

GET /campaigns/:id
  Response: { campaign, stats: { posts_collected, drafts_generated, active_monitors } }

PATCH /campaigns/:id
  Body: { name?, keywords?, target_subreddits?, status? }
  Response: { campaign }

DELETE /campaigns/:id
  Response: 204
```

### 5.3 Module 1 — Data Collector

```
POST /campaigns/:id/collect
  Body: {
    mode: "fresh" | "historical" | "hybrid",
    min_comments?: int (default: 5)
  }
  Response: 202 { job_id, estimated_duration_seconds }
  Rate limit: 1 concurrent collection per campaign

GET /campaigns/:id/collect/status
  Response: { job_id, status, progress: { total_found, regex_filtered, ai_processed } }

GET /campaigns/:id/posts
  Query: ?archetype=Journey&sort=success_score&limit=20&offset=0
  Response: { posts: RawPost[], total, filters_applied }

GET /campaigns/:id/posts/:post_id
  Response: { post, rhythm_metadata, success_breakdown }
```

### 5.4 Module 2 — Pattern Engine

```
POST /campaigns/:id/analyze
  Body: { force_refresh?: boolean }
  Response: 202 { job_id }

GET /campaigns/:id/community-profile
  Query: ?subreddit=SaaS
  Response: {
    subreddit, isc_score, rhythm_pattern, success_hooks,
    forbidden_patterns, archetype_distribution, sample_size, last_analyzed_at
  }

GET /campaigns/:id/scoring-breakdown
  Query: ?post_id=<uuid>
  Response: {
    vulnerability_weight, thread_depth_weight, rhythm_adherence,
    marketing_jargon_penalty, link_density_penalty, total_score
  }
```

### 5.5 Module 3 — Conditioning Generator

```
POST /campaigns/:id/drafts/generate
  Body: {
    subreddit: string,
    archetype: "Journey" | "ProblemSolution" | "Feedback",
    user_context?: string,
    tone_override?: string,
    count?: int (default: 1, max: 3)
  }
  Response: 201 {
    drafts: [{
      id, title, body, archetype,
      vulnerability_score, rhythm_match_score,
      blacklist_check: { passed, violations },
      model_used, token_cost_usd
    }]
  }
  Validation: community profile must exist, monthly limit enforced, ISC gating

GET /campaigns/:id/drafts
  Query: ?status=generated&subreddit=SaaS&limit=20
  Response: { drafts: Draft[], total }

PATCH /drafts/:id
  Body: { status?: "approved"|"discarded", user_edits?: string }
  Response: { draft }

POST /drafts/:id/regenerate
  Body: { feedback?: string }
  Response: 201 { draft }
```

### 5.6 Module 4 — Orchestrator

```
POST /monitor/register
  Body: {
    draft_id: uuid,
    post_url: string,
    account_status?: "New" | "WarmingUp" | "Established"
  }
  Response: 201 { shadow_id, monitoring_schedule, next_check_at, isc_at_post }
  Validation: monitor slot limit per plan

GET /monitor/active
  Query: ?campaign_id=<uuid>&status=Ativo
  Response: { monitored_posts: ShadowEntry[], total }

GET /monitor/:shadow_id
  Response: { shadow_entry, check_history, alerts_sent }

GET /monitor/dashboard
  Response: {
    active_count, removed_count, shadowbanned_count,
    avg_conversational_depth, success_rate, recent_alerts
  }
```

### 5.7 Subscription & Billing

```
POST /billing/checkout
  Body: { plan: "starter" | "growth" }
  Response: { checkout_url: string }

POST /billing/portal
  Response: { portal_url: string }

POST /billing/webhooks/stripe   (no auth - Stripe signature verification)
  Handles: checkout.session.completed, invoice.paid, invoice.payment_failed,
           customer.subscription.updated, customer.subscription.deleted

GET /billing/usage
  Response: {
    plan, period, limits, used, cost_breakdown
  }
```

### 5.8 Onboarding

```
GET /onboarding/status
  Response: { completed, current_step, steps }

POST /onboarding/step/:step_number/complete
  Body: { data?: any }
  Response: { next_step, completed }
```

### Standard Error Shape

```json
{
  "error": {
    "code": "PLAN_LIMIT_REACHED",
    "message": "You have used all 50 drafts for this billing period.",
    "details": { "used": 50, "limit": 50, "resets_at": "2026-03-01T00:00:00Z" }
  }
}
```

---

## 6. Inference Layer

### 6.1 OpenRouter Integration

```python
# Model routing configuration
MODEL_ROUTING = {
    "classify_archetype": {
        "model": "anthropic/claude-3-haiku-20240307",
        "max_tokens": 200,
        "temperature": 0.1,
        "fallback": "google/gemini-flash-1.5"
    },
    "generate_draft": {
        "model": "anthropic/claude-sonnet-4-20250514",
        "max_tokens": 2000,
        "temperature": 0.7,
        "fallback": "openai/gpt-4o-mini"
    },
    "score_post": {
        "model": "anthropic/claude-3-haiku-20240307",
        "max_tokens": 500,
        "temperature": 0.0,
        "fallback": "google/gemini-flash-1.5"
    },
    "extract_patterns": {
        "model": "anthropic/claude-3-haiku-20240307",
        "max_tokens": 1000,
        "temperature": 0.2,
        "fallback": "google/gemini-flash-1.5"
    },
}
```

### 6.2 Cost Control

```python
COST_CAPS = {
    "trial": 5.00,
    "starter": 15.00,
    "growth": 40.00,
}
# Enforced: SUM(cost_usd) checked before every inference call
# 80% threshold triggers frontend warning
```

### 6.3 SpaCy Local Processing (Zero Cost)

- Average sentence length
- Formality score
- Tone classification (rule-based)
- Vocabulary complexity

---

## 7. User Flow

### 7.1 Signup to First Value

```
1. SIGNUP → email/password, profile created, trial activated (7 days, no card)
2. ONBOARDING (4 steps):
   Step 1: "What's your SaaS?" → product_context, product_url
   Step 2: "Who are your people?" → select 3-5 subreddits
   Step 3: "What words describe their pain?" → keywords (5-15)
   Step 4: "Let's collect data" → triggers first Module 1 collection
3. FIRST COLLECTION → hybrid mode, 2-5 min, progress bar in dashboard
4. FIRST INSIGHT → community profile displayed (ISC, rhythm, archetypes)
5. FIRST DRAFT → user selects subreddit + archetype, Module 3 generates
6. POST & MONITOR → user posts manually, pastes URL, Module 4 monitors 7 days
7. CONVERSION → Day 5 trial reminder, Day 7 expiry, upgrade prompt
```

### 7.2 Core Loop

```
Collect → Analyze → Generate → Post (manual) → Monitor → Learn → Repeat
   M1        M2         M3        User Action       M4       M4→M2
```

---

## 8. Pricing & Usage Logic

### 8.1 Plan Limits

```python
PLAN_LIMITS = {
    "trial":   { "subreddits": 3,  "drafts_month": 10, "campaigns": 1,  "monitors": 5,  "concurrent_collections": 1 },
    "starter": { "subreddits": 5,  "drafts_month": 50, "campaigns": 3,  "monitors": 20, "concurrent_collections": 2 },
    "growth":  { "subreddits": 10, "drafts_month": -1, "campaigns": 10, "monitors": 50, "concurrent_collections": 5 },
}
# -1 = unlimited
# Current action always completes; next action blocked with 403
```

### 8.2 Trial Lifecycle

```
Day 0:  Trial starts, onboarding begins
Day 1-6: Full access with trial limits
Day 5:  Automated email with usage stats + "2 days left"
Day 7:  Trial expires → dashboard read-only, upgrade banner
Day 37: Data purged if not converted
```

### 8.3 Stripe Webhooks

```
checkout.session.completed → activate subscription
invoice.paid → extend period, reset monthly usage
invoice.payment_failed → set past_due, warning email
customer.subscription.deleted → set cancelled, 30-day retention
```

---

## 9. Error Handling & Security

### 9.1 Error Codes

```
AUTH_REQUIRED, AUTH_INVALID, PLAN_LIMIT_REACHED, RATE_LIMITED,
RESOURCE_NOT_FOUND, VALIDATION_ERROR, COLLECTION_IN_PROGRESS,
INFERENCE_FAILED, APIFY_ERROR, STRIPE_ERROR, INTERNAL_ERROR
```

### 9.2 Retry Policy

- Apify: retry 2x, exponential backoff (5s, 15s)
- OpenRouter: retry 1x, then fallback model
- Stripe webhooks: Stripe handles retry (up to 3 days)
- Monitoring checks: retry on next scheduled cycle

### 9.3 Rate Limits

```python
RATE_LIMITS = {
    "default": "60/minute",
    "/campaigns/*/collect": "3/hour",
    "/campaigns/*/drafts/generate": "10/minute",
    "/monitor/register": "10/hour",
    "/auth/login": "5/minute",
    "/auth/signup": "3/hour",
}
```

### 9.4 Security

- JWT validation on every request via Supabase
- RLS on all tenant-scoped tables
- Service role key only in backend workers
- Pydantic validation on all inputs
- CORS strict origin whitelist
- Stripe webhook signature verification

### 9.5 Shadowban Detection

```python
# Dual-check strategy:
# Check 1: Authenticated request (author's view)
# Check 2: Anonymous request (public view)
# If auth=200 but public=not_found for 2 consecutive checks → Shadowbanned
# New accounts: check interval reduced from 4h to 1h for first 3 posts
```

---

## 10. Deployment Checklist

### 10.1 Environment Variables

```bash
# SUPABASE
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_JWT_SECRET=

# OPENROUTER
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# APIFY
APIFY_API_TOKEN=apify_api_...
APIFY_REDDIT_ACTOR_ID=

# STRIPE
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_STARTER_PRICE_ID=price_...
STRIPE_GROWTH_PRICE_ID=price_...

# CELERY / REDIS
REDIS_URL=redis://default:pass@host:6379/0
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# EMAIL
RESEND_API_KEY=re_...
EMAIL_FROM=noreply@bcrao.app

# APP
APP_ENV=production
APP_URL=https://app.bcrao.app
API_URL=https://api.bcrao.app
CORS_ORIGINS=https://app.bcrao.app
LOG_LEVEL=INFO

# FRONTEND (Next.js)
NEXT_PUBLIC_SUPABASE_URL=${SUPABASE_URL}
NEXT_PUBLIC_SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
NEXT_PUBLIC_API_URL=${API_URL}
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

### 10.2 Infrastructure

```
1. Supabase: enable pgvector, run migrations, configure RLS + auth templates
2. Vercel: deploy Next.js, set env vars, domain app.bcrao.app
3. Railway/Render: deploy FastAPI + Celery worker + Celery Beat + Redis
4. Stripe: create products ($49/$99), configure webhook, enable Portal
5. Apify: select Reddit actor, configure proxies, set usage alerts at 80%
6. DNS: app.bcrao.app → Vercel, api.bcrao.app → Railway/Render
```

### 10.3 Pre-Launch Checklist

```
□ Auth flow: signup → login → JWT → protected endpoint
□ Trial lifecycle: creation → day 5 email → expiry → upgrade
□ Module 1: Apify → Regex filter → AI processing → storage
□ Module 2: Scoring engine → community profile
□ Module 3: Draft generation + blacklist + ISC gating
□ Module 4: Registration → monitoring → shadowban detection → alerts
□ Stripe: Checkout → webhook → subscription → usage reset
□ Rate limits enforced on all endpoints
□ RLS: tenant isolation verified with 2 accounts
□ Email alerts: all 3 templates send correctly
```

---

## 11. Out of Scope (MVP)

| Feature | Reason |
|---------|--------|
| Auto-posting to Reddit | ToS violation, trust anti-pattern |
| Hacker News support | Different API/dynamics — V2 |
| Multi-language NLP | English-first; other SpaCy models later |
| Team/multi-user accounts | Single-founder focus |
| Real-time WebSocket dashboard | Polling every 30s is sufficient |
| Custom model fine-tuning | OpenRouter model selection covers needs |
| Mobile app | Responsive web sufficient |
| Public API / webhooks | Not needed until platform play |
| A/B testing of drafts | After baseline established |
| Semantic search UI on raw_posts | pgvector column exists, UI deferred |
| White-label / agency tier | Growth handles small agencies; V2 |

---

## 12. Backend Project Structure

```
bc-rao-api/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   ├── api/v1/
│   │   ├── router.py
│   │   ├── auth.py
│   │   ├── campaigns.py
│   │   ├── collector.py
│   │   ├── analyzer.py
│   │   ├── generator.py
│   │   ├── monitor.py
│   │   ├── billing.py
│   │   └── onboarding.py
│   ├── api/webhooks/
│   │   └── stripe.py
│   ├── models/
│   │   ├── auth.py
│   │   ├── campaign.py
│   │   ├── post.py
│   │   ├── draft.py
│   │   ├── monitor.py
│   │   ├── billing.py
│   │   └── common.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── campaign_service.py
│   │   ├── collector_service.py
│   │   ├── pattern_service.py
│   │   ├── generator_service.py
│   │   ├── monitor_service.py
│   │   ├── usage_service.py
│   │   ├── billing_service.py
│   │   └── email_service.py
│   ├── inference/
│   │   ├── client.py
│   │   ├── router.py
│   │   ├── prompts/
│   │   │   ├── classify.py
│   │   │   ├── generate_draft.py
│   │   │   ├── score_post.py
│   │   │   └── extract_patterns.py
│   │   └── cost_tracker.py
│   ├── nlp/
│   │   ├── rhythm_analyzer.py
│   │   ├── regex_filters.py
│   │   └── blacklist_checker.py
│   ├── workers/
│   │   ├── celery_app.py
│   │   ├── collection_tasks.py
│   │   ├── analysis_tasks.py
│   │   ├── monitoring_tasks.py
│   │   └── email_tasks.py
│   ├── integrations/
│   │   ├── apify_client.py
│   │   ├── stripe_client.py
│   │   ├── supabase_client.py
│   │   └── resend_client.py
│   └── utils/
│       ├── logging.py
│       ├── errors.py
│       └── security.py
├── migrations/
│   └── 001_initial_schema.sql
├── tests/
├── celerybeat-schedule.py
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 13. Celery Task Schedule

```python
beat_schedule = {
    "monitor-active-posts": {
        "task": "app.workers.monitoring_tasks.check_active_posts",
        "schedule": crontab(minute=0, hour="*/4"),
    },
    "monitor-new-account-posts": {
        "task": "app.workers.monitoring_tasks.check_new_account_posts",
        "schedule": crontab(minute=0, hour="*"),
    },
    "audit-due-posts": {
        "task": "app.workers.monitoring_tasks.run_post_audits",
        "schedule": crontab(minute=30, hour="*/6"),
    },
    "trial-expiry-check": {
        "task": "app.workers.email_tasks.send_trial_reminders",
        "schedule": crontab(minute=0, hour=9),
    },
    "monthly-usage-reset": {
        "task": "app.workers.collection_tasks.reset_monthly_usage",
        "schedule": crontab(minute=0, hour=0, day_of_month=1),
    },
}
```

---

## 14. Module 3 — Generation Decision Tree

```
IF account_status == "New":
    → WARM-UP MODE: Comments only, no links, no pitch
    → Archetype forced to "Feedback"
    → Max vulnerability: 0.9

ELIF isc_score > 7.5:
    → HIGH SENSITIVITY MODE
    → Block "ProblemSolution" archetype
    → Force "Feedback" with max vulnerability
    → Zero links allowed

ELIF archetype == "ProblemSolution":
    → 90% pain / 10% solution
    → In Media Res opening (no greetings)
    → Product mention only in last 10% of text

ELIF archetype == "Journey":
    → Technical diary style
    → Specific milestones with numbers
    → Metrics required

ELIF archetype == "Feedback":
    → Invert authority
    → Ask community to find flaws
    → Controlled imperfection in tone
```

### Generation Pipeline

```
1. Load community profile (DB, no LLM)
2. Load syntax blacklist (DB, no LLM)
3. Build dynamic system prompt (archetype + ISC + rhythm + blacklist + account status)
4. LLM call via OpenRouter
5. Post-processing: regex blacklist check, link density, sentence length validation, jargon scan
6. Return draft with quality scores
```

---

*Version: 1.0.0 | Last updated: 2026-02-06*
