# BC-RAO Frontend Test Suite

Comprehensive test suite for the BC-RAO frontend using Vitest.

## Quick Start

### Install Dependencies

```bash
npm install -D vitest @vitejs/plugin-react @testing-library/react jsdom
```

### Run Tests

```bash
# Run all tests
npx vitest

# Run in watch mode
npx vitest --watch

# Run with coverage
npx vitest --coverage

# Run specific test file
npx vitest __tests__/lib/campaign-stages.test.ts
```

### Add to package.json

```json
{
  "scripts": {
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:coverage": "vitest --coverage"
  }
}
```

## Test Structure

```
__tests__/
├── setup.ts                      # Global test setup and mocks
├── lib/
│   ├── campaign-stages.test.ts   # Campaign stage progression logic (CRITICAL)
│   ├── sse.test.ts               # SSE URL construction
│   └── api.test.ts               # API client error handling
└── hooks/
    └── use-debounce.test.ts      # Debounce hook behavior
```

## What's Tested

### Campaign Stages (PRIORITY 1 - BUG-B01 Validation)
- ✓ All 5 stage URLs are correct
- ✓ Stage progression logic
- ✓ Stage locking/unlocking
- ✓ Stage completion criteria
- ✓ Linear progression flow

### SSE Utilities
- ✓ Production vs development URL routing
- ✓ Railway backend direct connection (avoids Vercel timeout)
- ✓ Next.js proxy in development

### API Client
- ✓ GET/POST/PATCH/DELETE methods
- ✓ Authorization header handling
- ✓ Error handling (network, HTTP, JSON parse)
- ✓ 401/403 authentication scenarios

### Hooks
- ✓ useDebounce timer behavior
- ✓ Rapid change handling
- ✓ Type safety across data types

## Mocked Dependencies

The test suite mocks these Next.js and browser APIs:

- `next/navigation` (useRouter, useParams, useSearchParams)
- `next/headers` (cookies)
- `EventSource` (for SSE testing)
- `fetch` (for API testing)

All mocks are configured in `setup.ts`.

## Test Philosophy

- **Focus on logic, not rendering** - We test business logic and utilities, not heavy component rendering
- **Minimal mocking** - Only mock external dependencies (Next.js, fetch, EventSource)
- **Real-world scenarios** - Tests validate actual usage patterns
- **Type safety** - Full TypeScript support

## Critical Tests

The **campaign-stages.test.ts** file is the most critical test suite because it validates the BUG-B01 fix:

- Stage 1 → `/dashboard/campaigns/{id}/edit`
- Stage 2 → `/dashboard/campaigns/{id}/collect`
- Stage 3 → `/dashboard/campaigns/{id}/analysis`
- Stage 4 → `/dashboard/campaigns/{id}/drafts/new`
- Stage 5 → `/dashboard/campaigns/{id}/monitoring`

If these tests fail, the stage navigation is broken.

## Coverage Goals

- **Target:** 80%+ coverage for critical paths
- **Focus areas:** lib/, hooks/
- **Excluded:** Heavy UI components, E2E scenarios

## Adding New Tests

1. Create test file: `__tests__/{category}/{filename}.test.ts`
2. Import from source: `import { fn } from '@/path/to/source'`
3. Use vitest's describe/it/expect pattern
4. Mock only what's necessary
5. Test edge cases and error scenarios

Example:

```typescript
import { describe, it, expect } from 'vitest'
import { myFunction } from '@/lib/myFunction'

describe('myFunction', () => {
  it('should do something', () => {
    const result = myFunction('input')
    expect(result).toBe('expected')
  })
})
```

## Troubleshooting

### Tests fail with "Cannot find module"
- Check path aliases in `vitest.config.ts`
- Ensure `@` resolves to project root

### EventSource not defined
- Check that `setup.ts` is being loaded
- Verify `setupFiles` in `vitest.config.ts`

### Fetch mock not working
- Use `vi.fn()` to create mock fetch
- Assign to `global.fetch` in test
- Clear mocks with `vi.clearAllMocks()` in beforeEach

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: npm ci
      - run: npm test
```

---

**Created by:** Equipe H - Frontend Test Writer
**Date:** 2026-02-12
