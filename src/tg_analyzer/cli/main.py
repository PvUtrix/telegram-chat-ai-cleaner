"""
Command Line Interface for Telegram Chat Analyzer
"""

import asyncio
import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..core import TelegramAnalyzer
from ..config.config_manager import ConfigManager
from ..llm.templates.default_prompts import list_available_templates
from ..processors.batch_processor import BatchProcessor
from ..processors.file_manager import FileManager


# Initialize Rich console for beautiful output
console = Console()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class CLIContext:
    """Context object for CLI commands"""

    def __init__(self):
        self.config = None
        self.analyzer = None
        self.file_manager = None

    def ensure_initialized(self):
        """Ensure all components are initialized"""
        if self.config is None:
            self.config = ConfigManager()

        if self.analyzer is None:
            self.analyzer = TelegramAnalyzer()

        if self.file_manager is None:
            self.file_manager = FileManager(self.config)


# Global context
ctx = CLIContext()


def select_input_file():
    """Automatically select or prompt for input file from data/input/ directory"""
    input_dir = ctx.file_manager.get_input_dir()
    json_files = list(input_dir.glob("*.json"))

    if not json_files:
        console.print(f"[red]No JSON files found in {input_dir}[/red]")
        console.print(
            "Please place your Telegram export JSON files in the data/input/ directory."
        )
        return None

    if len(json_files) == 1:
        # Only one file, use it automatically
        selected_file = json_files[0]
        console.print(f"[green]Using file:[/green] {selected_file.name}")
        return str(selected_file)

    # Multiple files, show selection menu
    console.print(
        f"[blue]Found {len(json_files)} JSON files in input directory:[/blue]"
    )
    console.print()

    for i, file_path in enumerate(json_files, 1):
        file_size = file_path.stat().st_size / (1024 * 1024)  # Size in MB
        console.print(f"{i:2d}. {file_path.name} ({file_size:.1f} MB)")

    console.print()
    console.print(
        "[dim]Select a file by entering its number to process it for cleaning and analysis[/dim]"
    )
    console.print("[dim]Example: Enter 1 to select the first file[/dim]")
    while True:
        try:
            choice = click.prompt("Select a file (number)", type=int)
            if 1 <= choice <= len(json_files):
                selected_file = json_files[choice - 1]
                console.print(f"[green]Selected:[/green] {selected_file.name}")
                return str(selected_file)
            else:
                console.print(
                    f"[red]Please enter a number between 1 and {len(json_files)}[/red]"
                )
        except click.Abort:
            return None


def handle_errors(f):
    """Decorator to handle and display errors nicely"""

    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}")
            logger.exception("CLI command failed")
            sys.exit(1)

    return wrapper


@click.group()
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True),
    help="Path to config file (default: auto-detect)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(click_ctx, config_path, verbose):
    """Telegram Chat Analyzer - Clean, analyze, and vectorize Telegram exports"""

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Store config path in context
    click_ctx.ensure_object(dict)
    click_ctx.obj["config_path"] = config_path


