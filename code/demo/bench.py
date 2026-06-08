#!/usr/bin/env python3
"""
bench.py — BenchBase experiment runner.

    python bench.py load samples/sample_tpch_config_30_min.xml
    python bench.py run  samples/tpch_Q7_disk.xml
    python bench.py suite samples/
"""

from __future__ import annotations

import threading
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Annotated

import docker
import typer
from rich.console import Console
from rich.text import Text

BENCHBASE_IMAGE = "benchbase.azurecr.io/benchbase:latest"
POSTGRES_CONTAINER = "tagd-postgres"
RESULTS_BASE = Path("./results")

app = typer.Typer(
    name="bench", help="Run BenchBase TPC-H experiments.", no_args_is_help=True
)
console = Console()

# ---------------------------------------------------------------------------


@app.command()
def load(
    config: Annotated[
        Path, typer.Argument(help="Config XML for schema creation and data loading.")
    ],
) -> None:
    """Create schema and load data. Run once before any experiments."""
    _run(docker.from_env(), config, RESULTS_BASE / "load", create=True, load=True)


@app.command()
def run(
    config: Annotated[Path, typer.Argument(help="Config XML for the experiment.")],
    results_dir: Annotated[
        Path | None, typer.Option(help="Override results directory.")
    ] = None,
) -> None:
    """Run a single experiment."""
    ok = _run(
        docker.from_env(),
        config,
        results_dir or RESULTS_BASE / config.stem,
        execute=True,
    )
    if not ok:
        raise typer.Exit(1)


@app.command()
def suite(
    directory: Annotated[Path, typer.Argument(help="Directory of experiment configs.")],
    exclude: Annotated[
        str, typer.Option(help="Skip filenames containing this string.")
    ] = "sample_",
) -> None:
    """Run all experiments in a directory sequentially."""
    configs = sorted(p for p in directory.glob("*.xml") if exclude not in p.name)
    if not configs:
        console.print(f"[yellow]No configs found in {directory}[/yellow]")
        raise typer.Exit(1)

    client = docker.from_env()
    outcomes = {
        cfg: _run(client, cfg, RESULTS_BASE / cfg.stem, execute=True) for cfg in configs
    }

    console.print("\n[bold]Suite summary[/bold]")
    for cfg, ok in outcomes.items():
        console.print(f"  {'[green]✓[/green]' if ok else '[red]✗[/red]'}  {cfg.name}")
    if not all(outcomes.values()):
        raise typer.Exit(1)


# ---------------------------------------------------------------------------


def _run(
    client: docker.DockerClient,
    config: Path,
    results_dir: Path,
    *,
    create=False,
    load=False,
    execute=False,
) -> bool:
    results_dir.mkdir(parents=True, exist_ok=True)
    config_dest = f"/benchbase/config/postgres/{config.name}"

    cmd = ["-b", "tpch", "-c", config_dest]
    if create:
        cmd += ["--create=true"]
    if load:
        cmd += ["--load=true"]
    if execute:
        cmd += ["--execute=true"]

    if execute:
        t = threading.Thread(
            target=_iostat,
            args=(client, results_dir / "iostat.txt", _duration(config)),
            daemon=True,
        )
        t.start()

    container = client.containers.run(
        BENCHBASE_IMAGE,
        cmd,
        environment={"BENCHBASE_PROFILE": "postgres"},
        network_mode="host",
        volumes={
            str(config.resolve()): {"bind": config_dest, "mode": "ro"},
            str(results_dir.resolve()): {"bind": "/benchbase/results", "mode": "rw"},
        },
        detach=True,
        remove=False,
    )
    for chunk in container.logs(stream=True, follow=True):
        console.print(Text(chunk.decode(errors="replace").rstrip(), style="dim"))

    ok = container.wait()["StatusCode"] == 0
    container.remove()

    if execute:
        t.join(timeout=15)

    status = "[green]✓[/green]" if ok else "[red]✗[/red]"
    console.print(f"{status} {config.name}  →  {results_dir.resolve()}\n")
    return ok


def _iostat(client: docker.DockerClient, output: Path, duration_s: int) -> None:
    try:
        pg = client.containers.get(POSTGRES_CONTAINER)
        result = pg.exec_run(
            ["iostat", "-x", "1", str(duration_s + 5)], stream=True, demux=False
        )
        output.write_bytes(b"".join(result.output))
    except Exception as exc:
        console.print(f"[yellow]iostat: {exc}[/yellow]")


def _duration(config: Path) -> int:
    el = ET.parse(config).getroot().find(".//work/time")
    return int(el.text) if el is not None and el.text else 300


if __name__ == "__main__":
    app()
