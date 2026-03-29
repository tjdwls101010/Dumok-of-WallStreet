# Invest Plugin

A plugin designed to 100% replicate the methodologies and personas of renowned investment experts, analyzing the market from their unique perspectives.

As of March 29, 2026, it currently supports 2 experts as independent skills: **Serenity** (Supply Chain Bottleneck 6-Level) and **Minervini** (SEPA). Each expert is a self-contained skill with its own pipeline, modules, and reference documents.

---

## 1. Design Philosophy

This plugin aims to perfectly recreate the **mindset and decision-making framework** of each investment expert, not just analyze stocks. To achieve this, the plugin enforces 8 core design principles (see Section 2) governing how the agent discovers code, executes analysis, and manages context. Every architectural decision — from the 2-step module discovery to pipeline-centric execution — derives from these principles.

---

## 2. Core Design Principles

Describe the meaning, purpose, and reason for introducing each principle.

### 2.1 Single Source of Truth (Eliminating Document Synchronization Burden)

**Principle**: The docstring is the single source of truth for the specific usage of the code. Do not specify **interface details** (subcommand names, argument formats, return structures) or **output field names** (JSON key names such as `sbc_flag`, `debt_quality_grade`, `composite_signal`) in commands or personas — these change when code evolves. The agent always accesses the latest interface information via `extract_docstring.py`, and field-level semantics via the JSON output's self-documenting fields (see §2.8). Structural references (which pipeline file serves which persona, execution path format patterns) and methodology concepts (e.g., "stock-based compensation health", "debt quality") are acceptable since they are stable architectural facts.

**Reason for Introduction**: When modifying code, updating the docstring in the same file is natural, but synchronizing interface details with separate files (commands/personas) was burdensome and prone to omissions. `extract_docstring.py` bridges this gap for interface discovery. Similarly, when calculation thresholds change in code, the JSON output's `thresholds` fields reflect the change automatically, while references to specific field names or threshold values in separate documents become stale.

**Anti-pattern**: Copying the same numeric value into multiple sections of the output (e.g., duplicating a score in both the data section and a summary section). Each data point must have exactly one canonical location; downstream consumers reference that location directly.

### 2.2 Persona Purity

**Principle**: Each command prioritizes the use of its dedicated pipeline. Calling pipelines of other personas is prohibited. Modules can be shared, but the interpretation of results must always be within the context of the respective persona.