@cli.command()
@click.argument("input_file", required=False)
@click.option(
    "--approach",
    type=click.Choice(["privacy", "size", "context"]),
    default=None,
    help="Cleaning approach",
)
@click.option(
    "--level", type=click.IntRange(1, 3), default=None, help="Cleaning level (1-3)"
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "markdown", "csv"]),
    default=None,
    help="Output format",
)
@click.option(
    "--output",
    "output_file",
    type=click.Path(),
    help="Output file path (default: auto-generate)",
)
@click.option("--batch", is_flag=True, help="Process all files in input directory")
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Interactive mode - prompt for approach and level",
)
def clean(input_file, approach, level, output_format, output_file, batch, interactive):
    """Clean Telegram chat exports with various strategies

    If INPUT_FILE is not provided, automatically selects from data/input/ directory.
    For multiple files, shows a selection menu.

    Use --interactive flag to be prompted for cleaning approach and level.

    Examples:
        # Interactive mode - select approach and level interactively
        tg-analyzer clean --interactive

        # Interactive mode with specific file
        tg-analyzer clean result.json --interactive

        # Interactive mode with batch processing
        tg-analyzer clean --interactive --batch

        # Interactive mode with custom output format
        tg-analyzer clean --interactive --format markdown

        # Non-interactive with all options specified
        tg-analyzer clean result.json --approach privacy --level 2 --format text"""

    ctx.ensure_initialized()

    # Get defaults from config
    if not approach:
        approach = ctx.config.get("default_cleaning_approach")
    if not level:
        level = ctx.config.get("default_cleaning_level")

    # Interactive mode - prompt for approach and level
    if interactive:
        # Map approaches and levels for numbered selection
        approaches = {1: "privacy", 2: "size", 3: "context"}

        # Approach descriptions
        approach_descriptions = {
            1: "Perfect for sharing conversations while protecting participant privacy",
            2: "Ideal for creating compact files for basic analysis or storage",
            3: "Simple linear format perfect for basic text analysis and keyword searches",
        }

        levels = {1: "basic", 2: "medium", 3: "full"}

        # Level descriptions for each approach
        level_descriptions = {
            "privacy": {
                1: "Names + content only, anonymized user IDs",
                2: "Balances privacy with conversation context for better analysis",
                3: "Complete data preservation for comprehensive analysis while maintaining original structure",
            },
            "size": {
                1: "Text only, minimal metadata",
                2: "Strikes a balance between file size and useful context information",
                3: "Preserves complete conversation richness for detailed analysis",
            },
            "context": {
                1: "Flat chronological message list",
                2: "Maintains conversation flow and context for better understanding of discussions",
                3: "Preserves all interaction patterns for advanced social network analysis",
            },
        }

        # Example outputs for each approach/level combination
        example_outputs = {
            "privacy": {
                1: "User_a1b2c3d4: Hello, how are you?",
                2: "[2023-06-15 14:30] [Reply to User_x7y8z9: Previous message...] User_a1b2c3d4: I'm doing great!",
                3: "[2023-06-15 14:30:45] ID:12345 [Reply to ID:12344] John Doe (user123): I'm doing great! [EDITED] [Reactions: 👍(5), ❤️(2)] [Media: Video (30s)]",
            },
            "size": {
                1: "Hello, how are you?\nI'm doing great!",
                2: "[06/15 14:30] John: Hello, how are you? [Links: https://github.com/repo]\n[06/15 14:35] Mary: I'm doing great!",
                3: "[2023-06-15 14:30] [EDITED] [REPLY] John: Hello, how are you? [🎥 30s] [👍5 ❤️2] [2 links, 1 mention]",
            },
            "context": {
                1: "[2023-06-15 14:30:45] John: Hello, how are you?\n[2023-06-15 14:35:20] Mary: I'm doing great!",
                2: "  [2023-06-15 14:25:00] John: Previous message\n[2023-06-15 14:30:45] Mary: I'm doing great!\n    [2023-06-15 14:31:00] John: Thanks!",
                3: "[2023-06-15 14:30:45] #12345 [EDITED] John: Hello [Reactions: 👍×5, ❤️×2]\n  [2023-06-15 14:35:20] #12346 Mary: I'm doing great! [Reactions: 👍×3]",
            },
        }

        # Get current selections as numbers
        current_approach_num = next(
            (k for k, v in approaches.items() if v == approach), 1
        )
        current_level_num = level

        console.print(
            f"[blue]Current approach:[/blue] {current_approach_num}. {approach}"
        )
        console.print("[blue]Available approaches:[/blue]")
        console.print()
        for num, approach_name in approaches.items():
            marker = "→" if num == current_approach_num else " "
            description = approach_descriptions[num]
            console.print(f"  {num}. {approach_name} {marker}")
            console.print(f"     [dim]{description}[/dim]")
            # Show example output for this approach (using level 2 as representative)
            if approach_name in example_outputs and 2 in example_outputs[approach_name]:
                example = example_outputs[approach_name][2]
                # Format multi-line examples properly
                if "\n" in example:
                    console.print("     [cyan]Example output (level 2):[/cyan]")
                    for line in example.split("\n"):
                        console.print(f"     [dim]│ {line}[/dim]")
                else:
                    console.print(
                        f"     [cyan]Example output (level 2):[/cyan] [dim]│ {example}[/dim]"
                    )
            console.print()  # Add spacing between choices

        while True:
            try:
                approach_input = click.prompt(
                    f"Choose cleaning approach (1-3, default: {current_approach_num})",
                    default=current_approach_num,
                    type=int,
                )
                if approach_input in approaches:
                    approach = approaches[approach_input]
                    break
                else:
                    console.print("[red]Please enter 1, 2, or 3[/red]")
                    console.print(
                        "[dim]Example: Enter 1 for privacy, 2 for size, 3 for context[/dim]"
                    )
            except click.Abort:
                return

        console.print(
            f"[blue]Current level:[/blue] {current_level_num}. {levels[current_level_num]}"
        )
        console.print("[blue]Available levels:[/blue]")
        console.print()
        for num, level_name in levels.items():
            marker = "→" if num == current_level_num else " "
            description = level_descriptions[approach][num]
            console.print(f"  {num}. {level_name} {marker}")
            console.print(f"     [dim]{description}[/dim]")
            # Show example output for this level
            if approach in example_outputs and num in example_outputs[approach]:
                example = example_outputs[approach][num]
                # Format multi-line examples properly
                if "\n" in example:
                    console.print("     [cyan]Example output:[/cyan]")
                    for line in example.split("\n"):
                        console.print(f"     [dim]│ {line}[/dim]")
                else:
                    console.print(
                        f"     [cyan]Example output:[/cyan] [dim]│ {example}[/dim]"
                    )
            console.print()  # Add spacing between choices

        while True:
            try:
                level_input = click.prompt(
                    f"Choose cleaning level (1-3, default: {current_level_num})",
                    default=current_level_num,
                    type=int,
                )
                if level_input in levels:
                    level = level_input
                    break
                else:
                    console.print("[red]Please enter 1, 2, or 3[/red]")
                    console.print(
                        "[dim]Example: Enter 1 for basic, 2 for medium, 3 for full[/dim]"
                    )
            except click.Abort:
                return

    output_format = output_format or "text"

    # Handle input file selection
    if not input_file:
        if batch:
            # Batch mode - process all files
            pass  # Will be handled below
        else:
            # Single file mode - select from input directory
            input_file = select_input_file()
            if not input_file:
                return

    # Auto-rename generic filenames (like result.json) before processing
    input_path = Path(input_file)
    if input_path.name.lower() in ["result.json", "result"]:
        from ..processors.file_renamer import FileRenamer

        renamer = FileRenamer(str(input_path.parent))
        new_filename = renamer.rename_file(input_path.name)
        if new_filename:
            # Update input_file to the new filename
            input_file = str(input_path.parent / new_filename)
            console.print(
                f"[green]✅ Auto-renamed input file to:[/green] {new_filename}"
            )
        else:
            console.print(
                "[dim]File already has a meaningful name, skipping rename[/dim]"
            )

    if batch:
        # Batch processing mode
        console.print("[bold blue]Batch Processing Mode[/bold blue]")
        console.print(f"Approach: {approach}, Level: {level}, Format: {output_format}")

        # Auto-rename generic filenames (like result.json) before batch processing
        from ..processors.file_renamer import FileRenamer

        input_dir = ctx.file_manager.get_input_dir()
        renamer = FileRenamer(str(input_dir))
        renamed_files = renamer.rename_all_files()
        if renamed_files:
            console.print(
                f"[green]✅ Auto-renamed {len(renamed_files)} generic file(s) before processing[/green]"
            )
            for filename in renamed_files:
                console.print(f"  • {filename}")

        processor = BatchProcessor(ctx.analyzer)
        results = processor.process_directory(
            input_dir=ctx.file_manager.get_input_dir(),
            output_dir=ctx.file_manager.get_output_dir(approach, level),
            approach=approach,
            level=level,
            output_format=output_format,
        )

        # Display results
        table = Table(title="Batch Processing Results")
        table.add_column("File", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Output", style="yellow")

        for file_path, output_path in results.items():
            status = "✅ Success" if output_path else "❌ Failed"
            output_name = Path(output_path).name if output_path else "N/A"
            table.add_row(Path(file_path).name, status, output_name)

        console.print(table)

    else:
        # Single file processing
        console.print(f"[bold blue]Cleaning:[/bold blue] {input_file}")
        console.print(f"Approach: {approach}, Level: {level}, Format: {output_format}")

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}")
        ) as progress:
            task = progress.add_task("Processing...", total=1)

            # Clean the file
            cleaned_data = ctx.analyzer.clean(
                input_file=input_file,
                approach=approach,
                level=level,
                output_format=output_format,
            )

            progress.update(task, completed=1)

        # Determine output file
        if not output_file:
            output_file = ctx.file_manager.generate_output_path(
                input_file, approach, level, output_format
            )

        # Save result
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(cleaned_data)

        console.print(f"[green]✅ Cleaned data saved to:[/green] {output_file}")
        console.print(f"[dim]Size: {len(cleaned_data)} characters[/dim]")


