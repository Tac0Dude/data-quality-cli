import json
import pandas as pd
import typer
import great_expectations as gx
import webbrowser
import logging
from pathlib import Path
from datetime import datetime
from great_expectations.core.expectation_suite import ExpectationSuite
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Suppress verbose Great Expectations logs to keep CLI output focused on user-facing info
logging.getLogger("great_expectations").setLevel(logging.ERROR)

app = typer.Typer(help="Data Quality CLI based on Great Expectations v1.0+")
console = Console()

def load_suite_safely(path: Path) -> ExpectationSuite:
    """
    Load a JSON expectation suite and migrate it to GX v1.x schema on-the-fly.
    
    Args:
        path (Path): The file system path to the JSON expectation suite.
        
    Returns:
        ExpectationSuite: A validated GX ExpectationSuite object.
        
    Raises:
        Exit: If the JSON is invalid or the path does not exist.
    """
    try:
        content = path.read_text(encoding="utf-8").strip()
        suite_dict = json.loads(content)
        
        # Schema migration: Great Expectations v1.0 changed several key names 
        # (e.g., 'expectation_suite_name' became 'name').
        if "expectation_suite_name" in suite_dict:
            suite_dict["name"] = suite_dict.pop("expectation_suite_name")
            
        if "expectations" in suite_dict:
            for exp in suite_dict["expectations"]:
                if "expectation_type" in exp:
                    exp["type"] = exp.pop("expectation_type")
            
        return ExpectationSuite(**suite_dict)
    except Exception as e:
        console.print(f"[bold red]Expectation Suite loading error:[/bold red] {e}")
        raise typer.Exit(code=2)

@app.command()
def validate(
    data: Path = typer.Argument(..., help="Path to the source CSV file"),
    suite: Path = typer.Option(..., "--suite", "-s", help="Path to the JSON Expectation Suite"),
    out: Path = typer.Option(
        None, "--out", "-o", 
        help="Destination path for JSON report. Defaults to reports/result_TIMESTAMP.json"
    ),
    html: bool = typer.Option(False, "--html", help="Generate and auto-open HTML Data Docs"),
):
    """
    Execute data quality validation and generate timestamped reports.
    
    This command orchestrates the validation process:
    1. Initialize an ephemeral GX context.
    2. Load data and rules.
    3. Run the validation engine.
    4. Export results to JSON and optionally HTML.
    """
    
    # Pre-flight check: Ensure input data exists before spinning up the engine
    if not data.exists():
        console.print(f"[bold red]Input data file not found:[/bold red] {data}")
        raise typer.Exit(code=2)

    # Dynamic output path: Use current timestamp if no output path is provided.
    # This prevents overwriting previous validation results.
    if out is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = Path(f"reports/result_{timestamp}.json")

    console.print(Panel(f"[bold cyan]Starting Validation Engine:[/bold cyan] {data.name}", border_style="blue"))

    exit_code = 0
    try:
        # Step 1: Initialize Ephemeral Context
        # Ephemeral mode keeps everything in memory, avoiding the need for a local /gx folder.
        context = gx.get_context(mode="ephemeral")
        df = pd.read_csv(data, sep=',', encoding='utf-8')
        
        # Step 2: Define Data Infrastructure
        # We define a DataSource and an Asset to describe how to handle the CSV data.
        ds = context.data_sources.add_pandas(name="default_datasource")
        asset = ds.add_dataframe_asset(name="input_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("default_batch_definition")

        # Step 3: Load Validation Rules
        suite_obj = load_suite_safely(suite)
        context.suites.add(suite_obj)

        # Step 4: Create Validation Definition
        # Links the data source with the expectation suite.
        validation_def = context.validation_definitions.add(
            gx.ValidationDefinition(
                name=f"validation_{data.stem}_{datetime.now().strftime('%H%M%S')}",
                data=batch_def,
                suite=suite_obj
            )
        )
        
        # Step 5: Execute Engine
        # The run method processes the rules against the provided DataFrame.
        with console.status("[bold green]Running validation rules...") as status:
            result = validation_def.run(batch_parameters={"dataframe": df})

        # Step 6: Process Results
        success = result.success
        stats = result.statistics

        # Persist result to JSON for auditing or machine consumption
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result.to_json_dict(), indent=2), encoding="utf-8")
        console.print(f"[dim]JSON report saved to: {out}[/dim]")

        # Step 7: (Optional) Generate Human-Readable HTML
        if html:
            with console.status("[bold magenta]Building Data Docs...") as status:
                context.build_data_docs()
                docs_url = context.get_docs_sites_urls()[0]["site_url"]
                webbrowser.open(docs_url)
            console.print(f"[bold magenta]HTML Report ready:[/bold magenta] {docs_url}")

        # Step 8: Terminal UI Output
        # Create a summary table for immediate feedback
        summary = Table(show_header=True, header_style="bold magenta")
        summary.add_column("Validation Metric", style="dim")
        summary.add_column("Count", justify="right")
        summary.add_row("Total Rules Evaluated", str(stats.get('evaluated_expectations')))
        summary.add_row("Passed ✅", f"[green]{stats.get('successful_expectations')}[/green]")
        summary.add_row("Failed ❌", f"[red]{stats.get('unsuccessful_expectations')}[/red]")
        
        console.print(summary)

        # Step 9: Exit Status Handling
        # Return exit code 0 for success, 1 for failed DQ, 2 for critical errors
        if success:
            console.print(Panel("[bold green]RESULT: DATA QUALITY PASSED[/bold green]", border_style="green"))
            exit_code = 0
        else:
            console.print(Panel("[bold red]RESULT: DATA QUALITY FAILED[/bold red]", border_style="red"))
            exit_code = 1

    except Exception as e:
        console.print(f"[bold red]Execution halted by critical error:[/bold red] {e}")
        raise typer.Exit(code=2)

    raise typer.Exit(code=exit_code)

if __name__ == "__main__":
    app()