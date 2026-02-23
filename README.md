# Seongjin's Claude Marketplace

A Claude Code plugin marketplace providing custom plugins for financial analysis, study/knowledge management, and plugin development.

![](https://github.com/tjdwls101010/DUMOK/blob/main/Images/nano-banana-5c426c14-6bd7-48dc-8a44-95984888be72.png?raw=true)

## Installation

```bash
# Register the marketplace in Claude Code
claude plugin add <repo-url>
```

## Plugins

| Plugin | Version | Category | Description |
|--------|---------|----------|-------------|
| **Invest** | 1.8.2 | Finance | Financial market data analysis with MarketData skill and analyst personas |
| **Study** | 1.1.2 | Education | Study and knowledge management with PDF, presentation, NotebookLM |
| **Obsidian** | 1.1.0 | Productivity | Obsidian vault authoring with Markdown, Canvas, and Bases file format skills |
| **Moai** | 1.0.0 | Developer Tools | Builder toolkit for creating Claude Code agents, plugins, skills |
| **Template** | 1.0.0 | Developer Tools | Scaffolding template for new Claude Code plugins |

### Invest

Financial market data analysis plugin. Includes the MarketData skill and analyst personas.

| Component | Type | Description |
|-----------|------|-------------|
| MarketData | Skill | Multi-source financial data collection via YFinance, FRED, SEC EDGAR, Finviz, CFTC, CBOE |
| Minervini | Command | Technical analysis based on Mark Minervini's SEPA methodology |
| Serenity | Command | Supply chain architecture and fundamental analysis |
| SidneyKim0 | Command | Macro-statistical analysis with regime identification and cross-asset divergence |
| TraderLion | Command | Momentum trading with S.N.I.P.E. workflow and volume-edge methodology |
| Williams | Command | Short-term volatility breakout trading analysis with chart pattern detection |

### Study

Study and knowledge management plugin.

| Component | Type | Description |
|-----------|------|-------------|
| Describe_Images | Skill | Image description and link conversion |
| Nano-Banana | Skill | Slide/template generation via Gemini Image Generation API |
| NoteBookLM | Skill | Google NotebookLM integration |
| Prepare_Book | Skill | Book preparation workflow |
| Restructure | Skill | Content restructuring |
| pdf | Skill | PDF processing |
| Book | Command | Book study workflow |
| Knowledge | Command | Knowledge graph generation |
| Mermaid | Command | Mermaid diagram generation |
| PPT | Command | Presentation generation |
| Restructure | Command | Content restructuring |

### Obsidian

Obsidian vault authoring plugin with file format skills for Markdown, Canvas, and Bases.

| Component | Type | Description |
|-----------|------|-------------|
| Markdown | Skill | Obsidian Flavored Markdown with wikilinks, embeds, callouts, properties |
| Canvas | Skill | JSON Canvas files with nodes, edges, groups, and connections |
| Bases | Skill | Obsidian Bases with views, filters, formulas, and summaries |

### Moai

MoAI builder toolkit for creating Claude Code agents, plugins, and skills with standards compliance.

| Component | Type | Description |
|-----------|------|-------------|
| builder-agent | Agent | Agent creation specialist |
| builder-plugin | Agent | Plugin creation specialist |
| builder-skill | Agent | Skill creation specialist |

### Template

Template plugin for scaffolding new Claude Code plugins.

## Structure

```
Seongjin's Claude/
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   ├── Invest/
│   │   ├── .claude-plugin/plugin.json
│   │   ├── commands/          # Minervini, Serenity, SidneyKim0, TraderLion, Williams
│   │   └── skills/MarketData/ # SKILL.md, Personas/, scripts/ (screening/, pipelines/), tools/
│   ├── Study/
│   │   ├── .claude-plugin/plugin.json
│   │   ├── agents/            # Architector-Knowledge, Architector-Mermaid, Planner-PPT
│   │   ├── commands/          # Book, Knowledge, Mermaid, PPT, Restructure
│   │   └── skills/            # Describe_Images, Nano-Banana, NoteBookLM, Prepare_Book, Restructure, pdf
│   ├── Obsidian/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/            # Markdown, Canvas, Bases
│   ├── Moai/
│   │   ├── .claude-plugin/plugin.json
│   │   └── agents/            # builder-agent, builder-plugin, builder-skill
│   └── Template/
│       └── .claude-plugin/plugin.json
└── README.md
```

## License

Private repository. For personal use only.
