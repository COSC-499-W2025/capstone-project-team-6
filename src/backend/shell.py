"""Interactive shell for the MDA CLI."""

import cmd
import shlex
from pathlib import Path
from typing import Optional

from .database import UserAlreadyExistsError, authenticate_user, create_user, initialize
from .traversal import Folder_traversal_fs


class MDAShell(cmd.Cmd):
    intro = """
============================================================
Welcome to Mining Digital Artifacts CLI - Interactive Mode
Type 'help' or '?' to list commands.
Type 'exit' to quit.
============================================================
    """
    prompt = "mda> "
    current_user: Optional[str] = None

    def preloop(self) -> None:
        initialize()

    def do_login(self, arg: str) -> None:
        """Login to your account. Usage: login username password"""
        try:
            username, password = shlex.split(arg)
        except ValueError:
            print("❌ Usage: login username password")
            return

        if authenticate_user(username, password):
            print("\n✅ Login successful!")
            self.current_user = username
            self.prompt = f"mda({username})> "
        else:
            print("\nInvalid username or password")

    def do_signup(self, arg: str) -> None:
        """Create a new account. Usage: signup username password"""
        try:
            username, password = shlex.split(arg)
        except ValueError:
            print("❌ Usage: signup username password")
            return

        try:
            create_user(username, password)
            print("\n✅ Account created successfully!")
        except UserAlreadyExistsError:
            print("\n❌ Username already exists")

    def do_analyze(self, arg: str) -> None:
        """Analyze a folder. Usage: analyze path/to/folder"""
        if not self.current_user:
            print("\nPlease login first")
            return

        if not arg:
            print("Usage: analyze path/to/folder")
            return

        try:
            path = Path(arg)
            if not path.exists():
                print(f"\nPath does not exist: {path}")
                return
            if not path.is_dir():
                print(f"\nPath is not a directory: {path}")
                return

            print(f"\nAnalyzing folder: {path}")
            results = Folder_traversal_fs(path)
            self._display_analysis(results)
        except Exception as e:
            print(f"\nError: {e}")

    def do_analyze_essay(self, arg: str) -> None:
        """Analyze an essay or document. Usage: analyze-essay path/to/document.pdf"""
        if not self.current_user:
            print("\nPlease login first")
            return

        if not arg:
            print("Usage: analyze-essay path/to/document")
            print("Supported formats: .txt, .pdf, .docx, .md")
            return

        try:
            # Lazy import to avoid circular dependency
            from .cli import analyze_essay, display_document_analysis

            path = Path(arg)
            if not path.exists():
                print(f"\nPath does not exist: {path}")
                return

            # Validate file type
            supported_extensions = {".txt", ".pdf", ".docx", ".md"}
            if not path.is_file() or path.suffix.lower() not in supported_extensions:
                print(f"\nFile must be one of: {', '.join(supported_extensions)}")
                return

            print(f"\nAnalyzing document: {path}")
            analysis = analyze_essay(path)
            display_document_analysis(analysis)
            print("\nDocument analysis complete!")
        except ValueError as e:
            print(f"\n{e}")
        except Exception as e:
            print(f"\nDocument analysis failed: {e}")
            import traceback

            traceback.print_exc()

    def do_logout(self, _: str) -> None:
        """Logout from current session."""
        if self.current_user:
            from .session import clear_session

            clear_session()
            print(f"\nGoodbye, {self.current_user}!")
            self.current_user = None
            self.prompt = "mda> "
        else:
            print("\n❌ Not logged in")

    def do_exit(self, _: str) -> bool:
        """Exit the application."""
        if self.current_user:
            print(f"\n👋 Goodbye, {self.current_user}!")
        else:
            print("\n👋 Goodbye!")
        return True

    def do_EOF(self, _: str) -> bool:
        """Handle Ctrl+D gracefully."""
        print()  # Add newline
        return self.do_exit("")

    def _display_analysis(self, results: dict) -> None:
        """Display folder analysis results."""
        print("\nAnalysis Results:")
        print("-" * 60)

        projects = []
        non_projects = []

        for directory, info in results.items():
            if info["project"]:
                projects.append(directory)
            else:
                non_projects.append(directory)

        print(f"\nFound {len(projects)} projects:")
        for proj in projects:
            print(f"   • {proj}")

        if non_projects:
            print(f"\nNon-project folders ({len(non_projects)}):")
            for folder in non_projects:
                print(f"   • {folder}")

    def default(self, line: str) -> None:
        """Handle unknown commands."""
        print(f"❌ Unknown command: {line}")
        print("Type 'help' or '?' to see available commands")
