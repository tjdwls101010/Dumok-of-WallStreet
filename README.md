# Seongjin's Claude Marketplace

A Claude Code plugin marketplace providing custom plugins for financial analysis and investment research.

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

**Setup:**

The environment is automatically configured on first use. All API keys are included — no additional configuration needed.

## Structure

```
Seongjin's Claude/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace definition
├── plugins/
│   └── Invest/
│       ├── .claude-plugin/
│       │   └── plugin.json       # Plugin metadata
│       ├── commands/
│       │   ├── Minervini.md      # SEPA analysis command
│       │   └── Serenity.md       # Supply chain analysis command
│       └── skills/
│           └── MarketData/
│               ├── SKILL.md      # Skill catalog
│               ├── Personas/     # Analyst persona files
│               ├── scripts/      # Python data collection scripts
│               └── tools/        # Utilities (docstring extractor, etc.)
└── README.md
```

## License

Private repository. For personal use only.
