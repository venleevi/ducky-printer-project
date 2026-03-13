# Codebase Concerns

**Analysis Date:** 2026-03-13

## Tech Debt

**Empty Project State:**
- Issue: Repository contains only GSD framework infrastructure with no application code
- Files: Root directory lacks any source directories (no `src/`, `app/`, `lib/`)
- Impact: Cannot assess application-specific technical debt until project code is written
- Fix approach: This is expected state for new project initialization; no fix needed

**GSD Framework Overhead:**
- Issue: 1.5MB of GSD framework files in `.claude/` directory with 145 tracked files
- Files: `.claude/get-shit-done/`, `.claude/agents/`, `.claude/commands/`, `.claude/hooks/`
- Impact: Large commit surface for framework updates; potential merge conflicts during upgrades
- Fix approach: Consider adding `.claude/get-shit-done/` to `.gitignore` if treating as external dependency

**Deleted Speckit Framework:**
- Issue: Git status shows deleted Speckit framework files (`.claude/commands/speckit.*`, `.specify/`)
- Files: 9 deleted Speckit command files, 5 deleted Speckit bash scripts, 6 deleted Speckit templates
- Impact: Commit in progress leaves repository in transitional state between frameworks
- Fix approach: Complete transition by committing deletion and establishing GSD as canonical framework

## Known Bugs

**No Application Code:**
- Symptoms: No bugs detected - repository contains only framework infrastructure
- Files: N/A
- Trigger: No application logic exists yet
- Workaround: Begin application development to surface implementation issues

## Security Considerations

**Git Hook Sample Files:**
- Risk: Default Git hook samples present in `.git/hooks/` (16 files)
- Files: `.git/hooks/*.sample`
- Current mitigation: All hooks are `.sample` files (not executable, not active)
- Recommendations: Remove unused samples or document which hooks are intentionally kept as reference

**Environment File Template Missing:**
- Risk: No `.env.example` or `.env.template` file to guide required environment variables
- Files: None exist (`.env` correctly excluded in `.gitignore`)
- Current mitigation: `.gitignore` properly excludes `.env` and `.env*` files
- Recommendations: Create `.env.example` when application code requires environment configuration

**No Secrets Detection:**
- Risk: No pre-commit hooks or CI checks for leaked secrets
- Files: `.git/hooks/` contains only sample hooks
- Current mitigation: Fresh repository with no secrets committed yet
- Recommendations: Add pre-commit hook using `git-secrets` or similar tool before committing application code

**Context Monitor Hook File Operations:**
- Risk: Hook writes session metrics to `/tmp/claude-ctx-{session_id}.json` without cleanup
- Files: `.claude/hooks/gsd-context-monitor.js` (lines 39-50, 71-101), `.claude/hooks/gsd-statusline.js` (lines 39-49)
- Current mitigation: OS temp directory cleanup handles eventual removal
- Recommendations: Add session cleanup handler or TTL-based purging to prevent `/tmp` bloat

## Performance Bottlenecks

**No Application Performance Issues:**
- Problem: No application code exists to analyze for performance
- Files: N/A
- Cause: Fresh project initialization
- Improvement path: Profile after implementing core application features

**Hook Stdin Timeout Workaround:**
- Problem: Hooks include 3-second timeout guard for stdin blocking issues
- Files: `.claude/hooks/gsd-context-monitor.js` (lines 30-33), `.claude/hooks/gsd-statusline.js` (lines 11-13), `.claude/hooks/gsd-check-update.js` (lines not shown)
- Cause: Git Bash/Windows pipe issues causing hangs (referenced as issue #775)
- Improvement path: This is a known platform-specific workaround; acceptable as-is

## Fragile Areas

**GSD Update Check Background Process:**
- Files: `.claude/hooks/gsd-check-update.js`
- Why fragile: Spawns detached Node process with `npm view` command that can fail silently
- Safe modification: Timeout set to 10 seconds (line 64), errors caught and ignored
- Test coverage: No tests detected for hook functionality

**Context Monitor Debounce State:**
- Files: `.claude/hooks/gsd-context-monitor.js` (lines 70-102)
- Why fragile: Debounce state persisted to `/tmp` file can become corrupted or stale
- Safe modification: Corruption handling present (lines 79-82), but race conditions possible with concurrent sessions
- Test coverage: No automated tests

**Statusline Hook Todo File Discovery:**
- Files: `.claude/hooks/gsd-statusline.js` (lines 74-91)
- Why fragile: Reads from `~/.claude/todos/` directory with multiple fallback paths and filesystem operations that may fail
- Safe modification: All file operations wrapped in try-catch (lines 75-90, silent failures)
- Test coverage: No automated tests

## Scaling Limits

**GSD Framework Not Evaluated:**
- Current capacity: Unknown - no application code to scale
- Limit: Framework documentation does not specify scaling characteristics
- Scaling path: Assess after implementing multi-phase project with significant codebase

**Session-Based Temp Files:**
- Current capacity: One metrics file per Claude Code session in `/tmp`
- Limit: No cleanup mechanism for abandoned sessions; accumulates indefinitely
- Scaling path: Add periodic cleanup or session-end hook to remove temp files

## Dependencies at Risk

**No Package Manager:**
- Risk: Only `.claude/package.json` exists (contains `{"type":"commonjs"}`)
- Impact: Cannot assess dependency vulnerabilities without application dependencies
- Migration plan: Establish package manager (npm/yarn/pnpm) when adding application code

**Framework Update Mechanism:**
- Risk: GSD update check relies on npm registry availability at runtime
- Impact: Hook spawns `npm view get-shit-done-cc version` that fails on network issues
- Migration plan: Update check already handles failures gracefully (exits silently)

## Missing Critical Features

**No Testing Infrastructure:**
- Problem: No test framework, no test files, no test configuration
- Blocks: Cannot verify framework hook functionality or future application code
- Priority: High - establish testing before writing application code

**No CI/CD Pipeline:**
- Problem: No GitHub Actions, CircleCI, or other CI configuration
- Blocks: No automated verification of hook functionality or future application tests
- Priority: Medium - add after establishing test infrastructure

**No Linting/Formatting:**
- Problem: No ESLint, Prettier, or other code quality tools configured
- Blocks: No enforcement of code style for JavaScript hooks or future application code
- Priority: Medium - add before team expansion or significant application development

**No Error Tracking:**
- Problem: Hooks silently fail without reporting (multiple `process.exit(0)` on error)
- Blocks: Cannot diagnose hook failures in production use
- Priority: Low - hooks are non-critical; failures should not block Claude Code usage

## Test Coverage Gaps

**Hook Scripts Untested:**
- What's not tested: All three `.claude/hooks/*.js` files lack automated tests
- Files: `.claude/hooks/gsd-context-monitor.js`, `.claude/hooks/gsd-statusline.js`, `.claude/hooks/gsd-check-update.js`
- Risk: Context monitoring, status display, and update checks could break silently
- Priority: Medium - hooks are user-facing but non-critical

**Framework Command Integration:**
- What's not tested: GSD command execution paths (`.claude/commands/gsd/*.md`)
- Files: 27 command definition files in `.claude/commands/gsd/`
- Risk: Command parsing, state management, and workflow transitions may have edge cases
- Priority: Low - framework is external; trust upstream testing

**No Integration Tests:**
- What's not tested: Interaction between hooks and Claude Code session lifecycle
- Files: `.claude/settings.json` (hooks configuration), all hook scripts
- Risk: Hook timing issues, session ID mismatches, or file permission errors could break features
- Priority: Medium - impacts user experience but fails gracefully

---

*Concerns audit: 2026-03-13*
