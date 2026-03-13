# Testing Patterns

**Analysis Date:** 2026-03-13

## Test Framework

**Runner:**
- Not detected - no test framework configuration found
- No package.json in project root
- No jest.config.*, vitest.config.*, or similar test configs

**Assertion Library:**
- None detected

**Run Commands:**
```bash
# No test scripts found
```

## Test File Organization

**Location:**
- No test files detected (no *.test.js, *.test.ts, *.spec.js files)

**Naming:**
- Not applicable - no tests present

**Structure:**
```
.claude/
  hooks/               # Hook scripts (no tests)
  agents/              # Agent definitions (no tests)
  commands/gsd/        # Command definitions (no tests)
  get-shit-done/
    workflows/         # Workflow documentation (no tests)
    templates/         # Templates (no tests)
    references/        # Reference documentation (no tests)
```

## Test Structure

**Suite Organization:**
Not applicable - no tests present

**Patterns:**
- No testing patterns established
- Hooks rely on operational testing (run in actual Claude Code sessions)
- Workflows tested through execution, not automated tests

## Mocking

**Framework:**
- None

**Patterns:**
- Not applicable

**What to Mock:**
- If tests added: file system (fs), child processes (spawn), stdin/stdout, timers (setTimeout)
- Environment-specific: process.env, os.homedir(), os.tmpdir()

**What NOT to Mock:**
- Path manipulation (path.join, path.basename)
- JSON parsing
- String operations

## Fixtures and Factories

**Test Data:**
- None present

**Location:**
- No fixtures directory

## Coverage

**Requirements:**
- No coverage requirements
- No coverage tooling configured

**Configuration:**
- None

**View Coverage:**
- Not applicable

## Test Types

**Unit Tests:**
- None present
- If added, would test: detectConfigDir function, JSON parsing, threshold calculations

**Integration Tests:**
- None present
- Hooks tested through actual Claude Code execution
- Manual verification of statusline display, context warnings, update checks

**E2E Tests:**
- Not applicable - GSD is tested in actual usage

## Common Patterns

**Current Testing Approach:**
- Manual testing through Claude Code sessions
- Hooks tested by running actual commands
- Workflows validated through real-world execution
- Documentation-driven development (workflows are both docs and specs)

**If Tests Added:**

Recommended patterns for future testing:

**Async Testing:**
```javascript
// Using Node.js native test runner or vitest
it('should handle async stdin', async () => {
  const result = await simulateStdin('{"session_id": "test"}');
  expect(result).toBe('expected output');
});
```

**Error Testing:**
```javascript
it('should exit silently on invalid JSON', () => {
  const exitCode = simulateInvalidInput();
  expect(exitCode).toBe(0);
});
```

**File System Mocking:**
```javascript
import { vi } from 'vitest';
import * as fs from 'fs';

vi.mock('fs');

it('should handle missing metrics file', () => {
  vi.mocked(fs.existsSync).mockReturnValue(false);
  // test graceful exit
});
```

**Timeout Testing:**
```javascript
it('should timeout after 3 seconds', async () => {
  vi.useFakeTimers();
  const timeoutHandler = setTimeout(() => process.exit(0), 3000);
  vi.advanceTimersByTime(3000);
  expect(process.exit).toHaveBeenCalledWith(0);
});
```

## Recommendations for Future Testing

**High Priority:**
- Unit tests for `detectConfigDir()` function in `gsd-check-update.js`
- Unit tests for threshold calculations in `gsd-context-monitor.js`
- Unit tests for context percentage calculations in `gsd-statusline.js`

**Medium Priority:**
- Integration tests for stdin/stdout behavior
- Mock file system tests for config directory detection
- Timeout behavior tests

**Low Priority:**
- E2E tests (hooks work in actual environment)
- Snapshot tests (output format stable)

**Recommended Stack:**
- Vitest (fast, modern, good Node.js support)
- Node.js native test runner (no dependencies)
- Mock stdin/stdout with test doubles
- Use `vi.useFakeTimers()` for timeout testing

---

*Testing analysis: 2026-03-13*
