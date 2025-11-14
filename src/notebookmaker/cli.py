"""Command-line interface for NotebookMaker."""

from pathlib import Path
from typing import Annotated

import click

from notebookmaker.utils import process_lecture


@click.command()
@click.argument(
    "input_file",
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default="outputs",
    help="Directory to save generated notebooks (default: outputs/)",
)
def main(input_file: Path, output_dir: Path) -> None:
    """Convert a lecture PDF or PowerPoint to Jupyter notebooks.

    Args:
        input_file: Path to the PDF or PowerPoint file
        output_dir: Directory where notebooks will be saved
    """
    click.echo(f"Processing: {input_file}")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process the lecture file
    result = process_lecture(input_file, output_dir)

    click.echo(f"Generated notebooks saved to: {output_dir}")
    click.echo(f"  - {result['notebook1']}")
    click.echo(f"  - {result['notebook2']}")


if __name__ == "__main__":
    main()
