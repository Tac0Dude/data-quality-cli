import typer
from pathlib import Path
import pandas as pd

app = typer.Typer(no_args_is_help=True)

@app.command()
def validate(path: str = typer.Argument(...)):
    """Validate a CSV file (basic read + summary)."""
    p = Path(path)

    if not p.exists():
        typer.echo(f"ERROR: file not found: {p}")
        raise typer.Exit(code=2)

    if p.suffix.lower() != ".csv":
        typer.echo("ERROR: only .csv files are supported for now")
        raise typer.Exit(code=2)

    typer.echo(f"Validating file: {p}")

    try:
        df = pd.read_csv(p)
    except Exception as e:
        typer.echo(f"ERROR: failed to read CSV: {e}")
        raise typer.Exit(code=2)

    typer.echo(f"Rows: {len(df)}")
    typer.echo(f"Columns: {len(df.columns)}")
    typer.echo(f"Column names: {', '.join(df.columns)}")

    # still a placeholder "verdict"
    typer.echo("Status: OK (dummy)")
    raise typer.Exit(code=0)

if __name__ == "__main__":
    app()
