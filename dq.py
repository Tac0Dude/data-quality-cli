import json
import pandas as pd
import typer
import great_expectations as gx
from pathlib import Path
from great_expectations.core.expectation_suite import ExpectationSuite
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Initialisation
app = typer.Typer(help="Data Quality CLI based on Great Expectations v1.0+")
console = Console()

def load_suite_safely(path: Path) -> ExpectationSuite:
    """Loads a JSON expectation suite and converts legacy v0.x keys to modern v1.x format."""
    try:
        content = path.read_text(encoding="utf-8").strip()
        suite_dict = json.loads(content)
        
        if "expectation_suite_name" in suite_dict:
            suite_dict["name"] = suite_dict.pop("expectation_suite_name")
            
        if "expectations" in suite_dict:
            for exp in suite_dict["expectations"]:
                if "expectation_type" in exp:
                    exp["type"] = exp.pop("expectation_type")
            
        return ExpectationSuite(**suite_dict)
    except Exception as e:
        console.print(f"[bold red]❌ Suite loading error:[/bold red] {e}")
        raise typer.Exit(code=2)

@app.command()
def validate(
    data: Path = typer.Argument(..., help="Path to the source CSV file"),
    suite: Path = typer.Option(..., "--suite", "-s", help="Path to the Expectation Suite JSON"),
    out: Path = typer.Option(Path("reports/result.json"), "--out", "-o", help="Path to save the validation report"),
):
    """Run data quality validation with style and precision."""
    
    if not data.exists():
        console.print(f"[bold red]❌ Data file not found:[/bold red] {data}")
        raise typer.Exit(code=2)

    console.print(Panel(f"🔍 [bold cyan]Starting Validation:[/bold cyan] {data.name}", border_style="blue"))

    exit_code = 0
    try:
        # Initialisation silencieuse de GX
        context = gx.get_context(mode="ephemeral")
        df = pd.read_csv(data)
        
        ds = context.data_sources.add_pandas(name="default_datasource")
        asset = ds.add_dataframe_asset(name="input_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("default_batch_definition")
        batch = batch_def.get_batch(batch_parameters={"dataframe": df})

        suite_obj = load_suite_safely(suite)
        context.suites.add(suite_obj)

        validator = context.get_validator(batch=batch, expectation_suite=suite_obj)
        
        with console.status("[bold green]Calculating metrics...") as status:
            result = validator.validate()

        # Sauvegarde du rapport
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result.to_json_dict(), indent=2), encoding="utf-8")

        # Extraction des stats
        stats = result.get("statistics", {})
        success = result.get("success")

        # --- Affichage du Tableau de Résultat ---
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="dim")
        table.add_column("Count", justify="right")
        
        table.add_row("Total Expectations", str(stats.get('evaluated_expectations')))
        table.add_row("Passed ✅", f"[green]{stats.get('successful_expectations')}[/green]")
        table.add_row("Failed ❌", f"[red]{stats.get('unsuccessful_expectations')}[/red]")
        
        console.print(table)

        if success:
            console.print(Panel("[bold green]STATUS: PASSED[/bold green]", border_style="green"))
            exit_code = 0
        else:
            console.print(Panel("[bold red]STATUS: FAILED[/bold red]", border_style="red"))
            exit_code = 1

    except Exception as e:
        console.print(f"[bold red]💥 Critical Error:[/bold red] {e}")
        raise typer.Exit(code=2)

    raise typer.Exit(code=exit_code)

if __name__ == "__main__":
    app()