@cli.command()
@click.argument("filename", required=False)
@click.option("--all", is_flag=True, help="Rename all JSON files in input directory")
def rename(filename, all):
    """Rename input files to include chat name and date range

    Renames Telegram export files from generic names like 'result.json' to meaningful names
    that include the chat name and date range, e.g., 'ChatName_20230629-20251028.json'

    Examples:
        # Interactive mode - select file from menu if multiple files exist
        tg-analyzer rename

        # Rename specific file
        tg-analyzer rename result.json

        # Rename all JSON files in input directory
        tg-analyzer rename --all

        # Auto-selects if only one file exists
        # (if only one JSON file in input directory, it will be auto-selected)
        tg-analyzer rename
    """
    from ..processors.file_renamer import FileRenamer

    ctx.ensure_initialized()
    input_dir = ctx.file_manager.get_input_dir()
    renamer = FileRenamer(str(input_dir))

    if all:
        console.print("[blue]Renaming all JSON files in input directory...[/blue]")
        renamed_files = renamer.rename_all_files()
        if renamed_files:
            console.print(f"[green]✅ Renamed {len(renamed_files)} files:[/green]")
            for filename in renamed_files:
                console.print(f"  - {filename}")
        else:
            console.print("[yellow]No files to rename[/yellow]")
    else:
        if not filename:
            # Auto-select file if not provided
            json_files = list(input_dir.glob("*.json"))
            if not json_files:
                console.print(f"[red]No JSON files found in {input_dir}[/red]")
                return
            elif len(json_files) == 1:
                filename = json_files[0].name
                console.print(f"[blue]Auto-selected file:[/blue] {filename}")
            else:
                console.print(f"[blue]Found {len(json_files)} JSON files:[/blue]")
                for i, file_path in enumerate(json_files, 1):
                    console.print(f"  {i}. {file_path.name}")
                console.print("[dim]Example: Enter 1 to rename the first file[/dim]")
                while True:
                    try:
                        choice = click.prompt(
                            "Select file to rename (number)", type=int
                        )
                        if 1 <= choice <= len(json_files):
                            filename = json_files[choice - 1].name
                            break
                        else:
                            console.print(
                                f"[red]Please enter a number between 1 and {len(json_files)}[/red]"
                            )
                    except click.Abort:
                        return

        console.print(f"[blue]Renaming file:[/blue] {filename}")
        new_filename = renamer.rename_file(filename)
        if new_filename:
            console.print(f"[green]✅ Successfully renamed to:[/green] {new_filename}")
        else:
            console.print("[red]Failed to rename file[/red]")


