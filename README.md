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
| **Invest** | 1.8.1 | Finance | Financial market data analysis with MarketData skill and analyst personas |
| **Study** | 1.1.2 | Education | Study and knowledge management with PDF, presentation, NotebookLM |
| **Obsidian** | 1.1.0 | Productivity | Obsidian vault authoring with Markdown, Canvas, and Bases file format skills |
| **Youtube** | 1.1.0 | Research | YouTube video search and transcript summarization with Gemini AI. Includes MCP server for Claude Desktop. |
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

### Youtube

YouTube video search and transcript summarization plugin. Includes MCP server for Claude Desktop.

| Component | Type | Description |
|-----------|------|-------------|
| Youtube | Skill | Video search with AI-powered transcript summarization via Gemini |
| youtube_search | MCP Tool | Search YouTube with metadata + Gemini summary (Claude Desktop) |
| youtube_transcript | MCP Tool | Full transcript retrieval for deep analysis (Claude Desktop) |

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
│   │   └── skills/MarketData/ # SKILL.md, Personas/, scripts/, tools/
│   ├── Study/
│   │   ├── .claude-plugin/plugin.json
│   │   ├── agents/            # Architector-Knowledge, Architector-Mermaid, Planner-PPT
│   │   ├── commands/          # Book, Knowledge, Mermaid, PPT, Restructure
│   │   └── skills/            # Describe_Images, Nano-Banana, NoteBookLM, Prepare_Book, Restructure, pdf
│   ├── Obsidian/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/            # Markdown, Canvas, Bases
│   ├── Youtube/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/Youtube/    # SKILL.md, scripts/
│   ├── Moai/
│   │   ├── .claude-plugin/plugin.json
│   │   └── agents/            # builder-agent, builder-plugin, builder-skill
│   └── Template/
│       └── .claude-plugin/plugin.json
├── mcps/
│   └── Youtube/
│       ├── server.py              # FastMCP server (youtube_search, youtube_transcript)
│       ├── _api_youtube.py        # YouTube Data API wrapper
│       ├── _api_transcript.py     # Transcript extraction wrapper
│       ├── _api_gemini.py         # Gemini summarization wrapper
│       ├── _utils.py              # Utilities
│       ├── prompt_summary.md      # Gemini prompt template
│       ├── requirements.txt       # Python dependencies
│       └── .venv/                 # Virtual environment
└── README.md
```

## License

Private repository. For personal use only.
