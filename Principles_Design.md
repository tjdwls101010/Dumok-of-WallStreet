# Invest Plugin

A plugin designed to 100% replicate the methodologies and personas of renowned investment experts, analyzing the market from their unique perspectives.

As of February 28, 2026, it currently supports 5 experts: **Minervini** (SEPA), **Serenity** (Supply Chain Bottleneck 6-Level), **TraderLion** (S.N.I.P.E.), **SidneyKim0** (Macro-Statistical), and **Williams** (Volatility Breakout).

---

## 1. Design Philosophy

This plugin aims to perfectly recreate the **mindset and decision-making framework** of each investment expert, not just analyze stocks. To achieve this, the plugin enforces 7 core design principles (see Section 2) governing how the agent discovers code, executes analysis, and manages context. Every architectural decision — from the 2-step module discovery to pipeline-centric execution — derives from these principles.

---

## 2. Core Design Principles

Describe the meaning, purpose, and reason for introducing each principle.

### 2.1 Single Source of Truth (Eliminating Document Synchronization Burden)

**Principle**: The docstring is the single source of truth for the specific usage of the code. Do not specify **interface details** (subcommand names, argument formats, return structures) in commands or personas — these change when code evolves. The agent always accesses the latest interface information via `extract_docstring.py`. Structural references (which pipeline file serves which persona, execution path format patterns) are acceptable since they are stable architectural facts.

**Reason for Introduction**: When modifying code, updating the docstring in the same file is natural, but synchronizing interface details with separate files (commands/personas) was burdensome and prone to omissions. `extract_docstring.py` bridges this gap, ensuring the agent always has access to the latest code information.

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

**Principle**: Hierarchically load only the necessary information at the exact moment it is needed. The agent first checks module names and one-line descriptions in `SKILL.md` (Level 1 Catalog), then uses `extract_docstring.py` (Level 2 Details) to check subcommands, arguments, and return structures only for the modules it actually needs. This two-step discovery process saves context while ensuring access to accurate information. Do not guess subcommands.

**Reason for Introduction**: Loading the entire docstrings of ~112 modules at once wastes context. The 2-step discovery process retrieves detailed information only for the necessary modules at the necessary time.

### 2.6 Graceful Degradation

**Principle**: Continue analysis with the remaining components even if individual components of the pipeline fail. Indicate `missing_components`.

**Reason for Introduction**: Individual module failures are inevitable due to reliance on external data sources (yfinance, FRED, etc.). If a single failure halts the entire analysis, usability severely degrades.

### 2.7 Module Neutrality

**Principle**: Individual modules are not dependent on a specific persona. The identity of a persona is determined by the combination, weights, and gate design of the pipeline, and the interpretation context of the command and persona documents.

**Reason for Introduction**: If the interpretation logic of a specific persona is hardcoded into a module, it cannot be reused in other pipelines, and the number of modules increases unnecessarily. Interpretation is handled by higher layers (commands/pipelines), keeping modules as neutral tools.

---

## 3. Architectural Hierarchy

```
Command (.md) — Agent Persona + Execution Protocol
  ↓ loads
SKILL.md — Function Catalog (Level 1 Discovery)
  ↓ references
Persona Files — Detailed Methodology Documents (Selectively Loaded)
  ↓ executes
Pipeline Scripts — Facade Orchestrators (Dedicated per Persona)
  ↓ calls
Module Scripts — Atomic Analysis Functions (~112)
```

**Load Timing and Conditions:**

| Hierarchy | Load Timing | Condition |
|-----------|-------------|-----------|
| Command | When the user invokes the command | Always |
| SKILL.md | Before the Command executes analysis | Always |
| Persona Files | When in-depth methodology is needed | Selectively, based on Query Classification |
| Pipeline Scripts | When executing analysis | Always (Pipeline-Complete Principle) |
| Module Scripts | Orchestrated by the pipeline | Exclusively called within pipelines; pipelines must contain all methodology-required module calls |

