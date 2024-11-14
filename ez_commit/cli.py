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
    click.echo("\nAvailable Actions:")
    click.echo(click.style("(e)dit", fg="green") + "      - Edit the commit message")
    click.echo(click.style("(c)ancel", fg="red") + "    - Cancel the commit")
    click.echo(click.style("(i)nteractive", fg="yellow") + " - Provide feedback")
    click.echo(click.style("(s)ave", fg="blue") + "      - Save and commit")
    
    while True:
        click.echo("\nSelect an action: ", nl=False)
        choice = click.getchar().lower()
        if choice in ['e', 'c', 'i', 's']:
            click.echo(choice)  # Echo the choice since getchar doesn't
            return choice
        click.secho("\nInvalid choice. Please select (e)dit, (c)ancel, (i)nteractive, or (s)ave", fg="red")

def handle_interactive_mode(current_message, diff):
    """Handle interactive mode where user provides feedback."""
    click.echo("\nCurrent commit message:")
    click.echo("-" * 50)
    click.echo(current_message)
    click.echo("-" * 50)
    
    click.secho("\nEnter your suggested changes:", fg="yellow")
    feedback = click.prompt("", prompt_suffix="\n", type=str)
    
    if not feedback.strip():
        click.secho("No feedback provided.", fg="yellow")
        return current_message
    
    click.secho("\nGenerating improved message...", fg="blue")
    
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
                click.secho("Getting git diff...", fg="blue")
                diff = core.get_git_diff()
            except ValueError as e:
                click.secho(f"Error: {str(e)}", fg="red", err=True)
                sys.exit(1)

            # Generate initial commit message
            try:
                click.secho("Generating commit message...", fg="blue")
                message = core.generate_commit_message(diff)
            except ValueError as e:
                click.secho(f"Error: {str(e)}", fg="red", err=True)
                sys.exit(1)

            while True:
                # Preview mode or show the generated message
                click.echo("\nGenerated Commit Message:")
                click.echo("-" * 50)
                click.echo(message)
                click.echo("-" * 50)

                if preview:
                    return

                # Get user choice
                choice = get_user_choice()

                if choice == 'c':
                    click.secho("\nCommit cancelled.", fg="red")
                    return
                elif choice == 'e':
                    click.secho("\nOpening editor...", fg="blue")
                    edited_message = open_editor_for_text(message)
                    if edited_message:
                        message = edited_message
                        continue
                elif choice == 'i':
                    message = handle_interactive_mode(message, diff)
                    continue
                elif choice == 's':
                    try:
                        click.secho("\nCommitting changes...", fg="blue")
                        core.commit_changes(message)
                        click.secho("Changes committed successfully!", fg="green")
                        return
                    except ValueError as e:
                        click.secho(f"Error: {str(e)}", fg="red", err=True)
                        sys.exit(1)

        except Exception as e:
            click.secho(f"Error: {str(e)}", fg="red", err=True)
            sys.exit(1)

@main.command()
def version():
    """Display the current version of ez-commit."""
    click.secho(f"ez-commit version {__version__}", fg="blue")

@main.group()
def config():
    """Manage ez-commit configuration."""
    pass

@config.command()
def edit():
    """Open the configuration file in your default editor."""
    config_file = config_module.get_config_file()
    config_module.ensure_config_exists()
    click.secho(f"Opening config file: {config_file}", fg="blue")
    open_editor(str(config_file))

@config.command()
@click.argument('key')
def set_api_key(key):
    """Set the OpenAI API key."""
    cfg = config_module.load_config()
    cfg["openai"]["api_key"] = key
    config_module.save_config(cfg)
    click.secho("API key updated successfully!", fg="green")

@config.command()
@click.argument('model')
def set_model(model):
    """Set the OpenAI model (e.g., gpt-4, gpt-3.5-turbo)."""
    cfg = config_module.load_config()
    cfg["openai"]["model"] = model
    config_module.save_config(cfg)
    click.secho(f"Model updated to: {model}", fg="green")

@config.command()
@click.argument('temperature', type=float)
def set_temperature(temperature):
    """Set the temperature (0.0 to 1.0) for response generation."""
    if not 0 <= temperature <= 1:
        click.secho("Temperature must be between 0.0 and 1.0", fg="red", err=True)
        sys.exit(1)
    
    cfg = config_module.load_config()
    cfg["openai"]["temperature"] = temperature
    config_module.save_config(cfg)
    click.secho(f"Temperature updated to: {temperature}", fg="green")

@config.command()
def edit_prompt():
    """Edit the system prompt in your default editor."""
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

@config.command()
def show():
    """Show current configuration (excluding API key)."""
    cfg = config_module.load_config()
    
    click.secho("\nCurrent Configuration:", fg="blue")
    click.echo("-" * 50)
    click.echo(f"Model: {click.style(cfg['openai']['model'], fg='green')}")
    click.echo(f"Temperature: {click.style(str(cfg['openai']['temperature']), fg='green')}")
    click.echo("\nSystem Prompt:")
    click.echo(cfg['system_prompt'])
    click.echo("-" * 50)

if __name__ == '__main__':
    main()
