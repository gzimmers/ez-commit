"""
Command-line interface for ez-commit
"""

import os
import sys
import click
import subprocess
from . import core
from . import config as config_module
from . import __version__

# Exit codes
EXIT_SUCCESS = 0
EXIT_CANCELLED = 1
EXIT_GIT_ERROR = 2
EXIT_API_ERROR = 3
EXIT_CONFIG_ERROR = 4
EXIT_UNKNOWN_ERROR = 5

def clear_screen():
    """Clear the terminal screen and move cursor to top."""
    click.echo('\033[2J\033[H', nl=False)

def clear_lines(n):
    """Clear the last n lines in terminal."""
    for _ in range(n):
        click.echo('\033[A\033[K', nl=False)

def display_interface(message, status_message=None):
    """Display the commit message and options interface."""
    clear_screen()
    if status_message:
        click.secho(status_message, fg="blue")
        click.echo()
    
    click.echo("Generated Commit Message:")
    click.echo("-" * 50)
    click.echo(message)
    click.echo("-" * 50)
    
    click.echo("\nAvailable Actions:")
    click.echo(click.style("(e)dit", fg="green") + "      - Edit the commit message")
    click.echo(click.style("(c)ancel", fg="red") + "    - Cancel the commit")
    click.echo(click.style("(i)nteractive", fg="yellow") + " - Provide feedback")
    click.echo(click.style("(s)ave", fg="blue") + "      - Save and commit")

def open_editor(filename):
    """Open the config file in the default editor."""
    if sys.platform.startswith('win'):
        subprocess.run(['notepad', filename])
    else:
        editor = os.environ.get('EDITOR', 'vim')
        subprocess.run([editor, filename])

def open_editor_for_text(initial_text=""):
    """Open a temporary file in the editor and return the edited content."""
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as tf:
        tf.write(initial_text)
        tf.flush()
        filename = tf.name
    
    open_editor(filename)
    
    with open(filename, 'r') as f:
        content = f.read()
    
    os.unlink(filename)
    return content.strip()

def get_user_choice():
    """Get user choice for commit message action."""
    while True:
        click.echo("\nSelect an action: ", nl=False)
        choice = click.getchar().lower()
        if choice in ['e', 'c', 'i', 's']:
            click.echo(choice)  # Echo the choice since getchar doesn't
            return choice
        clear_lines(1)
        click.secho("Invalid choice. Please select (e)dit, (c)ancel, (i)nteractive, or (s)ave", fg="red")
        clear_lines(1)

def handle_interactive_mode(current_message, diff):
    """Handle interactive mode where user provides feedback."""
    clear_screen()
    click.echo("Current commit message:")
    click.echo("-" * 50)
    click.echo(current_message)
    click.echo("-" * 50)
    
    click.secho("\nEnter your suggested changes:", fg="yellow")
    feedback = click.prompt("", prompt_suffix="\n", type=str)
    
    if not feedback.strip():
        return current_message
    
    click.secho("Generating improved message...", fg="blue")
    
    # Create messages history with the current message and user's feedback
    additional_messages = [
        {"role": "assistant", "content": current_message},
        {"role": "user", "content": f"Suggested changes: {feedback}"}
    ]
    
    # Generate new message with the feedback
    return core.generate_commit_message(diff, additional_messages)

@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--preview', is_flag=True, help='Preview the commit message without committing')
def main(ctx, preview):
    """Generate commit messages from git diffs using OpenAI."""
    if ctx.invoked_subcommand is None:
        try:
            # Get the diff first so we can reuse it
            try:
                diff = core.get_git_diff()
            except ValueError as e:
                click.secho(f"Error: {str(e)}", fg="red", err=True)
                sys.exit(EXIT_GIT_ERROR)

            # Generate initial commit message
            try:
                message = core.generate_commit_message(diff)
            except ValueError as e:
                if "OpenAI API error" in str(e):
                    click.secho(f"Error: {str(e)}", fg="red", err=True)
                    sys.exit(EXIT_API_ERROR)
                click.secho(f"Error: {str(e)}", fg="red", err=True)
                sys.exit(EXIT_UNKNOWN_ERROR)

            while True:
                display_interface(message)

                if preview:
                    return EXIT_SUCCESS

                # Get user choice
                choice = get_user_choice()

                if choice == 'c':
                    click.secho("\nCommit cancelled.", fg="red")
                    sys.exit(EXIT_CANCELLED)
                elif choice == 'e':
                    edited_message = open_editor_for_text(message)
                    if edited_message:
                        message = edited_message
                        continue
                elif choice == 'i':
                    try:
                        message = handle_interactive_mode(message, diff)
                    except ValueError as e:
                        if "OpenAI API error" in str(e):
                            click.secho(f"Error: {str(e)}", fg="red", err=True)
                            sys.exit(EXIT_API_ERROR)
                        click.secho(f"Error: {str(e)}", fg="red", err=True)
                        sys.exit(EXIT_UNKNOWN_ERROR)
                    continue
                elif choice == 's':
                    try:
                        clear_screen()
                        click.secho("Committing changes...", fg="blue")
                        core.commit_changes(message)
                        click.secho("Changes committed successfully!", fg="green")
                        return EXIT_SUCCESS
                    except ValueError as e:
                        click.secho(f"Error: {str(e)}", fg="red", err=True)
                        sys.exit(EXIT_GIT_ERROR)

        except Exception as e:
            click.secho(f"Error: {str(e)}", fg="red", err=True)
            sys.exit(EXIT_UNKNOWN_ERROR)

