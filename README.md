# Data quality cli
![CI Status](https://github.com/Tac0Dude/data-quality-cli/actions/workflows/ci.yml/badge.svg)

A lightweight terminal utility to validate CSV datasets using Great Expectations v1.x.
## Features
Automated Validation: Runs data quality rules defined in JSON suites.

Timestamped Reports: Saves every result in reports/ with a unique timestamp.

Rich UI: Clean terminal output with status panels and summary tables.

Data Docs: Option to generate and open a visual HTML report (--html).
## How it's made
Core Logic: Built with Great Expectations v1.x using an ephemeral (in-memory) context for speed and portability.

CLI Engine: Powered by Typer for the command-line interface and Rich for terminal formatting.

CI/CD: Automated testing pipeline via GitHub Actions on every push.

Testing: Robust unit testing suite using Pytest.
## Installation
### Clone the repository
```bash
git clone https://github.com/Tac0Dude/data-quality-cli.git

cd data-quality-cli
```
### Install dependencies

```bash
pip install -r requirements.txt
```
## Testing
```bash
python -m pytest
```
## Usage
### Basic command
```bash
python dq.py data/your_file.csv --suite expectations/your_rules.json
```
### Full options
```bash
python dq.py [DATA_PATH] --suite [SUITE_PATH] --out [REPORT_PATH] --html
```
--suite, -s: Path to your Great Expectations JSON suite.

--out, -o: (Optional) Custom path for the JSON report. Defaults to reports/result_YYYYMMDD_HHMMSS.json.

--html: (Optional) Builds and opens the visual HTML Data Docs in your browser.
## Author
https://github.com/Tac0Dude
