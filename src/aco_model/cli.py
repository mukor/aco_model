"""CLI interface using Typer."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from aco_model.config import load_config

app = typer.Typer(help="ACO Model - Game economic model")
console = Console()


@app.command()
def simulate(
    config_path: Path = typer.Option("config.yaml", "--config", "-c", help="Config file path"),
    output: Path = typer.Option("output/retention_sim.csv", "--output", "-o", help="CSV output path"),
):
    """Run the retention simulation and display results."""
    from aco_model.retention import load_installs, simulate as run_sim

    cfg = load_config(config_path)
    installs = load_installs(cfg.installs_path)
    sim = run_sim(installs, cfg.retention, cfg.sim_days)
    results = sim.to_dataframe()

    # Write CSV
    output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output, index=False)
    console.print(f"\n[dim]Results written to {output}[/dim]\n")

    # Display Rich table
    table = Table(title="Retention Simulation")
    table.add_column("Day", justify="right", style="cyan")
    table.add_column("New Installs", justify="right")
    table.add_column("DAU", justify="right", style="green")

    for _, row in results.iterrows():
        table.add_row(
            str(int(row["day"])),
            f"{int(row['new_installs']):,}",
            f"{int(row['dau']):,}",
        )

    console.print(table)


@app.command()
def revenue(
    config_path: Path = typer.Option("config.yaml", "--config", "-c", help="Config file path"),
    output: Path = typer.Option("output/revenue_estimate.csv", "--output", "-o", help="CSV output path"),
    pct_payers: float = typer.Option(None, "--pct-payers", help="Override % payers (0.0-1.0)"),
    arppu: float = typer.Option(None, "--arppu", help="Override ARPPU ($)"),
):
    """Estimate revenue from the retention simulation."""
    from aco_model.models import MonetizationParams
    from aco_model.monetization import estimate_revenue
    from aco_model.retention import load_installs, simulate as run_sim

    cfg = load_config(config_path)
    installs = load_installs(cfg.installs_path)
    sim = run_sim(installs, cfg.retention, cfg.sim_days)

    # Apply CLI overrides
    params = cfg.monetization
    if pct_payers is not None or arppu is not None:
        params = MonetizationParams(
            pct_payers=pct_payers if pct_payers is not None else params.pct_payers,
            arppu=arppu if arppu is not None else params.arppu,
        )

    rev = estimate_revenue(sim, params)
    results = rev.to_dataframe()

    # Write CSV
    output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output, index=False)
    console.print(f"\n[dim]Results written to {output}[/dim]")
    console.print(f"[dim]Assumptions: {params.pct_payers:.1%} payers, ${params.arppu:.2f} ARPPU[/dim]\n")

    # Display Rich table
    table = Table(title="Revenue Estimate")
    table.add_column("Day", justify="right", style="cyan")
    table.add_column("DAU", justify="right")
    table.add_column("Payers", justify="right")
    table.add_column("Daily Rev", justify="right", style="green")
    table.add_column("Cumulative Rev", justify="right", style="bold green")

    for _, row in results.iterrows():
        table.add_row(
            str(int(row["day"])),
            f"{int(row['dau']):,}",
            f"{int(row['payers']):,}",
            f"${row['daily_revenue_usd']:,.2f}",
            f"${row['cumulative_revenue_usd']:,.2f}",
        )

    console.print(table)
    arpdau = params.pct_payers * params.arppu
    console.print(f"\n[bold]Total Revenue: ${rev.total_revenue:,.2f}[/bold]")
    console.print(f"[bold]ARPDAU: ${arpdau:,.4f}[/bold]")
    console.print(f"[bold]Avg Revenue per Cohort: ${rev.avg_revenue_per_cohort:,.2f}[/bold]")


@app.command()
def status():
    """Show current simulation status."""
    console.print("No simulation running.")
