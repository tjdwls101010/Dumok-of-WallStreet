# Seongjin's Claude Marketplace

A Claude Code plugin marketplace providing custom plugins for financial analysis, study/knowledge management, and plugin development.

![](https://github.com/tjdwls101010/DUMOK/blob/main/Images/nano-banana-5c426c14-6bd7-48dc-8a44-95984888be72.png?raw=true)

## Installation

```bash
# Register the marketplace in Claude Code
claude plugin add <repo-url>
```

## Plugins

| Plugin | Category | Description |
|--------|----------|-------------|
| **Invest** | Finance | Financial market data analysis with analyst personas |
| **Study** | Education | Study and knowledge management with PDF, presentation, NotebookLM |
| **Moai** | Developer Tools | Builder toolkit for creating Claude Code agents, plugins, skills |
| **Template** | Developer Tools | Scaffolding template for new Claude Code plugins |

### Invest

Financial market data analysis plugin. Includes the MarketData skill and analyst personas.

| Component | Type | Description |
|-----------|------|-------------|
| MarketData | Skill | Multi-source financial data collection via YFinance, FRED, SEC EDGAR, Finviz, CFTC, CBOE |
| Minervini | Command | Technical analysis based on Mark Minervini's SEPA methodology |
| Serenity | Command | Supply chain architecture and fundamental analysis |

### Study

Study and knowledge management plugin.

| Component | Type | Description |
|-----------|------|-------------|
| Describe_Images | Skill | Image description and link conversion |
| Nano-Banana | Skill | Slide/template generation |
| NoteBookLM | Skill | Google NotebookLM integration |
| Prepare_Book | Skill | Book preparation workflow |
| Restructure | Skill | Content restructuring |
| pdf | Skill | PDF processing |
| Book | Command | Book study workflow |
| Knowledge | Command | Knowledge graph generation |
| Mermaid | Command | Mermaid diagram generation |
| PPT | Command | Presentation generation |
| Restructure | Command | Content restructuring |

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
│   │   ├── commands/          # Minervini, Serenity
│   │   └── skills/MarketData/ # SKILL.md, Personas/, scripts/, tools/
│   ├── Study/
│   │   ├── .claude-plugin/plugin.json
│   │   ├── agents/            # Architector-Knowledge, Architector-Mermaid, Planner-PPT
│   │   ├── commands/          # Book, Knowledge, Mermaid, PPT, Restructure
│   │   └── skills/            # Describe_Images, Nano-Banana, NoteBookLM, Prepare_Book, Restructure, pdf
│   ├── Moai/
│   │   ├── .claude-plugin/plugin.json
│   │   └── agents/            # builder-agent, builder-plugin, builder-skill
│   └── Template/
│       └── .claude-plugin/plugin.json
└── README.md
```

## License

Private repository. For personal use only.
