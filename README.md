# 🧸📺 ToyToons

> A comprehensive learning project that combines web scraping, data processing, local summarization, and static site generation to explore 1980s and early 1990s animated shows and their toy lines.

[![Built with Python](https://img.shields.io/badge/Built%20with-Python-blue.svg)](https://www.python.org/)
[![Built with Astro](https://img.shields.io/badge/Built%20with-Astro-orange.svg)](https://astro.build/)
[![Deployed on Netlify](https://img.shields.io/badge/Deployed%20on-Netlify-00C7B7.svg)](https://netlify.com/)
[![Local First](https://img.shields.io/badge/Local%20First-No%20Cloud%20APIs-green.svg)](https://github.com/yourusername/toytoons)

**ToyToons** teaches you modern web development through a nostalgic lens. Learn scraping, data processing, summarization, and deployment by building a comprehensive database of classic cartoons and their iconic toy lines.

## 🚀 What You'll Learn

- **Web Scraping**: Respectful crawling with robots.txt compliance, retries, and rate limiting
- **Data Processing**: Extract structured data from HTML using BeautifulSoup and readability
- **Local Summarization**: Generate summaries using Ollama (qwen3:8b) or TextRank fallback
- **Static Site Generation**: Build fast, SEO-friendly sites with Astro and Tailwind CSS
- **API Design**: Create JSON/CSV exports for data consumption
- **Deployment**: Deploy to Netlify with optimized builds and caching
- **Project Management**: Use Makefiles for cross-platform development workflows

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))
- **Git** ([Download](https://git-scm.com/downloads)) - Recommended
- **Ollama** ([Download](https://ollama.ai/)) - Optional, for local AI summarization

### Optional: Ollama Setup

For the best summarization experience, install Ollama and pull the qwen3:8b model:

```bash
# Install Ollama (visit ollama.ai for platform-specific instructions)
# Then pull the model:
ollama pull qwen3:8b
```

If Ollama is not available, the system will automatically fall back to TextRank extractive summarization.

## 🛠️ Installation

### Option 1: Quick Setup with Makefile (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/toytoons.git
cd toytoons

# Check system dependencies
make check-deps

# Set up development environment (Python + Node.js)
make dev-setup

# Quick start with sample data
make quick-start
```

### Option 2: Manual Setup

<details>
<summary>Click to expand manual installation steps</summary>

#### Windows (PowerShell)

```powershell
# Clone and enter directory
git clone https://github.com/yourusername/toytoons.git
cd toytoons

# Create Python virtual environment
python -m venv venv
venv\Scripts\Activate.ps1

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install web dependencies
cd web
npm install
cd ..
```

#### macOS/Linux

```bash
# Clone and enter directory
git clone https://github.com/yourusername/toytoons.git
cd toytoons

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install web dependencies
cd web
npm install
cd ..
```

</details>

## 🎯 Quick Start

### 1. Add Your Seed URLs

Add URLs to scrape in `scraper/seeds.txt`:

```
# Add your starting URLs here, one per line
https://example.com/80s-cartoons-toys
https://example.com/transformers-history
https://example.com/gi-joe-toys
```

### 2. Configure Environment (Optional)

Copy `.env.example` to `.env` and customize settings:

```bash
cp .env.example .env
```

```env
# Optional: Use Ollama for better summaries
OLLAMA_MODEL=qwen3:8b

# Scraping settings (defaults shown)
USER_AGENT=toytoons-scraper/0.1
DELAY_MIN=0.8
DELAY_MAX=2.0
CONCURRENCY=2
SUMMARY_SENTENCES=2
```

### 3. Run the Pipeline

```bash
# Full pipeline: crawl → parse → summarize → export
make build

# Or run steps individually:
make crawl      # Scrape URLs
make parse      # Extract structured data  
make summarize  # Generate summaries
```

### 4. Start Development Server

```bash
# Start Astro development server
make web-dev

# Open http://localhost:4321 in your browser
```

## 📁 Project Structure

```
toytoons/
├── 📄 .env.example          # Environment variables template
├── 📄 .gitignore           # Git ignore rules
├── 📄 Makefile             # Cross-platform build commands
├── 📄 README.md            # This file
├── 📄 requirements.txt     # Python dependencies
│
├── 🐍 scraper/             # Python scraper module
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── models.py           # Pydantic data models
│   ├── seeds.txt           # Seed URLs (add your URLs here)
│   ├── crawl.py            # Web crawler with robots.txt respect
│   ├── parse.py            # HTML parsing and data extraction
│   ├── summarize.py        # Dual summarization (Ollama + TextRank)
│   ├── pipeline.py         # Pipeline orchestration
│   ├── cli.py              # Command-line interface
│   └── utils.py            # Utilities and helpers
│
├── 📊 data/                # Data storage
│   ├── raw/                # Raw HTML documents (JSON)
│   └── processed/          # Processed data (JSON, JSONL, CSV)
│       ├── docs.jsonl      # Individual listings
│       ├── listings.json   # Final dataset for web
│       └── listings.csv    # CSV export
│
└── 🌐 web/                 # Astro website
    ├── astro.config.mjs    # Astro configuration
    ├── netlify.toml        # Netlify deployment config
    ├── package.json        # Node.js dependencies
    ├── tailwind.config.mjs # Tailwind CSS config
    ├── tsconfig.json       # TypeScript config
    ├── public/
    │   └── favicon.svg     # Site favicon
    └── src/
        ├── lib/
        │   └── loadData.ts # Data loading utilities
        ├── components/
        │   ├── Card.astro  # Listing card component
        │   ├── Filters.tsx # Search and filter component
        │   └── Header.astro# Site header
        ├── layouts/
        │   └── Layout.astro# Base layout with SEO
        └── pages/
            ├── index.astro # Homepage with grid and filters
            └── item/
                └── [slug].astro # Individual listing pages
```

## 🔧 Available Commands

### Development Workflow

```bash
make help           # Show all available commands
make check-deps     # Verify system dependencies
make dev-setup      # Complete development environment setup
make status         # Show pipeline and data status
```

### Data Pipeline

```bash
make build          # Run complete pipeline (recommended)
make crawl          # Crawl URLs from seeds.txt
make parse          # Parse HTML into structured data
make summarize      # Generate AI/extractive summaries
```

### Web Development

```bash
make web-dev        # Start development server (localhost:4321)
make web-build      # Build static site for production
make web-preview    # Preview production build
```

### Maintenance

```bash
make clean          # Clean generated files
make deep-clean     # Clean everything including venv
```

## 🏗️ Data Model

Each listing represents a show + toyline combination:

```json
{
  "show_title": "Transformers",
  "toyline_name": "Transformers",
  "slug": "transformers",
  "era": "1980s",
  "years_aired": "1984-1987",
  "years_toyline": "1984-1990",
  "manufacturer": "Hasbro",
  "country": "United States",
  "studio_network": "Sunbow Productions",
  "description_summary": "Robots in disguise...",
  "notable_characters": ["Optimus Prime", "Megatron"],
  "source_url": "https://example.com/transformers",
  "source_title": "Transformers History",
  "first_seen": "2024-01-01T00:00:00Z",
  "parse_notes": ["Extracted from title tag"]
}
```

## 🤖 CLI Reference

The scraper includes a powerful CLI built with Typer:

```bash
# Activate virtual environment first
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Run commands
python -m scraper.cli --help

# Examples:
python -m scraper.cli build --max 50 --verbose
python -m scraper.cli crawl --delay-min 1.0 --delay-max 3.0
python -m scraper.cli summarize --sentences 3
python -m scraper.cli status
```

### CLI Options

- `--max, -m`: Limit number of URLs to process
- `--delay-min/--delay-max`: Request delay range (seconds)
- `--concurrency, -c`: Maximum concurrent requests
- `--summary-sentences, -s`: Sentences per summary
- `--verbose, -v`: Enable debug logging
- `--force-*`: Force re-processing of existing data

## 🌐 Website Features

The generated Astro website includes:

### 🏠 Homepage (`/`)
- Responsive grid layout of all listings
- Real-time search by title, toyline, manufacturer, or characters
- Filter by era (1980s, early 1990s) and manufacturer
- Statistics dashboard
- Accessible design with keyboard navigation

### 📄 Detail Pages (`/item/[slug]`)
- Complete listing information with summary
- Notable characters showcase
- Production timeline and facts
- Source attribution with external links
- SEO-optimized with meta tags and structured data

### 🔍 Search & Filtering
- Client-side search with instant results
- Multi-select filters for era and manufacturer
- URL-based filter state (shareable links)
- "No results" state with clear actions

## 🚀 Deployment

### Netlify Deployment (Recommended)

1. **Connect Repository**: Link your GitHub repository to Netlify

2. **Configure Build Settings**:
   - Build command: `make web-build`
   - Publish directory: `web/dist`
   - Node.js version: 18

3. **Environment Variables** (if using Ollama):
   ```
   OLLAMA_MODEL=qwen3:8b
   ```

4. **Deploy**: Netlify will automatically build and deploy

### Manual Deployment

```bash
# Build the site
make web-build

# Deploy the web/dist folder to your hosting provider
# Examples:
# - Upload web/dist/* to your web server
# - Use rsync: rsync -av web/dist/ user@server:/var/www/html/
# - Use GitHub Pages, Vercel, etc.
```

### GitHub Actions (Optional)

<details>
<summary>Example GitHub Actions workflow</summary>

Create `.github/workflows/deploy.yml`:

```yaml
name: Build and Deploy
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
          
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: make dev-setup
        
      - name: Build site
        run: make web-build
        
      - name: Deploy to Netlify
        uses: nwtgck/actions-netlify@v2
        with:
          publish-dir: './web/dist'
        env:
          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}
```

</details>

## 🛡️ Ethical Scraping

ToyToons follows ethical scraping practices:

### ✅ Respectful Behavior
- **robots.txt compliance**: Checks and respects robots.txt files
- **Rate limiting**: Configurable delays between requests (0.8-2.0s default)
- **Retry logic**: Exponential backoff for failed requests
- **User-Agent**: Identifies itself clearly as `toytoons-scraper/0.1`
- **Timeout handling**: Prevents hanging requests (30s timeout)

### 📜 Legal Considerations
- **Personal/Educational Use**: Designed for learning and personal projects
- **Attribution**: Maintains source URLs and attribution
- **Data Licensing**: Check individual site terms before commercial use
- **Copyright Respect**: Does not scrape copyrighted images or full text

### 🔧 Customization
Configure scraping behavior in `.env`:

```env
# Be more polite with slower sites
DELAY_MIN=2.0
DELAY_MAX=5.0

# Reduce concurrency for smaller sites
CONCURRENCY=1

# Increase timeout for slow-loading pages
TIMEOUT_SECONDS=60
```

## 🐛 Troubleshooting

### Common Issues

**"No seed URLs found"**
- Add URLs to `scraper/seeds.txt`, one per line
- Remove comment lines (starting with `#`)

**"Ollama not available"**
- Install Ollama from [ollama.ai](https://ollama.ai)
- Pull the model: `ollama pull qwen3:8b`
- Or let it fall back to TextRank summarization

**"Virtual environment not found"**
- Run `make venv` or `make dev-setup`
- On Windows, ensure Python is in PATH

**"Permission denied" on Makefile**
- On Windows, run PowerShell as Administrator
- Or use manual installation steps

**Web server shows "No data"**
- Run `make build` to generate data
- Or use sample data with `make quick-start`

### Debug Mode

Enable verbose logging:

```bash
python -m scraper.cli build --verbose
```

Check data status:

```bash
make status
```

### Getting Help

1. **Check the logs**: Look for error messages in the terminal
2. **Verify dependencies**: Run `make check-deps`
3. **Check file paths**: Ensure `scraper/seeds.txt` exists and has URLs
4. **Test individual steps**: Run `crawl`, `parse`, `summarize` separately
5. **Use sample data**: Run `make quick-start` to test with sample data

## 🤝 Contributing

ToyToons is designed as a learning project, but contributions are welcome!

### Development Workflow

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/toytoons.git
cd toytoons

# Set up development environment
make dev-setup

# Make your changes
# ...

# Test your changes
make build
make web-dev

# Commit and create pull request
```

### Ideas for Improvements

- **Data Sources**: Add more seed URLs or data sources
- **Parsing**: Improve extraction rules for specific sites
- **Summarization**: Try different AI models or summarization techniques  
- **UI/UX**: Enhance the website design or add new features
- **Export**: Add new export formats (XML, GraphQL schema, etc.)
- **Analytics**: Add usage tracking or data quality metrics

## 📚 Learning Resources

This project demonstrates several key concepts:

### Web Scraping
- [Requests vs HTTPX](https://www.python-httpx.org/compatibility/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [robots.txt Specification](https://developers.google.com/search/docs/crawling-indexing/robots/robots_txt)

### Data Processing
- [Pydantic Models](https://docs.pydantic.dev/latest/)
- [Pandas for CSV Export](https://pandas.pydata.org/docs/)
- [JSON Lines Format](https://jsonlines.org/)

### AI & Summarization
- [Ollama Documentation](https://ollama.ai/docs)
- [TextRank Algorithm](https://web.eecs.umich.edu/~mihalcea/papers/mihalcea.emnlp04.pdf)
- [Sumy Library](https://pypi.org/project/sumy/)

### Frontend Development
- [Astro Documentation](https://docs.astro.build/)
- [React Integration](https://docs.astro.build/en/guides/integrations-guide/react/)
- [Tailwind CSS](https://tailwindcss.com/docs)

### Deployment
- [Netlify Documentation](https://docs.netlify.com/)
- [Static Site Hosting](https://jamstack.org/generators/)

## 📄 License

This project is released under the MIT License. See [LICENSE](LICENSE) file for details.

The sample data and any scraped content may be subject to the original sites' terms of service and copyright. Always respect robots.txt and terms of use when scraping.

---

**Happy scraping! 🧸📺**

*Built with ❤️ for learning and nostalgia*