**Reason for Introduction**: Previously, when the agent autonomously selected modules, boundaries between personas collapsed (e.g., interpreting Minervini's SEPA/VCP from a Minervini perspective during a Serenity analysis). Pipelines solve this by enforcing module combinations, weights, and gates unique to each persona.

### 2.3 Pipeline-Complete

**Principle**: Each pipeline must contain ALL module calls required by the expert's methodology. The pipeline's subcommands serve as the complete implementation of the methodology — the agent should NEVER need to call individual modules to supplement pipeline results.

**Reason for Introduction**: The original "Pipeline-First" approach allowed agents to supplement pipeline results with individual module calls. However, this led to inconsistency — the same query produced different supplementary module selections across runs, undermining reproducibility. The evolved approach (demonstrated by Minervini and Williams pipelines) embeds all methodology-required module calls within the pipeline's subcommands, achieving 100% consistency. The agent's role is limited to interpreting pipeline outputs, not selecting which modules to call.

### 2.4 Context Efficiency

**Principle**: Pipelines load sufficient data internally but do not include massive raw data with low insight density (e.g., years of daily price history) in the response. However, sufficient evidence for each judgment must be included. The principle is not "less data," but "exclude unnecessary raw data, but include all scores, signals, and evidence for judgments."

**Reason for Introduction**: Claude's context window (200k) is a finite resource. When raw data occupied the context, the quality of the agent's analysis degraded. Pipelines solve this by processing raw data internally and returning only derived metrics and evidence for judgments, utilizing the context efficiently.

### 2.5 Progressive Disclosure

**Principle**: Hierarchically load only the necessary information at the exact moment it is needed. Pipeline subcommands (e.g., `macro`, `analyze`, `discover`) are stable interfaces documented directly in the skill's SKILL.md — the agent calls them directly without additional discovery. Reference documents (methodology, valuation, macro) are loaded selectively based on Query Classification, not all at once.

**Reason for Introduction**: Loading all reference documents for every query wastes context. Selective loading based on query type keeps the agent focused. Pipeline interfaces are stable and few (3-5 subcommands per expert), so documenting them directly in SKILL.md is sufficient.

### 2.6 Graceful Degradation

**Principle**: Continue analysis with the remaining components even if individual components of the pipeline fail. Indicate `missing_components`.

**Reason for Introduction**: Individual module failures are inevitable due to reliance on external data sources (yfinance, FRED, etc.). If a single failure halts the entire analysis, usability severely degrades.

### 2.7 Skill-Scoped Modules

**Principle**: Each skill owns its modules and pipeline. Modules within a skill may be tailored to that skill's methodology — there is no requirement for cross-skill neutrality. Shared modules (used by multiple skills) are duplicated into each skill for independence; divergence between copies is acceptable when it serves different analytical needs.

**Reason for Introduction**: The previous "Module Neutrality" principle required all modules to be persona-agnostic, creating overhead when a module's output needed persona-specific transformation in the pipeline. With self-contained skills, each expert's modules can be optimized for their specific methodology without concern for cross-persona compatibility.

### 2.8 Structural Clarity (Directory–Code Balance)

**Principle**: Minimize directory nesting while keeping each file to a single, clear responsibility. The trade-off between directory simplicity and code clarity is governed by two tests:

1. **5-Second Find Test**: Can someone locate the right file to modify within 5 seconds of scanning the directory?
2. **5-Second Purpose Test**: Can someone understand the file's purpose within 5 seconds of opening it?

When both tests pass, the structure is correct. If merging files would cause the second test to fail (file exceeds ~800 lines or mixes unrelated concerns), keep them separate. If splitting creates directory noise that fails the first test, consolidate.

**Guidelines**:
- Prefer role-based folders (`pipeline/`, `modules/`) over category folders (`technical/`, `analysis/`, `data_sources/`)
- Each file should have one reason to change — if a file changes for two unrelated reasons, it should be two files
- Target: ≤800 lines per file. At 500+ lines, consider whether responsibilities are mixed. Over 800 is a strong signal to split
- Single-module logic (uses output from exactly one module) belongs in that module, not in pipeline helpers
- Cross-cutting logic (synthesizes outputs from 2+ modules) belongs in the pipeline

**Reason for Introduction**: Over-decomposition into many small files with deep directory nesting increases cognitive load for navigation. Over-consolidation into large files with mixed concerns increases cognitive load for comprehension. The sweet spot minimizes total cognitive load: few directories with well-named files of moderate size.

### 2.9 Self-Documenting Output (2-Layer Trust Model)

**Principle**: Every computed score, signal, and flag in the JSON output must be self-documenting through **field naming** and **thresholds**. The agent must treat code-computed scores as a **consistent baseline, not absolute truth** — scores may be wrong due to hardcoded thresholds that don't fit every context. The agent critically evaluates scores by cross-checking against the `detail`/`evidence` fields provided alongside them.

Two layers provide information to the agent, each with a distinct role and zero synchronization risk:

| Layer | Role | Contains | Sync Risk |
|-------|------|----------|-----------|
| **JSON Output** | Field-level semantics | Self-documenting field names + `thresholds` (classification criteria) | Zero — same code function |
| **Persona Documents** | Methodology framework | WHY and HOW to think — investment reasoning, decision frameworks, judgment heuristics | Zero — no field names, stable concepts only |

**Field naming convention:**
- `thresholds`: Dict mapping each classification/stage to a natural-language rule with point values (e.g., `{"S1": "flat (|slope|<0.02) = 25pts", "S2": "rising (>0.02) = 15pts"}`). Do not use pipe-separated compressed strings — use structured dicts for agent readability.
- `unit`: Describes what the numeric value represents — its unit of measurement or calculation formula (e.g., `"%/day"`, `"up-day vol / down-day vol"`, `"% above 52-week low"`). Required for every numeric `value` field so the agent can interpret scale and meaning without external knowledge.
- `value`: The numeric measurement itself, always a number (not a string).
- Field names are self-documenting (e.g., `severity_score`, `margin_of_safety_pct`, `consecutive_beats`)

**Complete evidence field structure** (required for every score/evidence in module output):
```json
{
  "value": -0.013,
  "unit": "%/day",
  "thresholds": {
    "S1": "flat (|slope|<0.02) = 25pts",
    "S2": "rising (>0.02) = 15pts"
  }
}
```

`interpretation` and `note` fields are **not** included in JSON output. The agent interprets data by combining `value`, `unit`, and `thresholds`. Agent behavior directives belong in command/persona files, not in pipeline output.

**Reason for Introduction**: Score/signal/flag calculation methodologies were previously described in both code and persona documents. This created two risks: (1) When code thresholds changed, documents became stale, causing LLM misjudgment; (2) LLM couldn't distinguish "should I calculate this myself?" from "is this already calculated?" The self-documenting output pattern eliminates both risks — thresholds travel with the data, always in sync, and the LLM knows every score is pre-computed while having the evidence to question it.

**Anti-pattern**: Copying the same numeric value into multiple sections of the output (e.g., `io_quality_score` appearing in both L4 data and control layer). Each data point must exist in exactly one canonical location.

---

## 3. Architectural Hierarchy

```
SKILL.md — Agent Persona + Execution Protocol + Function Catalog
  ↓ references
Reference Files — Detailed Methodology Documents (Selectively Loaded)
  ↓ executes
Pipeline Scripts — Facade Orchestrators (Dedicated per Expert)
  ↓ calls
Module Scripts — Atomic Analysis Functions (Skill-Scoped)
```

**Load Timing and Conditions:**

| Hierarchy | Load Timing | Condition |
|-----------|-------------|-----------|
| SKILL.md | When the user invokes the skill (e.g., `/Serenity`) | Always |
| Reference Files | When in-depth methodology is needed | Selectively, based on Query Classification |
| Pipeline Scripts | When executing analysis | Always (Pipeline-Complete Principle) |
| Module Scripts | Orchestrated by the pipeline | Exclusively called within pipelines; pipelines must contain all methodology-required module calls |

---

## 4. Component Guide

Refer to existing implementations as structural templates. Serenity is the most complete reference (SKILL.md, 3 reference files, pipeline with 9 modules + 25 analysis modules).

### 4.1 SKILL.md

**Location**: `skills/{ExpertName}/SKILL.md`
**Role**: The single entry point for each expert. Defines the agent's identity, analysis protocol, query classification, pipeline interface, function catalog, and execution environment. When the user invokes `/ExpertName`, SKILL.md is loaded automatically.

**Key constraints:**
- **Pipeline Interface**: Pipeline subcommand names and usage are documented directly in SKILL.md (stable, few subcommands).
- **Output Field Name References**: SKILL.md may reference specific JSON output field names in orchestration rules (e.g., Investigation Triggers, Evidence Sufficiency Criteria). Do not include score calculation methodology — the JSON output's self-documenting fields handle this (§2.9).
- **Path Clarity**: All file path references must use `{skill_dir}/` as the explicit base path. Reference files, pipeline scripts, and modules as `{skill_dir}/path/to/file` so the agent can resolve paths unambiguously.
- **Environment Bootstrap**: Include venv setup instructions and execution patterns (`$VENV`, `$SCRIPTS` variables).

### 4.2 Reference Files

**Location**: `skills/{ExpertName}/References/`
**Role**: Provides the expert's specific methodology, interpretation framework, and decision-making criteria. Defines "how to interpret," but is not dependent on specific code implementations. Refer to existing references (e.g., `skills/Serenity/References/`) for structural patterns.

**Core Principle**: Extract the expert's **transferable methodology** (knowledge, know-how, decision-making framework) and apply it to current and future analysis. It is not for archiving past analysis records.

**Proper Use of Past Cases**: Past cases are allowed for few-shot purposes, but only to demonstrate the **decision-making process**. Ensure specific stock conclusions do not cause anchoring bias in future analysis.

**Content Principles** (what persona files SHOULD contain):

- **Principle-Based, Not Rule-Based**: Express methodology through values and principles (WHY), not through enumerated rules with specific numeric thresholds. When a rule is stated, it must trace back to a governing principle so the agent can reason from the principle in novel situations. Rules without principles create brittle agents; principles without rigid rules create flexible agents.

- **Three-Layer Documentation Hierarchy**: (1) **WHY — Values/Principles**: Why does the expert make this judgment? What value drives it? Highest priority — enables edge-case handling. (2) **HOW — Interpretation Methodology**: How should the agent synthesize multiple pipeline outputs? Covers cross-field reasoning that code output alone cannot provide. (3) **WHEN — Score Caveats**: When might a pipeline-computed score be misleading? What contextual factors should the agent consider?

- **Cross-Field Synthesis Focus**: Documents exist to explain how to COMBINE multiple pipeline outputs to reach judgments neither field alone provides. Do not define individual field meanings — self-evident fields (e.g., RSI, forward P/E, market cap) are already understood by the LLM; non-obvious fields are self-documented in JSON output via `thresholds` fields (§2.9). The document's value is in SYNTHESIS methodology: which fields to cross-reference, what patterns to look for, and what conclusions to draw from combinations.

- **Code vs Document Boundary**: When clear, deterministic logic exists for computing a score or signal → implement in pipeline code. When logic is ambiguous, requires contextual judgment, or depends on information beyond what the pipeline collects → describe the judgment framework in documents. The boundary question: "Can a deterministic rule be written?" If yes → code. If no → document.

- **Critical Evaluation Guidance**: Focus on when pipeline-computed scores might be misleading and what contextual factors the agent should consider — not on how to recalculate scores.

- **Empirical Fidelity**: Do not fabricate precise thresholds, named tests, or formalized frameworks that have no basis in the expert's actual practice. If the expert uses qualitative judgment, express it qualitatively. Fabricated frameworks mislead worse than no framework — the agent treats fabricated precision as ground truth.

- **Anchoring Prevention**: Do not include specific ticker symbols, price levels, or dates in methodology documents — these create anchoring bias. Past cases as few-shot must focus exclusively on the reasoning process, never on specific conclusions.

**Structural Rules** (what persona files should NOT contain):

- **Methodology Only, Not Calculation Methods**: Describe WHY and HOW to think, not HOW scores are computed. Do not duplicate calculation methodology or threshold values — the JSON output's `thresholds` fields provide this (§2.9). Reference concepts (e.g., "debt quality") without referencing specific JSON field names (e.g., `debt_quality_grade`).
- Must map to the SKILL.md's Query Classification.
- Avoid specifying interface details — creates synchronization burden when code changes.
- Avoid over-generalization — preserve the unique perspective of the specific expert.

### 4.3 Pipeline Scripts

**Location**: `skills/{ExpertName}/Scripts/pipelines/{name}/`
**Role**: Facade pattern — executes multiple modules in parallel for persona-specific analysis. Refer to existing pipelines for structural patterns.

**[HARD] Pre-verification of Module Interfaces:**

When writing or modifying pipeline code, you must verify the actual interfaces of all modules to be called — subcommand names, argument formats, return structures, and execution method. Read the module's docstring to confirm. Writing calling code based on guesswork is **strictly prohibited**. If even one interface detail is incorrect, the module call will fail and fall into `missing_components`.

**Self-Documenting Composite Scores (§2.9)**: When the pipeline computes composite scores by aggregating multiple inputs, the output must include `thresholds` or equivalent fields that reveal component weights and grade boundaries.

### 4.4 Module Scripts

**Location**: `skills/{ExpertName}/Scripts/` (organized by category: `technical/`, `analysis/`, `data_sources/`, etc.)
**Role**: Atomic functions focusing on a single analysis concern. Refer to existing modules for structural patterns (`@safe_run` decorator, `utils.output_json()`, top-level docstring).

**Key constraints:**
- **Single Responsibility Principle (SRP)**: Maintain clear boundaries without functional overlap. When writing a new module, check for overlap with existing modules within the same skill.
- **Self-Documenting Output (§2.9)**: Computed scores must include `thresholds` fields.
- **Skill-Scoped (§2.7)**: Modules may be tailored to the skill's methodology. Cross-skill reuse is via duplication, not shared references.

---

## 5. Anti-patterns

The following anti-patterns are **not derivable from §2 principles or existing examples** — they represent non-obvious failure modes learned from experience.

- **Duplicating calculation methodology in reference documents** — If code computes a score with specific thresholds and the reference document also describes those thresholds, two risks emerge: (1) stale documents when code changes; (2) LLM confusion about whether to recalculate or use pre-computed values. Reference documents focus on when to QUESTION scores, not how they were calculated.

- **Referencing specific JSON field names in reference documents** (e.g., "check `sbc_flag`", "if `debt_quality_grade` is D") — Creates synchronization burden when field names change. Use methodology concepts instead (e.g., "evaluate stock-based compensation health"). Exception: SKILL.md may reference field names in orchestration rules.

- **Fabricating precise thresholds when the expert uses qualitative judgment** — Creates false precision. Writing "demand/supply ratio >= 2:1" when the expert evaluates "demand visibly outstripping supply" invents a number the expert never used. Express qualitative judgments qualitatively.

- **Including specific ticker/price/date examples as anchors** — Creates anchoring bias. The agent pattern-matches to examples rather than reasoning from principles. Past cases are acceptable only as few-shot demonstrations of the REASONING PROCESS.

- **Changing module output structure without checking the consuming pipeline** — The pipeline parsing that module's output will break. Check all call sites within the pipeline first. Prioritize adding new keys over deleting existing ones.

- **Using pipeline outputs by cutting with head/tail** — Leads to incorrect judgments from partial data. Pipeline outputs are already designed with context efficiency in mind.

---

## 6. Guide to Adding a New Expert

Follow the existing implementation pattern. Reference: Serenity (most complete — SKILL.md, 3 reference files, pipeline with 9 helper modules + 25 analysis modules).

**Steps**: (1) Extract transferable methodology from source material → (2) Write reference files → (3) Copy needed modules from existing skills or create new ones → (4) Write pipeline → (5) Write SKILL.md (persona + protocol + catalog) → (6) Plugin checklist (plugin.json, marketplace.json, README.md).

**Skill directory structure:**
```
skills/{ExpertName}/
├── SKILL.md              (identity + protocol + catalog + environment)
├── References/           (methodology documents)
└── Scripts/
    ├── requirements.txt
    ├── utils.py
    ├── pipelines/
    │   └── {name}/       (pipeline code)
    ├── technical/        (analysis modules)
    ├── analysis/
    └── ...
```

**Key constraints:**
- **[HARD]** Verify ALL module interfaces before writing pipeline code
- New modules use `@safe_run` decorator and top-level docstring
- Each skill is self-contained — no cross-skill imports or shared module references

---

## 7. Modification Guide

- **Modifying pipelines**: Update the SKILL.md's pipeline documentation whenever subcommands change. Verify module interfaces before calling new modules.
- **Changing module output structure (most dangerous change)**: Identify ALL call sites within the pipeline and update their parsing logic. Prioritize adding new keys over deleting existing ones.
- **Modifying SKILL.md/reference files**: Verify mapping with Query Classification and reference files when changing workflows.
