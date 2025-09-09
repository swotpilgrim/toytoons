"""
Command-line interface for the toytoons scraper.
"""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .config import Config
from .pipeline import ToytoonsePipeline
from .utils import setup_logging

app = typer.Typer(help="Toytoons scraper - Extract 1980s-1990s cartoon and toy data")
console = Console()


@app.command()
def build(
    max_urls: Optional[int] = typer.Option(None, "--max", "-m", help="Maximum number of URLs to process"),
    delay_min: Optional[float] = typer.Option(None, "--delay-min", help="Minimum delay between requests (seconds)"),
    delay_max: Optional[float] = typer.Option(None, "--delay-max", help="Maximum delay between requests (seconds)"),
    concurrency: Optional[int] = typer.Option(None, "--concurrency", "-c", help="Maximum concurrent requests"),
    summary_sentences: Optional[int] = typer.Option(None, "--summary-sentences", "-s", help="Number of sentences in summaries"),
    force_crawl: bool = typer.Option(False, "--force-crawl", help="Force re-crawling even if data exists"),
    force_parse: bool = typer.Option(False, "--force-parse", help="Force re-parsing even if data exists"),
    force_summarize: bool = typer.Option(False, "--force-summarize", help="Force re-summarization even if summaries exist"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")
):
    """Run the complete pipeline: crawl -> parse -> summarize -> export."""
    
    # Set up logging
    log_level = "DEBUG" if verbose else "INFO"
    logger = setup_logging(log_level)
    
    # Override config if specified
    if delay_min is not None:
        Config.DELAY_MIN = delay_min
    if delay_max is not None:
        Config.DELAY_MAX = delay_max
    if concurrency is not None:
        Config.CONCURRENCY = concurrency
    if summary_sentences is not None:
        Config.SUMMARY_SENTENCES = summary_sentences
    
    # Show configuration
    _show_config()
    
    # Run pipeline
    async def run():
        pipeline = ToytoonsePipeline()
        stats = await pipeline.run_full_pipeline(
            max_urls=max_urls,
            force_crawl=force_crawl,
            force_parse=force_parse,
            force_summarize=force_summarize
        )
        return stats
    
    try:
        stats = asyncio.run(run())
        _show_results(stats)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Pipeline interrupted by user[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Pipeline failed: {e}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def crawl(
    max_urls: Optional[int] = typer.Option(None, "--max", "-m", help="Maximum number of URLs to crawl"),
    delay_min: Optional[float] = typer.Option(None, "--delay-min", help="Minimum delay between requests (seconds)"),
    delay_max: Optional[float] = typer.Option(None, "--delay-max", help="Maximum delay between requests (seconds)"),
    concurrency: Optional[int] = typer.Option(None, "--concurrency", "-c", help="Maximum concurrent requests"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")
):
    """Crawl URLs and save raw HTML data."""
    
    # Set up logging
    log_level = "DEBUG" if verbose else "INFO"
    logger = setup_logging(log_level)
    
    # Override config if specified
    if delay_min is not None:
        Config.DELAY_MIN = delay_min
    if delay_max is not None:
        Config.DELAY_MAX = delay_max
    if concurrency is not None:
        Config.CONCURRENCY = concurrency
    
    _show_config()
    
    async def run():
        pipeline = ToytoonsePipeline()
        docs = await pipeline.crawl_only(max_urls=max_urls)
        return docs
    
    try:
        docs = asyncio.run(run())
        console.print(f"[green]✓ Crawled {len(docs)} documents[/green]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Crawling interrupted by user[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Crawling failed: {e}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def parse(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")
):
    """Parse existing raw HTML data into structured listings."""
    
    # Set up logging
    log_level = "DEBUG" if verbose else "INFO"
    logger = setup_logging(log_level)
    
    try:
        pipeline = ToytoonsePipeline()
        listings = pipeline.parse_only()
        console.print(f"[green]✓ Created {len(listings)} listings[/green]")
        
    except Exception as e:
        console.print(f"[red]Parsing failed: {e}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def summarize(
    summary_sentences: Optional[int] = typer.Option(None, "--sentences", "-s", help="Number of sentences in summaries"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")
):
    """Generate summaries for existing listings."""
    
    # Set up logging
    log_level = "DEBUG" if verbose else "INFO"
    logger = setup_logging(log_level)
    
    # Override config if specified
    if summary_sentences is not None:
        Config.SUMMARY_SENTENCES = summary_sentences
    
    async def run():
        pipeline = ToytoonsePipeline()
        listings = await pipeline.summarize_only()
        return listings
    
    try:
        listings = asyncio.run(run())
        summaries_count = sum(1 for l in listings if l.description_summary)
        console.print(f"[green]✓ Generated summaries for {summaries_count}/{len(listings)} listings[/green]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Summarization interrupted by user[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Summarization failed: {e}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def config():
    """Show current configuration."""
    _show_config()


@app.command()
def status():
    """Show status of data files and processing."""
    _show_status()


def _show_config():
    """Display current configuration."""
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("User Agent", Config.USER_AGENT)
    table.add_row("Delay Min/Max", f"{Config.DELAY_MIN}s - {Config.DELAY_MAX}s")
    table.add_row("Concurrency", str(Config.CONCURRENCY))
    table.add_row("Timeout", f"{Config.TIMEOUT_SECONDS}s")
    table.add_row("Max Retries", str(Config.MAX_RETRIES))
    table.add_row("Summary Sentences", str(Config.SUMMARY_SENTENCES))
    table.add_row("Ollama Model", Config.OLLAMA_MODEL or "[dim]Not configured[/dim]")
    table.add_row("Chunk Size", str(Config.CHUNK_SIZE))
    
    console.print(table)


def _show_status():
    """Display status of data files."""
    table = Table(title="Data Status")
    table.add_column("File", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Count/Size", style="yellow")
    
    # Check seeds file
    if Config.SEEDS_FILE.exists():
        from .utils import load_seeds
        seeds = load_seeds(Config.SEEDS_FILE)
        table.add_row("Seeds", "✓ Found", f"{len(seeds)} URLs")
    else:
        table.add_row("Seeds", "[red]✗ Missing[/red]", "Add URLs to scraper/seeds.txt")
    
    # Check raw data
    if Config.RAW_DATA_DIR.exists():
        raw_files = list(Config.RAW_DATA_DIR.glob("*.json"))
        if raw_files:
            table.add_row("Raw Data", "✓ Found", f"{len(raw_files)} documents")
        else:
            table.add_row("Raw Data", "[dim]Empty[/dim]", "0 documents")
    else:
        table.add_row("Raw Data", "[dim]Not created[/dim]", "Run crawl first")
    
    # Check processed data
    if Config.DOCS_JSONL.exists():
        from .utils import load_jsonl
        docs = load_jsonl(Config.DOCS_JSONL)
        table.add_row("Parsed Data", "✓ Found", f"{len(docs)} listings")
    else:
        table.add_row("Parsed Data", "[dim]Not created[/dim]", "Run parse first")
    
    if Config.LISTINGS_JSON.exists():
        from .utils import load_json
        data = load_json(Config.LISTINGS_JSON)
        table.add_row("JSON Export", "✓ Found", f"{len(data)} listings")
    else:
        table.add_row("JSON Export", "[dim]Not created[/dim]", "Run build first")
    
    if Config.LISTINGS_CSV.exists():
        import pandas as pd
        df = pd.read_csv(Config.LISTINGS_CSV)
        table.add_row("CSV Export", "✓ Found", f"{len(df)} listings")
    else:
        table.add_row("CSV Export", "[dim]Not created[/dim]", "Run build first")
    
    console.print(table)


def _show_results(stats):
    """Display pipeline results."""
    table = Table(title="Pipeline Results")
    table.add_column("Stage", style="cyan")
    table.add_column("Result", style="green")
    
    table.add_row("URLs Crawled", str(stats['urls_crawled']))
    table.add_row("Documents Parsed", str(stats['docs_parsed']))
    table.add_row("Listings Created", str(stats['listings_created']))
    table.add_row("Summaries Generated", str(stats['summaries_generated']))
    table.add_row("Export Files", str(stats['exports_created']))
    table.add_row("Duration", str(stats['duration']).split('.')[0])  # Remove microseconds
    
    console.print(table)
    
    # Show file locations
    console.print("\n[bold]Output Files:[/bold]")
    if Config.LISTINGS_JSON.exists():
        console.print(f"• JSON: [cyan]{Config.LISTINGS_JSON}[/cyan]")
    if Config.LISTINGS_CSV.exists():
        console.print(f"• CSV: [cyan]{Config.LISTINGS_CSV}[/cyan]")


if __name__ == "__main__":
    app()