@cli.command()
@click.option(
    "--provider",
    type=click.Choice(
        ["openai", "anthropic", "google", "groq", "ollama", "openrouter"]
    ),
    help="LLM provider override (default: openrouter)",
)
@click.option(
    "--model", help="Model override (e.g., openai/gpt-4, anthropic/claude-3-sonnet)"
)
@click.option(
    "--temperature",
    type=float,
    help="Temperature for LLM (0.0-1.0, default: template-specific)",
)
@click.option(
    "--max-tokens",
    type=int,
    help="Maximum tokens for LLM response (default: template-specific)",
)
def analyze(provider, model, temperature, max_tokens):
    """Interactive analysis with template-based scripts

    Select a cleaned chat file and run analysis templates interactively.
    This command is fully interactive and will guide you through:
    1. Selecting a cleaned chat file
    2. Creating an analysis workspace
    3. Choosing analysis templates
    4. Running analyses and saving results

    Examples:
        # Interactive mode - full guided workflow
        tg-analyzer analyze

        # Use specific provider
        tg-analyzer analyze --provider openrouter

        # Use specific model
        tg-analyzer analyze --model anthropic/claude-3-sonnet

        # Control creativity (lower = more focused, higher = more creative)
        tg-analyzer analyze --temperature 0.3

        # Limit response length
        tg-analyzer analyze --max-tokens 2000

        # Combine options for custom analysis
        tg-analyzer analyze --provider openrouter --model openai/gpt-4-turbo --temperature 0.7 --max-tokens 8000

        # Select specific templates during interactive session:
        # When prompted, enter numbers like "1,3,4" or "all" for all templates"""

    ctx.ensure_initialized()

    # Import analysis components
    from ..analysis import TemplateManager, WorkspaceManager, ScriptRunner

    # Initialize analysis components
    template_manager = TemplateManager(ctx.config)
    workspace_manager = WorkspaceManager(ctx.config)
    script_runner = ScriptRunner(ctx.config, ctx.analyzer.llm_manager)

    # Prepare user parameters
    user_params = {}
    if provider:
        user_params["provider"] = provider
    if model:
        user_params["model"] = model
    if temperature is not None:
        user_params["temperature"] = temperature
    if max_tokens is not None:
        user_params["max_tokens"] = max_tokens

    # Step 1: Select cleaned file from output directory
    console.print("[bold blue]Step 1: Select a cleaned chat file[/bold blue]")
    cleaned_file = select_cleaned_file(ctx.file_manager)
    if not cleaned_file:
        return

    # Step 2: Create workspace
    console.print("[bold blue]Step 2: Creating analysis workspace[/bold blue]")
    workspace_info = workspace_manager.create_workspace(cleaned_file)
    console.print(
        f"[green]✅ Workspace created:[/green] {workspace_info['workspace_name']}"
    )

    # Step 3: Select analysis templates
    console.print("[bold blue]Step 3: Select analysis templates[/bold blue]")
    selected_templates = select_analysis_templates(template_manager)
    if not selected_templates:
        return

    # Display current parameters
    if user_params:
        console.print(f"[dim]Using parameters: {user_params}[/dim]")
    else:
        console.print("[dim]Using template defaults[/dim]")

    # Step 4: Load chat data
    console.print("[bold blue]Step 4: Loading chat data[/bold blue]")
    with open(cleaned_file, "r", encoding="utf-8") as f:
        chat_data = f.read()
    console.print(f"[green]✅ Loaded {len(chat_data)} characters[/green]")

    # Step 5: Run analysis scripts
    console.print(
        f"[bold blue]Step 5: Running {len(selected_templates)} analysis scripts[/bold blue]"
    )

    for i, template in enumerate(selected_templates, 1):
        console.print(
            f"\n[bold cyan]Running analysis {i}/{len(selected_templates)}: {template['name']}[/bold cyan]"
        )
        console.print(f"[dim]{template['description']}[/dim]")

        try:
            # Merge template defaults with user parameters
            template_defaults = template_manager.get_template_defaults(template["name"])
            merged_params = template_defaults.copy()
            merged_params.update(user_params)

            # Display parameters for this template
            if merged_params:
                console.print(f"[dim]Template parameters: {merged_params}[/dim]")

            # Run the analysis script
            result = asyncio.run(
                script_runner.run_script(
                    script_path=template["script_path"],
                    chat_data=chat_data,
                    template_name=template["name"],
                    **merged_params,
                )
            )

            # Display result
            console.print("\n[bold green]Analysis Result:[/bold green]")
            console.print("─" * 60)
            console.print(result["result"])
            console.print("─" * 60)

            # Ask if user wants to save
            save_result = click.confirm(
                f"\nSave this {template['name']} analysis result?", default=True
            )

            if save_result:
                result_path = workspace_manager.save_result(
                    workspace_info=workspace_info,
                    template_name=template["name"],
                    result=result["result"],
                    format_type=result["format"],
                )
                console.print(f"[green]✅ Saved to:[/green] {result_path}")

            # Ask if user wants to continue
            if i < len(selected_templates):
                continue_analysis = click.confirm(
                    "\nContinue with next analysis?", default=True
                )
                if not continue_analysis:
                    break

        except Exception as e:
            console.print(f"[red]❌ Analysis failed:[/red] {str(e)}")
            continue_analysis = click.confirm(
                "\nContinue with next analysis?", default=True
            )
            if not continue_analysis:
                break

    console.print("\n[bold green]✅ Analysis session complete![/bold green]")
    console.print(f"[dim]Workspace: {workspace_info['workspace_path']}[/dim]")
    console.print(f"[dim]Results saved in: {workspace_info['results_dir']}[/dim]")


