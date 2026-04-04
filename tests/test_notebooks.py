"""Smoke tests for Jupyter notebooks — execute headless and check for errors."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

NOTEBOOK_DIR = Path(__file__).parent.parent / "notebooks"

NOTEBOOKS = [
    "01_retention.ipynb",
    "02_monetization.ipynb",
    "03_economy.ipynb",
]


@pytest.mark.slow
@pytest.mark.parametrize("notebook", NOTEBOOKS)
def test_notebook_executes(notebook):
    """Run notebook headless and verify no cells raise exceptions."""
    nb_path = NOTEBOOK_DIR / notebook
    assert nb_path.exists(), f"Notebook not found: {nb_path}"

    env = {**os.environ, "ACO_HEADLESS": "1"}

    result = subprocess.run(
        [
            sys.executable, "-m", "jupyter", "nbconvert",
            "--to", "notebook",
            "--execute",
            "--ExecutePreprocessor.timeout=300",
            "--ExecutePreprocessor.kernel_name=python3",
            "--output", f"/tmp/test_{notebook}",
            str(nb_path),
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(nb_path.parent.parent),
    )

    assert result.returncode == 0, (
        f"Notebook {notebook} failed:\n"
        f"STDOUT: {result.stdout[-500:] if result.stdout else 'none'}\n"
        f"STDERR: {result.stderr[-500:] if result.stderr else 'none'}"
    )
