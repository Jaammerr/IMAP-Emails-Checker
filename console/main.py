import os
import sys
import time
from datetime import datetime
import inquirer
from inquirer.themes import GreenPassion
from art import text2art
from colorama import Fore, Style
from loader import config
from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text
from rich.align import Align

sys.path.append(os.path.realpath("."))


class Console:
    MODULES = (
        "🔑 Start checker",
        "❌ Exit",
    )

    MODULES_DATA = {
        "🔑 Start checker": "checker",
        "❌ Exit": "exit",
    }

    def __init__(self):
        self.rich_console = RichConsole()
        self.start_time = datetime.now()

    def show_loading_animation(self):
        with self.rich_console.status("[bold green]Loading...", spinner="dots"):
            time.sleep(1.5)

    def show_dev_info(self):
        os.system("cls" if os.name == "nt" else "clear")

        self.show_loading_animation()

        title = text2art("JamBit", font="small")
        styled_title = Text(title, style="bold cyan")

        version = Text("VERSION: 1.0", style="blue")
        telegram = Text("📱 Channel: https://t.me/JamBitPY", style="green")
        github = Text("💻 GitHub: https://github.com/Jaammerr", style="green")

        dev_panel = Panel(
            Text.assemble(styled_title, "\n", version, "\n", telegram, "\n", github),
            border_style="yellow",
            expand=False,
            box=box.ASCII,
            title="Welcome to JamBit",
            subtitle="Powered by Jammer",
        )

        self.rich_console.print(dev_panel)
        print()

    @staticmethod
    def prompt(data: list):
        answers = inquirer.prompt(data, theme=GreenPassion())
        return answers

    def get_module(self):
        questions = [
            inquirer.List(
                "module",
                message=Fore.LIGHTBLACK_EX + "Select the module" + Style.RESET_ALL,
                choices=self.MODULES,
            ),
        ]

        answers = self.prompt(questions)
        return answers.get("module")

    def display_info(self):
        config_table = Table(
            title="Configuration",
            box=box.ASCII,
            show_header=True,
            header_style="bold cyan",
        )

        config_table.add_column("Parameter", style="cyan")
        config_table.add_column("Value", style="magenta")
        config_table.add_column("Status", style="green")

        config_table.add_row(
            "Emails", str(len(config.accounts)), "✓" if config.accounts else "!"
        )
        config_table.add_row(
            "Proxies", str(len(config.proxies)), "✓" if config.proxies else "!"
        )
        config_table.add_row(
            "Threads", str(config.threads), "✓" if config.threads > 0 else "!"
        )
        config_table.add_row(
            "Retry Limit",
            str(config.retry_limit),
            "✓" if config.retry_limit > 0 else "!",
        )
        config_table.add_row(
            "Use Proxy", str(config.use_proxy), "✓" if config.use_proxy else "!"
        )
        config_table.add_row(
            "Use OAuth2", str(config.use_oauth), "✓" if config.use_oauth else "!"
        )

        panel = Panel(
            config_table,
            expand=False,
            border_style="green",
            box=box.ASCII,
            title="System Configuration",
            subtitle="Use arrow keys to navigate",
        )

        self.rich_console.print(panel)

        hint = Text("\n💡 Use arrow keys to navigate, Enter to select", style="dim")
        self.rich_console.print(Align.center(hint))

    def build(self) -> str:
        try:
            self.show_dev_info()
            self.display_info()

            module = self.get_module()
            config.module = self.MODULES_DATA[module]

            if config.module == "exit":
                with self.rich_console.status(
                    "[bold red]Shutting down...", spinner="dots"
                ):
                    time.sleep(1)
                self.rich_console.print("[bold red]Goodbye! 👋[/bold red]")
                exit(0)

            return config.module

        except KeyboardInterrupt:
            self.rich_console.print(
                "\n[bold red]Interrupted by user. Exiting...[/bold red]"
            )
            exit(0)