def select_cleaned_file(file_manager):
    """Select a cleaned file from output directory"""
    output_dir = file_manager.get_data_dir() / "output"

    if not output_dir.exists():
        console.print(f"[red]No output directory found: {output_dir}[/red]")
        return None

    # Find all cleaned files in the main output directory
    cleaned_files = []
    for file_path in output_dir.glob("*.txt"):
        if file_path.is_file():
            file_size = file_path.stat().st_size / (1024 * 1024)  # Size in MB
            cleaned_files.append(
                {
                    "path": str(file_path),
                    "name": file_path.name,
                    "size": file_size,
                    "relative_path": file_path.name,
                }
            )

    if not cleaned_files:
        console.print(f"[red]No cleaned files found in {output_dir}[/red]")
        return None

    # Sort by modification time (newest first)
    cleaned_files.sort(key=lambda x: Path(x["path"]).stat().st_mtime, reverse=True)

    console.print(f"[blue]Found {len(cleaned_files)} cleaned files:[/blue]")
    console.print()

    for i, file_info in enumerate(cleaned_files, 1):
        console.print(
            f"{i:2d}. {file_info['relative_path']} ({file_info['size']:.1f} MB)"
        )

    console.print()
    console.print(
        "[dim]Select a cleaned file to run AI analysis and extract insights[/dim]"
    )
    console.print("[dim]Example: Enter 1 to select the first file[/dim]")
    while True:
        try:
            choice = click.prompt("Select a file (number)", type=int)
            if 1 <= choice <= len(cleaned_files):
                selected_file = cleaned_files[choice - 1]
                console.print(
                    f"[green]Selected:[/green] {selected_file['relative_path']}"
                )
                return selected_file["path"]
            else:
                console.print(
                    f"[red]Please enter a number between 1 and {len(cleaned_files)}[/red]"
                )
        except click.Abort:
            return None


