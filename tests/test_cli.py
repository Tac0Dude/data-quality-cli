import pytest
from typer.testing import CliRunner
from dq import app
from pathlib import Path

runner = CliRunner()

# On définit les chemins de manière absolue par rapport à l'emplacement du fichier de test
BASE_DIR = Path(__file__).parent.parent
VALID_CSV = str(BASE_DIR / "tests" / "valid_drug.csv")
INVALID_CSV = str(BASE_DIR / "tests" / "invalid_drug.csv")
SUITE_JSON = str(BASE_DIR / "expectations" / "drugs.json")

def test_validate_success():
    """Vérifie qu'un fichier correct renvoie un succès (exit code 0)."""
    result = runner.invoke(app, [VALID_CSV, "--suite", SUITE_JSON])
    # Si ça échoue, on affiche la sortie pour comprendre pourquoi
    if result.exit_code != 0:
        print(f"DEBUG STDOUT: {result.stdout}")
    
    assert result.exit_code == 0
    assert "STATUS: PASSED" in result.stdout

def test_validate_failure():
    """Vérifie qu'un fichier erroné renvoie un échec (exit code 1)."""
    result = runner.invoke(app, [INVALID_CSV, "--suite", SUITE_JSON])
    
    assert result.exit_code == 1
    assert "STATUS: FAILED" in result.stdout

def test_file_not_found():
    """Vérifie la gestion d'erreur si le CSV n'existe pas (exit code 2)."""
    result = runner.invoke(app, ["non_existent.csv", "--suite", SUITE_JSON])
    
    assert result.exit_code == 2
    assert "Data file not found" in result.stdout