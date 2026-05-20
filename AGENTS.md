# AGENTS.md — Data Architect Agent Workspace

## Purpose
This workspace is dedicated to data architecture research, documentation, diagramming, and artifact management. All deliverables are versioned in GitHub. Communication with Daniel happens via Telegram DM through the bound bot account.

## Project Structure
```
artifacts/
├── diagrams/        # Mermaid source (.mmd) + rendered PNGs  
│   └── <project>/   
├── specs/           # Architecture docs, RFCs, ADRs (Markdown/PDF)  
│   └── <project>/   
└── research/        # Collected references, benchmarks, comparison notes
    └── <project>/   
memory/              # Daily engagement logs per YYYY-MM-DD.md
```

## Diagram Conventions
- **Mermaid** as default format (`.mmd` files)  
- Use `mmdc` CLI to render PNGs alongside source where available:
  ```bash
  npx mmdc -i diagram.mmd -o diagram.png --theme dark
  ```
- For complex C4 models, use layered approach: Context → Container → Component → Code level as needed

## Artifact Templates

### Architecture Decision Record (ADR)
```markdown
# ADR-NNN: <Title>  
**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXX  
**Date:** YYYY-MM-DD  

## Context  
(What problem are we solving?)

## Options Considered  
| Option  | Pros          | Cons           |
|---------|-               |-                |
| A       | ...           | ...            |
| B       | ...           | ...            |

## Decision  
<Chosen approach + rationale>

## Consequences  
(What follows from this decision?)
```

### System Architecture Doc Outline
1. Executive Summary / Problem Statement  
2. Current State (if applicable) — pain points, constraints  
3. Proposed Solution Overview (diagram first!)  
4. Component Breakdown  
5. Data Flow & Interfaces  
6. Non-functional Requirements (scale, perf, security, ops)  
7. Alternatives Considered + Trade-offs  

## GitHub Workflow
- Each engagement → feature branch `project/<name>` in the designated repo
- Commit artifacts incrementally as they're created/refined
- Tag milestones when Daniel approves final deliverables

## Tools & Skills Needed
- `web_search`, `web_fetch` — research  
- `exec` — Mermaid rendering, git CLI, file ops  
- GitHub skill (when enabled) — repo management via API  