def select_analysis_templates(template_manager):
    """Select analysis templates"""
    templates = template_manager.discover_templates()

    if not templates:
        console.print(
            "[red]No analysis templates found. Create some templates first.[/red]"
        )
        return []

    console.print(f"[blue]Found {len(templates)} analysis templates:[/blue]")
    console.print()

    for i, template in enumerate(templates, 1):
        console.print(f"{i:2d}. [cyan]{template['name']}[/cyan]")
        console.print(f"    {template['description']}")
        if template.get("tags"):
            console.print(f"    [dim]Tags: {', '.join(template['tags'])}[/dim]")
        console.print()

    console.print("Options:")
    console.print(
        "  - Enter numbers separated by commas (e.g., 1,3,4) - Select specific analysis templates"
    )
    console.print("     Example: 1,3,4 will run templates 1, 3, and 4")
    console.print(
        "  - Enter 'all' to select all templates - Run comprehensive analysis with all available templates"
    )
    console.print("     Example: all will run all available templates")
    console.print("  - Enter 'none' to cancel - Exit without running analysis")
    console.print()

    while True:
        try:
            choice = click.prompt(
                "Select templates (e.g., 1,3,4 or 'all')", default="all"
            )

            if choice.lower() == "none":
                return []
            elif choice.lower() == "all":
                selected_templates = templates
                break
            else:
                # Parse comma-separated numbers
                indices = [int(x.strip()) for x in choice.split(",")]
                if all(1 <= i <= len(templates) for i in indices):
                    selected_templates = [templates[i - 1] for i in indices]
                    break
                else:
                    console.print(
                        f"[red]Please enter numbers between 1 and {len(templates)}[/red]"
                    )
        except (ValueError, IndexError):
            console.print(
                "[red]Invalid selection. Please enter numbers separated by commas.[/red]"
            )
        except click.Abort:
            return []

    console.print(f"[green]Selected {len(selected_templates)} templates:[/green]")
    for template in selected_templates:
        console.print(f"  • {template['name']}")

    return selected_templates


