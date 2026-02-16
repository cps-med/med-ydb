# VistA + YottaDB + Python Security Model (Starter)

## Why This Matters

Your current learning path uses direct global reads because it is fast and transparent for discovery. That is useful for learning, but it is not the same security model used by CPRS or other production clinical applications.

This document defines the starter security model you should use while learning with Python in VEHU.

---

## Security Boundaries

### 1. Roll-and-Scroll M Applications
- Access is mediated by VistA login/session context.
- Menu options, keys, and user context control what actions are allowed.
- Clinical workflows run through validated business logic.
- Auditing and operational controls are built into normal application usage.

### 2. RPC Broker Applications (CPRS-style)
- Access is mediated by authentication, authorization, and menu context.
- RPC definitions in File #8994 route calls to approved entry points.
- Business rules, validations, and workflow constraints are applied server-side.
- This is the preferred model for production patient-care applications.

### 3. Direct Global Access (Python + YottaDB API)
- Reads/writes occur directly against globals.
- You bypass much of FileMan/RPC validation logic by default.
- You can unintentionally expose PHI or create inconsistent data if not controlled.
- This is acceptable for bounded, read-only learning and diagnostics in safe environments.

---

## Core Risk Differences

| Topic | Roll-and-Scroll / RPC | Direct Global Access |
|---|---|---|
| Authentication context | Required | Not inherently required by API call |
| Authorization checks | Built-in | Must be enforced by script/process controls |
| Business-rule validation | Built-in | Often bypassed |
| Audit behavior | Established patterns | Must be intentionally designed |
| Safe writes | Possible through vetted APIs | Easy to do unsafely |

---

## Starter Rules for Python Learning Scripts

1. Read-only by default.
2. Allowlist globals explicitly.
3. Bound traversal (`--max-nodes`) to avoid runaway exploration.
4. Redact PHI by default for terminal output/logs.
5. Require explicit opt-in flag before displaying unredacted data.
6. Never perform production writes from exploratory scripts.
7. Prefer RPCs when moving from exploration to application workflows.

---

## Decision Guide: Which Access Pattern to Use

| Scenario | Recommended Pattern |
|---|---|
| Learn structure of `^DIC`, `^DD`, `^DPT`, `^VA` | Direct globals (read-only, bounded, allowlisted) |
| Build production patient UI/API | RPC Broker |
| Implement ordering/signing workflow | RPC/FileMan APIs (not direct writes) |
| Bulk reporting in controlled environment | Direct globals (read-only, controlled output) |

---

## Practical Controls You Should Implement

### Process Controls
- Run scripts under least-privilege accounts.
- Separate learning/test environments from production.
- Keep output destinations controlled (no casual PHI exports).

### Script Controls
- Implement explicit allowlists.
- Add command-line safety defaults (`redaction on`, bounded scans).
- Emit clear warnings when unsafe options are enabled.
- Keep all destructive operations out of starter scripts.

### Data Handling Controls
- Mask names/SSNs in logs and screenshots.
- Avoid checking PHI-containing output into Git.
- Treat copied terminal output as sensitive data.

---

## How This Fits Your Current Materials

- `app/03_explore_allowlisted.py` already demonstrates allowlist + bounded read-only exploration.
- `app/04_rpc_explorer.py` teaches the RPC layer used for production integration.
- New script: `app/05_security_explorer.py` demonstrates security-first direct global exploration with default redaction and explicit unsafe opt-in.

---

## Transition Path (Recommended)

1. Continue direct global reads for learning structure.
2. Add security controls to every exploration script.
3. Shift to RPC-centric workflows for app-like behavior.
4. Keep direct global writes out of starter learning scope.

---

## Key Takeaways

- Direct global access is powerful and educational, but it bypasses important guardrails.
- Production-safe behavior in VistA usually means RPC/FileMan-mediated operations.
- A good starter security model is: read-only + allowlist + bounded traversal + redaction by default.

