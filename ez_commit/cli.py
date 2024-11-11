"""
Command-line interface for ez-commit
"""

import os
import sys
import click
import subprocess
from . import core
from . import config as config_module

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

@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--preview', is_flag=True, help='Preview the commit message without committing')
def main(ctx, preview):
    """Generate commit messages from git diffs using OpenAI."""
    if ctx.invoked_subcommand is None:
        try:
            # Generate commit message
            try:
                message = core.generate_commit_message()
            except ValueError as e:
                click.echo(f"Error: {str(e)}", err=True)
                sys.exit(1)

            # Preview mode
            if preview:
                click.echo("\nGenerated commit message:")
                click.echo("-" * 50)
                click.echo(message)
                click.echo("-" * 50)
                return

            # Confirm the commit message
            click.echo("\nGenerated commit message:")
            click.echo("-" * 50)
            click.echo(message)
            click.echo("-" * 50)
            
            if click.confirm("Do you want to commit with this message?"):
                try:
                    core.commit_changes(message)
                    click.echo("Changes committed successfully!")
                except ValueError as e:
                    click.echo(f"Error: {str(e)}", err=True)
                    sys.exit(1)
            else:
                click.echo("Commit cancelled.")

        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)
            sys.exit(1)

@main.group()
def config():
    """Manage ez-commit configuration."""
    pass

@config.command()
def edit():
    """Open the configuration file in your default editor."""
    config_file = config_module.get_config_file()
    config_module.ensure_config_exists()
    click.echo(f"Opening config file: {config_file}")
    open_editor(str(config_file))

@config.command()
@click.argument('key')
def set_api_key(key):
    """Set the OpenAI API key."""
    cfg = config_module.load_config()
    cfg["openai"]["api_key"] = key
    config_module.save_config(cfg)
    click.echo("API key updated successfully!")

@config.command()
@click.argument('model')
def set_model(model):
    """Set the OpenAI model (e.g., gpt-4, gpt-3.5-turbo)."""
    cfg = config_module.load_config()
    cfg["openai"]["model"] = model
    config_module.save_config(cfg)
    click.echo(f"Model updated to: {model}")

@config.command()
@click.argument('temperature', type=float)
def set_temperature(temperature):
    """Set the temperature (0.0 to 1.0) for response generation."""
    if not 0 <= temperature <= 1:
        click.echo("Temperature must be between 0.0 and 1.0", err=True)
        sys.exit(1)
    
    cfg = config_module.load_config()
    cfg["openai"]["temperature"] = temperature
    config_module.save_config(cfg)
    click.echo(f"Temperature updated to: {temperature}")

@config.command()
def edit_prompt():
    """Edit the system prompt in your default editor."""
    cfg = config_module.load_config()
    current_prompt = cfg["system_prompt"]
    
    click.echo("Opening editor to modify system prompt...")
    new_prompt = open_editor_for_text(current_prompt)
    
    if new_prompt:
        cfg["system_prompt"] = new_prompt
        config_module.save_config(cfg)
        click.echo("System prompt updated successfully!")
    else:
        click.echo("No changes made to system prompt.")

@config.command()
def show():
    """Show current configuration (excluding API key)."""
    cfg = config_module.load_config()
    
    click.echo("\nCurrent Configuration:")
    click.echo("-" * 50)
    click.echo(f"Model: {cfg['openai']['model']}")
    click.echo(f"Temperature: {cfg['openai']['temperature']}")
    click.echo("\nSystem Prompt:")
    click.echo("-" * 50)
    click.echo(cfg['system_prompt'])
    click.echo("-" * 50)

if __name__ == '__main__':
    main()