@cli.command()
@click.argument("input_file", required=False)
@click.option(
    "--provider",
    type=click.Choice(["openai", "google", "ollama"]),
    default=None,
    help="Embedding provider",
)
@click.option("--model", help="Embedding model")
@click.option(
    "--chunk-strategy",
    type=click.Choice(["fixed_size", "sentence", "paragraph", "overlap"]),
    default="overlap",
    help="Text chunking strategy",
)
@click.option("--chunk-size", type=int, help="Text chunk size")
def vectorize(input_file, provider, model, chunk_strategy, chunk_size):
    """Create embeddings and store in vector database

    If INPUT_FILE is not provided, automatically selects from data/input/ directory.
    For multiple files, shows a selection menu."""

    ctx.ensure_initialized()

    # Handle input file selection if not provided
    if not input_file:
        input_file = select_input_file()
        if not input_file:
            return

    # Check if vector database is configured
    if not ctx.config.get("supabase_url") or not ctx.config.get("supabase_key"):
        console.print(
            "[red]Error: Supabase not configured. Please set SUPABASE_URL and SUPABASE_KEY.[/red]"
        )
        console.print("Run 'tg-analyzer config set SUPABASE_URL <url>' to configure.")
        return

    console.print(f"[bold blue]Vectorizing:[/bold blue] {Path(input_file).name}")
    console.print(f"Provider: {provider or 'default'}, Model: {model or 'default'}")
    console.print(f"Chunking: {chunk_strategy}")

    try:
        # Load input data
        with open(input_file, "r", encoding="utf-8") as f:
            text_data = f.read()

        # Create embeddings
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}")
        ) as progress:
            task = progress.add_task("Creating embeddings...", total=1)

            async def run_vectorize():
                return await ctx.analyzer.vectorize(
                    input_data=text_data,
                    provider=provider,
                    model=model,
                    metadata={
                        "source_file": input_file,
                        "chunk_strategy": chunk_strategy,
                        "chunk_size": chunk_size or ctx.config.get("text_chunk_size"),
                    },
                    chunking_strategy=chunk_strategy,
                )

            result = asyncio.run(run_vectorize())
            progress.update(task, completed=1)

        console.print("[green]✅ Vectorization complete![/green]")
        console.print(f"[dim]Created {result.get('chunks_created', 0)} chunks[/dim]")
        console.print(
            f"[dim]Stored {result.get('vectors_stored', 0)} vectors in database[/dim]"
        )
        console.print(
            f"[dim]Processing time: {result.get('processing_time', 0):.2f}s[/dim]"
        )

    except Exception as e:
        console.print(f"[red]Vectorization failed: {e}[/red]")
        raise