---

## 4. Component Guide

### 4.1 Command (.md)

**Location**: `commands/`
**Role**: Defines the agent's identity, analysis protocol, and query classification system. It defines "what to analyze and how to interpret it," but does not define "which code to call and how."

**Required Sections:**

| Section | Role |
|---------|------|
| YAML frontmatter | name, description, skills, tools, model, color |
| Identity | The expert's core philosophy and positioning |
| Voice | Natural language catchphrases (including Korean translations) |
| Core Principles | Foundational principles of the methodology (6-9 items) |
| Prohibitions | Actions to absolutely avoid (Guardrails) |
| Methodology Quick Reference | Inline summary of core formulas and criteria |
| Query Classification | Workflows by user intent (Type A-G) |
| Analysis Protocol | Mandating Pipeline-Complete usage |
| Reference Files | List of persona files |
| Error Handling | Response to data source failures |
| Response Format | Definition of output structure |

**Notes:**
- **Include Inline Methodology Summary**: Directly include core criteria (e.g., Minervini's 8 Trend Template conditions) in the Methodology Quick Reference. Used as a fallback if persona files fail to load.
- **Query Classification**: Define analysis workflows for each type (Type A ~ G) to determine the appropriate analysis path based on the user's question intent.
- **Do Not Specify Interface Details**: Following the Single Source of Truth principle, do not include subcommand names, argument formats, or return structures. Discover them at runtime via `extract_docstring.py`. Structural references (pipeline file paths, execution format) are acceptable.

### 4.2 SKILL.md

**Location**: `skills/MarketData/SKILL.md`
**Role**: The Level 1 catalog for all scripts. The entry point for Progressive Disclosure.

**Required Structure:**

| Section | Role |
|---------|------|
| Environment Bootstrap | venv setup protocol |
| Progressive Disclosure Architecture | Explanation of the 2-step discovery |
| Function Catalog | Module tables by category (Pipelines, Core Analysis, Data & Screening, Advanced Data Sources) |
| Script Execution Safety Protocol | Mandatory Batch Discovery Rule, Safety Guardrails |
| How to Use | 3-step workflow + Environment variables |
| Error Handling & Fallback Guide | 3-step fallback chain |

**Notes:**
- Always register new modules/pipelines in the catalog.
- Do not list subcommand names — discover them via Level 2 (`extract_docstring.py`).
- Do not modify the Safety Protocol rules.

### 4.3 Persona Files

**Location**: `skills/MarketData/Personas/{Name}/`
**Role**: Provides the expert's specific methodology, interpretation framework, and decision-making criteria. Like the Command, it defines "how to interpret," but is not dependent on specific code implementations.

**Core Principle**: The goal is to extract the expert's **methodology (knowledge, know-how, decision-making framework)** and apply it to current and future analysis. It is not for archiving and searching the expert's past analysis records. You must extract **transferable methodologies** from their books and reports.

**Proper Use of Past Cases**: Including past cases to show "what judgments were made on which stocks and what decisions were reached" is allowed for few-shot purposes. However, use them only in the context of demonstrating the **decision-making process** of the methodology, and ensure that the specific stock conclusions themselves do not cause anchoring bias in future analysis.

**Required Structure**: Separate into one file per methodology. Example (Minervini):

| File | Content |
|------|---------|
| `sepa_methodology.md` | 5 Elements of SEPA, 4-Stage Ranking, Probability Convergence |
| `sector_leadership.md` | Bottom-up approach, 52W Highs, Leader-based timing |
| `earnings_insights.md` | Cockroach effect, Earnings quality, Surprise history |
| `risk_and_trade_management.md` | Position sizing, Stop-loss, Expected value management |

**Notes:**
- Must map to the Command's Query Classification.
- Extract the methodology (HOW) from original books and reports. Use past cases only as few-shot examples, focusing on the decision-making process. Prevent anchoring bias from specific stock conclusions.
- Avoid over-generalization — preserve the unique perspective of the specific expert.
- Avoid specifying interface details (subcommand names, arguments, return structures) — creates synchronization burden when code changes. Structural pipeline references are acceptable.

### 4.4 Pipeline Scripts

**Location**: `scripts/pipelines/`
**Role**: Facade pattern — executes multiple modules in parallel to provide a comprehensive analysis tailored to the persona's methodology.

**Current Pipelines:**

| Pipeline | Persona | Number of Subcommands |
|----------|---------|-----------------------|
| `minervini.py` | Minervini (SEPA) | 6 |
| `traderlion.py` | TraderLion (S.N.I.P.E.) | 6 |
| `serenity.py` | Serenity (6-Level) | 6 |
| `sidneykim0.py` | SidneyKim0 (Macro-Statistical) | 6 |
| `williams.py` | Williams (Volatility Breakout) | 6 |

**Required Elements:**

- **Subcommands**: Naturally derived from the expert's methodology. No common minimum requirements are enforced; designed to fit each persona's analysis workflow.
- **Hard Gate / Soft Gate System**: Blocks signals (Hard) or deducts points (Soft) if specific conditions are not met.
- **Composite Scoring + Signal Generation**: Weighted summation → Signal (STRONG_BUY, BUY, HOLD, etc.).
- **ThreadPoolExecutor Parallel Execution**: Reduces response time by executing independent modules concurrently.
- **Graceful Degradation**: Continues analysis with the rest even if partial failures occur. Indicates `missing_components`.
- **Response Compression Post-processing**: Converts raw data into insights to ensure context efficiency.

**[HARD] Pre-verification of Module Interfaces (Pipeline Development Rule):**

When writing or modifying pipeline code, you must exhaustively verify the actual interfaces of all modules to be called using `extract_docstring.py` before writing the code. Items to check:

1. **Subcommand Names**: The subcommands actually provided by the module (e.g., `erp`, `get-current`, `yield-equity`, etc.).
2. **Argument Formats**: positional vs. named, default values, types (e.g., `["SPY"]` vs. `["--symbol", "SPY"]`).
3. **Return Structures**: Key names and nested structures of the output JSON (e.g., `{"current": {"erp": float}}` vs. `{"erp": float}`).
4. **Execution Method**: Standalone script (`python script.py`) vs. package module (`python -m package`).

Writing calling code based on guesswork without verifying the module's interface is **strictly prohibited**. If even one of the subcommand names, argument formats, or output key names is incorrect, the module call will fail and fall into `missing_components`. Therefore, pre-verification is an essential prerequisite for pipeline quality.

**Notes:**
- Every command must have a dedicated pipeline.
- Load sufficient data internally, but do not include massive raw data with low insight density (e.g., years of price history) in the response.
- Must include sufficient evidence for each judgment, not just scores and signals.
- Principle: Not "less data," but **"exclude unnecessary raw data + include evidence for judgments."**

### 4.5 Module Scripts

**Location**: `scripts/` (excluding pipelines)
**Role**: Atomic functions focusing on a single analysis concern. Approximately 112 modules.

**Required Structure:**
- Module docstring (compatible with `extract_docstring.py`, adhering to `docstring_guidelines.md` specifications)
- `@safe_run` decorator — converts all exceptions into JSON error formats
- JSON output — use `utils.output_json()`

**Notes:**
- **Single Responsibility Principle (SRP)**: Maintain clear boundaries without functional overlap between modules. Since pipelines combine and call multiple modules, each module must be clearly distinct for easy maintenance. When writing a new module, always check for functional overlap with existing modules.
- **Write Persona-Neutrally**: Do not hardcode the interpretation logic of a specific persona so that it can be reused across multiple pipelines.
- **Docstring Concentration Principle**: `extract_docstring.py` extracts only the module-level docstring at the very top of the file using `ast.get_docstring()`. All information the agent needs to know (subcommands, arguments, return structures, usage examples) must be concentrated within a single `""" """` block at the very top of the file. Function-specific docstrings or inline comments will not be discovered by `extract_docstring.py`.

### 4.6 Docstring & extract_docstring.py

**Location**: `tools/extract_docstring.py`
**Role**: Level 2 Discovery — safely discovers the subcommands, arguments, and return structures of modules.

This is the **core mechanism of the Single Source of Truth**. Instead of specifying code usage in command or persona files, it acts as a bridge allowing the agent to always get the latest information directly from the code itself.

**Reason for Existence**: When modifying code, updating the docstring at the top of the same file is natural, but synchronizing it with separate files (commands/personas) is a heavy burden. To resolve this, the agent extracts the latest information directly from the docstring.

**Notes:**
- Do not read Python files directly; always use `extract_docstring.py`.
- Maximum of 5 scripts per call.
- Adhere to the `docstring_guidelines.md` specifications.

---

## 5. Anti-patterns

Describe each anti-pattern along with the reason why it is a problem.

- **Analyzing by randomly combining modules without a pipeline** — Redundant loading of the same data wastes context, lacks consistency in analysis results, and forms an arbitrary analysis flow rather than the persona's methodology.

- **Calling pipelines of other personas** — Methodologies between personas become mixed, polluting purity. Example: Using Minervini's SEPA score directly in a Serenity analysis eliminates Serenity's unique interpretation context.

- **Including massive raw data with low insight density in the response** (years of price history, full lists of holders, etc.) — Occupies the 200k context window, degrading the agent's analysis quality. However, sufficient evidence for judgments must be included.

- **Reading Python files directly instead of using `extract_docstring.py`** — Hundreds to thousands of lines of code occupy the context. `extract_docstring.py` efficiently extracts only the docstring based on AST.

- **Executing by guessing subcommand names** — Causes errors due to incorrect subcommands. You must first verify the exact subcommand through Progressive Disclosure (Level 2).

- **Writing module calls in pipeline code without verifying interfaces** — If even one of the subcommand names (`current` vs. `erp` vs. `get-current`), argument formats (`["calculate", "SPY"]` vs. `["SPY"]`), output keys (`zscore` vs. `z_score`, `current_price` vs. `current_value`), or nested structures (`data.get("erp")` vs. `data.get("current", {}).get("erp")`) is incorrect, the module call will fail, falling into `missing_components` or returning null values. You must exhaustively verify the interfaces of all modules to be called using `extract_docstring.py` before writing pipeline code.

- **Hardcoding the interpretation logic of a specific persona into module scripts** — Prevents reuse in other pipelines and unnecessarily increases the number of modules. Interpretation is handled by higher layers (commands/pipelines).

- **Specifying concrete code names or subcommand names in command/persona files** — Creates a synchronization burden across multiple files when code changes. Violates the Single Source of Truth.

- **Scattering module usage instructions outside the top-level docstring** (function-specific docstrings, inline comments, etc.) — Cannot be discovered because `extract_docstring.py` extracts only the module-level docstring using `ast.get_docstring()`.

- **Using pipeline outputs by cutting them with head/tail** — Can lead to incorrect judgments due to partial data. Pipeline outputs are already designed with context efficiency in mind.

- **Changing the JSON output structure of a module without checking pipelines** — Can break the parsing logic of all pipelines that call the module. This is the change with the largest ripple effect.

---

## 6. Guide to Adding a New Expert

### Checklist

#### Step 1: Analyze Original Books and Reports

Extract the expert's **transferable methodology** (decision-making framework, unique perspective, knowledge, and know-how). Focus on methodologies applicable to the present and future, not past analysis cases or specific stock records.

#### Step 2: Write Persona Files

Separate files by methodology under `skills/MarketData/Personas/{Name}/`.

| File | Content |
|------|---------|
| `methodology.md` | Core framework, analysis workflow, decision-making criteria |
| `{domain_1}.md` | Methodology domain details (e.g., risk management, sector analysis) |
| `{domain_2}.md` | Methodology domain details |
| `{domain_3}.md` | Methodology domain details |

Refer to existing personas (e.g., `Personas/Minervini/`) as structural templates, but fill the content with the new expert's methodology.

#### Step 3: Module Gap Analysis and Creation

List the analysis functions required to implement the methodology organized in Step 2, and check if they can be covered by the existing ~112 modules.

- **If existing modules are sufficient**: Proceed directly to Step 4.
- **If new analysis functions are needed**: If it falls within the SRP scope of an existing module, add a subcommand. If it is a new concern, create a new module. Design it to be independent of any persona according to the module neutrality principle, allowing reuse in other pipelines in the future.
- When creating a new module: `@safe_run` decorator, JSON output (`utils.output_json()`), and a top-level module docstring (`docstring_guidelines.md` specifications) are mandatory. Also, register it in the `SKILL.md` catalog.

#### Step 4: Write Pipeline Script

`scripts/pipelines/{name}.py` — Design the module combinations, weights, and gates appropriate for the methodology.

**[HARD] Preliminary Step — Exhaustive Verification of Module Interfaces:**

Before writing code, verify the actual interfaces of all modules to be called in the pipeline using `extract_docstring.py`. Items to check: subcommand names, argument formats (positional/named), and return JSON structures (key names, nesting depth). Skipping this step will result in incorrect calls, causing most modules to fall into `missing_components`.

Required Elements:
- Subcommand design (derived from the expert's analysis workflow)
- Hard Gate / Soft Gate System
- Composite Scoring + Signal Generation
- ThreadPoolExecutor Parallel Execution
- Graceful Degradation
- Response Compression Post-processing
- Top-level module docstring (`docstring_guidelines.md` specifications)

#### Step 5: Write Command .md

`commands/{Name}.md` — Refer to existing command files as structural templates.

Required Sections: YAML frontmatter, Identity, Voice, Core Principles, Prohibitions, Methodology Quick Reference, Query Classification, Analysis Protocol, Reference Files, Error Handling, Response Format.

#### Step 6: Update SKILL.md

Register the new pipeline in the Pipelines section of the Function Catalog.

#### Step 7: Plugin Modification Checklist

Update `CHANGELOG.md`, `plugin.json`, `marketplace.json`, and the root `README.md`.

---

## 7. Modification Guide

Precautions when modifying existing components.

### Modifying Commands

When changing Query Classification, verify the mapping with Persona files. When adding a new Query Type, ensure that a Persona file or pipeline subcommand exists to handle that workflow.

### Modifying Pipelines

When adding or changing subcommands, updating the top-level docstring is mandatory. Since the information discovered by `extract_docstring.py` is the only interface documentation, if the docstring does not match the actual implementation, the agent will make incorrect calls.

When calling a new module or changing an existing call, you must verify the current interface (subcommand name, arguments, return structure) of the module using `extract_docstring.py` before modifying the code. Since the module's output structure might have changed, also validate the field names and nested paths in the existing parsing code.

### Changing the JSON Output Structure of a Module (Most Dangerous Change)

If the output key names or structure change, **all pipelines** calling that module are affected. Before making the change, you must identify the pipelines using the module and modify their parsing logic accordingly.

### Modifying Modules (General)

Since they can be used in multiple pipelines, maintain backward compatibility. Prioritize adding new keys over deleting existing output keys.

### Creating a New Module vs. Adding a Subcommand to an Existing Module

If a new analysis function falls within the Single Responsibility Principle (SRP) of an existing module, add it as a subcommand. If it is a new concern, create a new module. Prevent modules from proliferating indiscriminately or a single module from becoming bloated.

### Modifying SKILL.md

Synchronize the catalog when adding, removing, or renaming modules.
