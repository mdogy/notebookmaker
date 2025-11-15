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
    "--analysis-provider",
    type=click.Choice(["anthropic", "google", "openai", "openrouter"]),
    default="google",
    help="LLM provider for Phase 1 analysis (default: google)",
)
@click.option(
    "--generation-provider",
    type=click.Choice(["anthropic", "google", "openai", "openrouter"]),
    default=None,
    help="LLM provider for Phase 2 generation (default: same as analysis)",
)
@click.option(
    "--analysis-model",
    type=str,
    default=None,
    help="Model for Phase 1 (uses provider default if not specified)",
)
@click.option(
    "--generation-model",
    type=str,
    default=None,
    help="Model for Phase 2 (uses provider default if not specified)",
)
@click.option(
    "--min-priority",
    type=int,
    default=5,
    help="Minimum section priority to include (default: 5)",
)
@click.option(
    "--chunk-size",
    type=int,
    default=10,
    help="Pages per API call in Phase 1 (default: 10)",
)
def main(
    input_file: Path,
    output_dir: Path,
    analysis_provider: str,
    generation_provider: str | None,
    analysis_model: str | None,
    generation_model: str | None,
    min_priority: int,
    chunk_size: int,
) -> None:
    """Convert a lecture PDF to Jupyter notebooks using two-phase architecture.

    Phase 1: Analyze PDF with vision LLM
    Phase 2: Generate notebooks from analysis

    Args:
        input_file: Path to the PDF file
        output_dir: Directory where notebooks will be saved
        analysis_provider: LLM provider for Phase 1
        generation_provider: LLM provider for Phase 2
        analysis_model: Model for Phase 1
        generation_model: Model for Phase 2
        min_priority: Minimum section priority
        chunk_size: Pages per API call
    """
    click.echo(f"Processing: {input_file}")
    click.echo(f"Analysis provider: {analysis_provider}")
    if generation_provider:
        click.echo(f"Generation provider: {generation_provider}")

    # Process the lecture file
    result = process_lecture(
        input_file,
        output_dir,
        analysis_provider=analysis_provider,
        generation_provider=generation_provider,
        analysis_model=analysis_model,
        generation_model=generation_model,
        min_priority=min_priority,
        chunk_size=chunk_size,
    )

    click.echo(f"\nGenerated notebooks saved to: {output_dir}")
    click.echo(f"  - Instructor: {result['instructor']}")
    click.echo(f"  - Student: {result['student']}")


if __name__ == "__main__":
    main()