@cli.command()
@click.argument("query")
@click.option("--limit", type=int, default=10, help="Maximum results to return")
@click.option(
    "--provider",
    type=click.Choice(["openai", "google", "ollama"]),
    help="Embedding provider for query",
)
def search(query, limit, provider):
    """Search vector database for similar content"""

    ctx.ensure_initialized()

    console.print(f"[bold blue]Searching:[/bold blue] '{query}'")

    try:

        async def run_search():
            return await ctx.analyzer.search_vectors(
                query=query, limit=limit, provider=provider
            )

        results = asyncio.run(run_search())

        if not results:
            console.print("[yellow]No results found.[/yellow]")
            return

        # Display results
        table = Table(title=f"Search Results (limit: {limit})")
        table.add_column("Rank", style="cyan", justify="right")
        table.add_column("Similarity", style="green", justify="right")
        table.add_column("Content Preview", style="white")
        table.add_column("Source", style="yellow")

        for i, result in enumerate(results, 1):
            similarity = result.get("similarity", 0)
            content = (
                result.get("content", "")[:100] + "..."
                if len(result.get("content", "")) > 100
                else result.get("content", "")
            )
            source = result.get("metadata", {}).get("source_file", "Unknown")

            table.add_row(
                str(i),
                f"{similarity:.3f}",
                content,
                Path(source).name if source != "Unknown" else source,
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Search failed: {e}[/red]")
        raise


@cli.group()
def config():
    """Manage configuration and API keys"""
    pass


@config.command("list")
def config_list():
    """List current configuration"""
    ctx.ensure_initialized()

    config_data = ctx.config.get_all()
    validation_issues = ctx.config.validate_config()

    # Create table
    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Status", style="yellow")

    for key, value in config_data.items():
        # Hide sensitive values
        if "key" in key.lower() and "api" in key.lower():
            display_value = "••••••••" if value else "[red]Not set[/red]"
        else:
            display_value = str(value) if value is not None else "[red]Not set[/red]"

        # Check validation status
        status = "✅ OK"
        if key in validation_issues:
            status = f"❌ {validation_issues[key]}"

        table.add_row(key, display_value, status)

    console.print(table)

    if validation_issues:
        console.print("\n[yellow]⚠️  Configuration Issues:[/yellow]")
        for issue in validation_issues.values():
            console.print(f"  • {issue}")


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """Set a configuration value"""
    ctx.ensure_initialized()

    # Handle sensitive values
    if any(word in key.lower() for word in ["key", "secret", "password"]):
        console.print(f"[yellow]Setting sensitive value: {key}[/yellow]")

    ctx.config.set(key, value)
    ctx.config.save_to_env()

    console.print(f"[green]✅ Set {key} = {value}[/green]")


@config.command("get")
@click.argument("key")
def config_get(key):
    """Get a configuration value"""
    ctx.ensure_initialized()

    value = ctx.config.get(key)
    if value is None:
        console.print(f"[red]Configuration key '{key}' not found[/red]")
        return

    # Hide sensitive values in display
    if any(word in key.lower() for word in ["key", "secret", "password"]):
        console.print(f"[yellow]{key} = ••••••••[/yellow]")
    else:
        console.print(f"{key} = {value}")


@cli.command()
@click.option(
    "--input-dir", type=click.Path(exists=True), help="Input directory to watch"
)
@click.option("--interval", type=int, default=5, help="Watch interval in seconds")
def watch(input_dir, interval):
    """Watch input directory and auto-process new files"""

    ctx.ensure_initialized()

    watch_dir = Path(input_dir) if input_dir else ctx.file_manager.get_input_dir()

    console.print(f"[bold blue]Watching directory:[/bold blue] {watch_dir}")
    console.print(f"[dim]Interval: {interval}s - Press Ctrl+C to stop[/dim]")

    try:
        # This would implement file watching
        # For now, just show the concept
        console.print(
            "[yellow]File watching not yet implemented - use batch processing instead[/yellow]"
        )
        console.print("Run: tg-analyzer clean --batch <input_file>")

    except KeyboardInterrupt:
        console.print("\n[blue]Stopped watching.[/blue]")


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", type=int, default=8000, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def web(host, port, reload):
    """Start the web interface"""
    try:
        import uvicorn

        console.print(
            f"[bold blue]Starting web server on http://{host}:{port}[/bold blue]"
        )
        console.print("[dim]Press Ctrl+C to stop[/dim]")

        uvicorn.run(
            "src.tg_analyzer.web.backend.app:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
        )

    except ImportError:
        console.print(
            "[red]Error: uvicorn not installed. Install with: pip install uvicorn[standard][/red]"
        )
        return


@cli.command()
def templates():
    """List available prompt templates"""

    available_templates = list_available_templates()

    console.print("[bold blue]Available Prompt Templates:[/bold blue]")

    for name, description in available_templates.items():
        console.print(f"  [cyan]{name}[/cyan]: {description}")


def main():
    """Entry point for the CLI"""
    cli()


if __name__ == "__main__":
    main()