@main.command()
def version():
    """Display the current version of ez-commit."""
    click.secho(f"ez-commit version {__version__}", fg="blue")
    return EXIT_SUCCESS

@main.group()
def config():
    """Manage ez-commit configuration."""
    pass

@config.command()
def edit():
    """Open the configuration file in your default editor."""
    try:
        config_file = config_module.get_config_file()
        config_module.ensure_config_exists()
        click.secho(f"Opening config file: {config_file}", fg="blue")
        open_editor(str(config_file))
        return EXIT_SUCCESS
    except Exception as e:
        click.secho(f"Error: {str(e)}", fg="red", err=True)
        sys.exit(EXIT_CONFIG_ERROR)

@config.command()
@click.argument('key')
def set_api_key(key):
    """Set the OpenAI API key."""
    try:
        cfg = config_module.load_config()
        cfg["openai"]["api_key"] = key
        config_module.save_config(cfg)
        click.secho("API key updated successfully!", fg="green")
        return EXIT_SUCCESS
    except Exception as e:
        click.secho(f"Error: {str(e)}", fg="red", err=True)
        sys.exit(EXIT_CONFIG_ERROR)

@config.command()
@click.argument('model')
def set_model(model):
    """Set the OpenAI model (e.g., gpt-4, gpt-3.5-turbo)."""
    try:
        cfg = config_module.load_config()
        cfg["openai"]["model"] = model
        config_module.save_config(cfg)
        click.secho(f"Model updated to: {model}", fg="green")
        return EXIT_SUCCESS
    except Exception as e:
        click.secho(f"Error: {str(e)}", fg="red", err=True)
        sys.exit(EXIT_CONFIG_ERROR)

@config.command()
@click.argument('temperature', type=float)
def set_temperature(temperature):
    """Set the temperature (0.0 to 1.0) for response generation."""
    try:
        if not 0 <= temperature <= 1:
            click.secho("Temperature must be between 0.0 and 1.0", fg="red", err=True)
            sys.exit(EXIT_CONFIG_ERROR)
        
        cfg = config_module.load_config()
        cfg["openai"]["temperature"] = temperature
        config_module.save_config(cfg)
        click.secho(f"Temperature updated to: {temperature}", fg="green")
        return EXIT_SUCCESS
    except Exception as e:
        click.secho(f"Error: {str(e)}", fg="red", err=True)
        sys.exit(EXIT_CONFIG_ERROR)

@config.command()
def edit_prompt():
    """Edit the system prompt in your default editor."""
    try:
        cfg = config_module.load_config()
        current_prompt = cfg["system_prompt"]
        
        click.secho("Opening editor to modify system prompt...", fg="blue")
        new_prompt = open_editor_for_text(current_prompt)
        
        if new_prompt:
            cfg["system_prompt"] = new_prompt
            config_module.save_config(cfg)
            click.secho("System prompt updated successfully!", fg="green")
        else:
            click.secho("No changes made to system prompt.", fg="yellow")
        return EXIT_SUCCESS
    except Exception as e:
        click.secho(f"Error: {str(e)}", fg="red", err=True)
        sys.exit(EXIT_CONFIG_ERROR)

@config.command()
def show():
    """Show current configuration (excluding API key)."""
    try:
        cfg = config_module.load_config()
        
        click.secho("\nCurrent Configuration:", fg="blue")
        click.echo("-" * 50)
        click.echo(f"Model: {click.style(cfg['openai']['model'], fg='green')}")
        click.echo(f"Temperature: {click.style(str(cfg['openai']['temperature']), fg='green')}")
        click.echo("\nSystem Prompt:")
        click.echo(cfg['system_prompt'])
        click.echo("-" * 50)
        return EXIT_SUCCESS
    except Exception as e:
        click.secho(f"Error: {str(e)}", fg="red", err=True)
        sys.exit(EXIT_CONFIG_ERROR)

if __name__ == '__main__':
    sys.exit(main())
