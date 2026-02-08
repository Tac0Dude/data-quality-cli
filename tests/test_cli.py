import pytest
from typer.testing import CliRunner
from dq import app
from pathlib import Path

# Initialize the Typer CliRunner for testing terminal interactions
runner = CliRunner()

# Test data configuration
# Using existing project files to validate the engine behavior
VALID_CSV = "examples/drug.csv"
INVALID_CSV = "tests/invalid_drug.csv"  # Ensure this file contains schema/logic violations
SUITE_JSON = "expectations/drugs.json"

def test_validate_success():
    """
    Test the validation command with compliant data.
    Expects exit code 0 and the 'PASSED' success message.
    """
    result = runner.invoke(app, [VALID_CSV, "--suite", SUITE_JSON])
    
    assert result.exit_code == 0
    # Matches the updated output strings in dq.py
    assert "RESULT: DATA QUALITY PASSED" in result.stdout

def test_validate_failure():
    """
    Test the validation command with non-compliant data.
    Expects exit code 1 and the 'FAILED' status message.
    """
    # This test verifies that the engine correctly identifies data quality issues
    result = runner.invoke(app, [INVALID_CSV, "--suite", SUITE_JSON])

    assert result.exit_code == 1
    assert "RESULT: DATA QUALITY FAILED" in result.stdout

def test_file_not_found():
    """
    Test the CLI robustness when the input source is missing.
    Expects exit code 2 and a clear error message.
    """
    result = runner.invoke(app, ["non_existent.csv", "--suite", SUITE_JSON])

    assert result.exit_code == 2
    # Verifies the exact error message defined in the CLI pre-flight check
    assert "Input data file not found" in result.stdout