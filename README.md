# Seongjin's Claude Marketplace

A Claude Code plugin marketplace providing custom plugins for financial analysis, study/knowledge management, and plugin development.

## Installation

```bash
# Register the marketplace in Claude Code
claude plugin add <repo-url>
```

## Plugins

### Invest

Financial market data analysis plugin. Includes the MarketData skill and analyst personas (Minervini, Serenity).

**Key Features:**
- **MarketData Skill**: Multi-source financial data collection via YFinance, FRED, SEC EDGAR, Finviz, CFTC, CBOE
- **Minervini Command**: Technical analysis based on Mark Minervini's SEPA methodology
- **Serenity Command**: Supply chain architecture and fundamental analysis

**Data Sources:**
| Source | Coverage |
|--------|----------|
| YFinance | Stock prices, financials, options, company info |
| FRED | Interest rates, inflation, monetary policy |
| SEC EDGAR | Filings, insider trading, 13F |
| Finviz | Screening, sector analysis |
| CFTC | Futures positioning |
| CBOE | IV, options chains, VIX futures |

### Study

Study and knowledge management plugin. PDF processing, image description, presentation generation, NotebookLM integration, and content restructuring.

**Skills:**
- **Describe_Images** — Image description and link conversion
- **Nano-Banana** — Slide/template generation
- **NoteBookLM** — Google NotebookLM integration
- **Prepare_Book** — Book preparation workflow
- **Restructure** — Content restructuring
- **pdf** — PDF processing

**Commands:** Book, Knowledge, Mermaid, PPT, Restructure

### Moai

MoAI builder toolkit for creating Claude Code agents, plugins, and skills with standards compliance.

**Agents:**
- **builder-agent** — Agent creation specialist
- **builder-plugin** — Plugin creation specialist
- **builder-skill** — Skill creation specialist

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
