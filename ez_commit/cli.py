"""
Command-line interface for ez-commit
"""

import sys
import click
from click.exceptions import Exit
from . import core
from . import config as config_module
from . import __version__
from .ui import TerminalUI
from .commands import EditorHandler, CommitHandler, ConfigHandler

# Exit codes
EXIT_SUCCESS = 0
EXIT_CANCELLED = 1
EXIT_GIT_ERROR = 2
EXIT_API_ERROR = 3
EXIT_CONFIG_ERROR = 4
EXIT_UNKNOWN_ERROR = 5

def handle_error(error: str, code: int, ui: TerminalUI) -> int:
    """Handle error display and return appropriate exit code."""
    ui.display_error(error)
    raise Exit(code)

def create_handlers():
    """Create and return handlers with dependencies."""
    ui = TerminalUI()
    editor = EditorHandler()
    commit_handler = CommitHandler(ui, core, editor)
    config_handler = ConfigHandler(config_module, editor)
    return ui, commit_handler, config_handler

@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--preview', is_flag=True, help='Preview the commit message without committing')
def main(ctx, preview):
    """Generate commit messages from git diffs using OpenAI."""
    if ctx.invoked_subcommand is None:
        ui, commit_handler, _ = create_handlers()
        
        # Initialize commit process
        success, error = commit_handler.initialize()
        if not success:
            if "OpenAI API error" in error:
                return handle_error(error, EXIT_API_ERROR, ui)
            if "git" in error.lower():
                return handle_error(error, EXIT_GIT_ERROR, ui)
            return handle_error(error, EXIT_UNKNOWN_ERROR, ui)

        while True:
            # Display interface
            ui.display_message(commit_handler.current_message, "Generated Commit Message")
            if preview:
                raise Exit(EXIT_SUCCESS)

            ui.display_actions()
            choice = ui.get_user_choice()

            if choice == 'c':
                ui.display_info("\nCommit cancelled.")
                raise Exit(EXIT_CANCELLED)
            
            elif choice == 'e':
                ui.display_info("\nOpening editor...")
                commit_handler.handle_edit()
                continue
            
            elif choice == 'i':
                success, error = commit_handler.handle_interactive()
                if not success:
                    if "OpenAI API error" in error:
                        return handle_error(error, EXIT_API_ERROR, ui)
                    return handle_error(error, EXIT_UNKNOWN_ERROR, ui)
                continue
            
            elif choice == 's':
                ui.display_info("\nCommitting changes...")
                success, error = commit_handler.handle_save()
                if success:
                    ui.display_success("Changes committed successfully!")
                    raise Exit(EXIT_SUCCESS)
                return handle_error(error, EXIT_GIT_ERROR, ui)

@main.command()
def version():
    """Display the current version of ez-commit."""
    ui = TerminalUI()
    ui.display_info(f"ez-commit version {__version__}")
    raise Exit(EXIT_SUCCESS)

@main.group()
def config():
    """Manage ez-commit configuration."""
    pass

@config.command()
def edit():
    """Open the configuration file in your default editor."""
    ui, _, config_handler = create_handlers()
    success, error = config_handler.edit_config()
    if not success:
        return handle_error(error, EXIT_CONFIG_ERROR, ui)
    raise Exit(EXIT_SUCCESS)

@config.command()
def reset():
    """Reset configuration to default values."""
    ui, _, config_handler = create_handlers()
    success, error = config_handler.reset_config(ui)
    if not success:
        return handle_error(error, EXIT_CONFIG_ERROR, ui)
    raise Exit(EXIT_SUCCESS)

@config.command()
@click.argument('key')
def set_api_key(key):
    """Set the OpenAI API key."""
    ui, _, config_handler = create_handlers()
    success, error = config_handler.set_api_key(key)
    if not success:
        return handle_error(error, EXIT_CONFIG_ERROR, ui)
    ui.display_success("API key updated successfully!")
    raise Exit(EXIT_SUCCESS)

@config.command()
@click.argument('model')
def set_model(model):
    """Set the OpenAI model (e.g., gpt-4, gpt-3.5-turbo)."""
    ui, _, config_handler = create_handlers()
    success, error = config_handler.set_model(model)
    if not success:
        return handle_error(error, EXIT_CONFIG_ERROR, ui)
    ui.display_success(f"Model updated to: {model}")
    raise Exit(EXIT_SUCCESS)

@config.command()
@click.argument('temperature', type=float)
def set_temperature(temperature):
    """Set the temperature (0.0 to 1.0) for response generation."""
    ui, _, config_handler = create_handlers()
    success, error = config_handler.set_temperature(temperature)
    if not success:
        return handle_error(error, EXIT_CONFIG_ERROR, ui)
    ui.display_success(f"Temperature updated to: {temperature}")
    raise Exit(EXIT_SUCCESS)

@config.command()
def edit_prompt():
    """Edit the system prompt in your default editor."""
    ui, _, config_handler = create_handlers()
    success, error = config_handler.edit_prompt()
    if not success:
        return handle_error(error, EXIT_CONFIG_ERROR, ui)
    ui.display_success("System prompt updated successfully!")
    raise Exit(EXIT_SUCCESS)

@config.command()
def show():
    """Show current configuration (excluding API key)."""
    ui, _, config_handler = create_handlers()
    config, error = config_handler.show_config()
    if error:
        return handle_error(error, EXIT_CONFIG_ERROR, ui)
    ui.display_config(config)
    raise Exit(EXIT_SUCCESS)

if __name__ == '__main__':
    sys.exit(main())
