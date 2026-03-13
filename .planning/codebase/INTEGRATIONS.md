# External Integrations

**Analysis Date:** 2026-03-13

## APIs & External Services

**Development Tools:**
- npm registry - Used by GSD update checker (`.claude/hooks/gsd-check-update.js`) to check for `get-shit-done-cc` updates
  - SDK/Client: Native Node.js `execSync`
  - Auth: None required for version checks

**Application Services:**
- None yet - Fresh project initialization

## Data Storage

**Databases:**
- Not configured

**File Storage:**
- Local filesystem only
- `.planning/codebase/` - Documentation storage
- `.claude/cache/` - GSD update check cache
- Temporary files: `/tmp/claude-ctx-{session_id}.json` - Context metrics bridge (written by `.claude/hooks/gsd-statusline.js`)

**Caching:**
- None configured for application
- GSD uses local cache at `~/.claude/cache/gsd-update-check.json` (or project-local equivalent)

## Authentication & Identity

**Auth Provider:**
- Not configured

**Implementation:**
- Not applicable - No application code yet

## Monitoring & Observability

**Error Tracking:**
- None configured

**Logs:**
- GSD hooks use console output only
- No structured logging framework detected

**Context Monitoring:**
- `.claude/hooks/gsd-context-monitor.js` - Tracks Claude Code context usage
  - WARNING threshold: ≤35% remaining
  - CRITICAL threshold: ≤25% remaining
  - Debounce: 5 tool uses between warnings

## CI/CD & Deployment

**Hosting:**
- Not configured

**CI Pipeline:**
- None configured
- No `.github/workflows/`, `.gitlab-ci.yml`, or similar detected

## Environment Configuration

**Required env vars:**
- None yet - No `.env` file present
- `.gitignore` configured to exclude: `.env`, `.envrc`, `.venv`, `env/`, `venv/`

**Secrets location:**
- Not configured
- `.gitignore` includes standard secret file patterns (`.pypirc`, `.cursorignore`, Abstra credentials)

**Optional env vars:**
- `CLAUDE_CONFIG_DIR` - Override for GSD config directory location (supports multi-account setups)

## Webhooks & Callbacks

**Incoming:**
- None configured

**Outgoing:**
- None configured

## Development Integrations

**Claude Code Hooks:**
- SessionStart: `.claude/hooks/gsd-check-update.js` - Background update check on session start
- PostToolUse: `.claude/hooks/gsd-context-monitor.js` - Context usage monitoring after each tool use
- StatusLine: `.claude/hooks/gsd-statusline.js` - Shows model, task, directory, context usage

**GSD Workflow System:**
- Location: `.claude/get-shit-done/` (v1.22.4)
- Components:
  - `bin/gsd-tools.cjs` - Core CLI tool
  - `bin/lib/` - Modular libraries (commands, config, core, frontmatter, init, milestone, phase, roadmap, state, template, verify)
  - `workflows/` - 36 workflow definitions
  - `templates/` - Project templates and codebase analysis templates
  - `references/` - Documentation (checkpoints, git integration, TDD, verification patterns, etc.)

---

*Integration audit: 2026-03-13*
*Note: This is a fresh project with only GSD workflow infrastructure. Application integrations will be determined once development begins.*
