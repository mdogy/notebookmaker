"""Command-line interface for NotebookMaker."""

from pathlib import Path

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
@click.option(
    "--provider",
    "-p",
    type=click.Choice(["anthropic", "google", "openai", "openrouter"]),
    default="anthropic",
    help="LLM provider to use (default: anthropic)",
)
@click.option(
    "--model",
    "-m",
    type=str,
    default=None,
    help="Model name (uses provider default if not specified)",
)
def main(
    input_file: Path, output_dir: Path, provider: str, model: str | None
) -> None:
    """Convert a lecture PDF or PowerPoint to Jupyter notebooks.

    Args:
        input_file: Path to the PDF or PowerPoint file
        output_dir: Directory where notebooks will be saved
        provider: LLM provider to use
        model: Optional model name
    """
    click.echo(f"Processing: {input_file}")
    click.echo(f"Provider: {provider}")
    if model:
        click.echo(f"Model: {model}")

    # Process the lecture file
    result = process_lecture(input_file, output_dir, provider=provider, model=model)

    click.echo(f"\nGenerated notebooks saved to: {output_dir}")
    click.echo(f"  - Instructor: {result['instructor']}")
    click.echo(f"  - Student: {result['student']}")


if __name__ == "__main__":
    main()
