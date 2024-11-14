"""
UI components for ez-commit
"""

import sys
import click

class TerminalUI:
    """Handles terminal display and user interaction."""
    
    def clear_screen(self):
        """Clear the terminal screen and move cursor to top."""
        click.echo('\033[2J\033[H', nl=False)

    def clear_lines(self, n):
        """Clear the last n lines in terminal."""
        for _ in range(n):
            click.echo('\033[A\033[K', nl=False)

    def display_message(self, message, title=None, status=None):
        """Display a message with optional title and status."""
        self.clear_screen()
        if status:
            click.secho(status, fg="blue")
        
        if title:
            click.echo(title)
        click.echo("-" * 50)
        click.echo(message)
        click.echo("-" * 50)

    def display_actions(self):
        """Display available actions."""
        click.echo("\nAvailable Actions:")
        actions = [
            (click.style("(e)dit", fg="green"), "Edit the commit message"),
            (click.style("(c)ancel", fg="red"), "Cancel the commit"),
            (click.style("(i)nteractive", fg="yellow"), "Provide feedback"),
            (click.style("(s)ave", fg="blue"), "Save and commit")
        ]
        for action, description in actions:
            click.echo(f"{action}      - {description}")

    def get_user_choice(self):
        """Get user choice for commit message action."""
        while True:
            click.echo("\nSelect an action: ", nl=False)
            choice = click.getchar().lower()
            if choice in ['e', 'c', 'i', 's']:
                click.echo(choice)  # Echo the choice since getchar doesn't
                return choice
            self.clear_lines(1)
            self._print_error("Invalid choice. Please select (e)dit, (c)ancel, (i)nteractive, or (s)ave")
            self.clear_lines(1)

    def get_user_feedback(self, current_message):
        """Get user feedback for interactive mode."""
        self.clear_screen()
        self.display_message(current_message, "Current commit message")
        
        click.secho("\nEnter your suggested changes:", fg="yellow")
        return click.prompt("", prompt_suffix="\n", type=str)

    def confirm_action(self, message: str) -> bool:
        """Ask user to confirm an action."""
        return click.confirm(f"\n{message}")

    def _print_error(self, message: str):
        """Print error message to stderr with proper formatting."""
        program_name = "ez-commit"
        click.secho(f"{program_name}: error: {message}", fg="red", err=True)

    def display_error(self, message: str):
        """Display an error message to stderr."""
        self._print_error(self._sanitize_error(message))

    def _sanitize_error(self, message: str) -> str:
        """Remove implementation details and format error for user display."""
        # Remove common Python error prefixes
        message = str(message)
        if ": " in message:
            message = message.split(": ")[-1]
        
        # Remove implementation details
        replacements = {
            "ValueError: ": "",
            "Exception: ": "",
            "Error: ": "",
            "Failed to ": "",
            "Unable to ": "",
        }
        for old, new in replacements.items():
            message = message.replace(old, new)
        
        return message.strip()

    def display_success(self, message: str):
        """Display a success message."""
        click.secho(message, fg="green")

    def display_info(self, message: str):
        """Display an info message."""
        click.secho(message, fg="blue")

    def display_warning(self, message: str):
        """Display a warning message to stderr."""
        program_name = "ez-commit"
        click.secho(f"{program_name}: warning: {message}", fg="yellow", err=True)

    def display_config(self, config: dict):
        """Display configuration information."""
        click.secho("\nCurrent Configuration:", fg="blue")
        click.echo("-" * 50)
        
        # Style values separately to match test expectations
        model = click.style(config['openai']['model'], fg='green')
        temp = click.style(str(config['openai']['temperature']), fg='green')
        
        click.echo(f"Model: {model}")
        click.echo(f"Temperature: {temp}")
        click.echo("\nSystem Prompt:")
        click.echo(config['system_prompt'])
        click.echo("-" * 50)
