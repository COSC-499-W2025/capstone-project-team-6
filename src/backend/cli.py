#!/usr/bin/env python3

from __future__ import annotations

import sys
import argparse
from pathlib import Path
from typing import Optional

from . import (
    Folder_traversal,
    initialize,
    create_user,
    authenticate_user,
    UserAlreadyExistsError,
    MDAShell
)


def login(username: str, password: str) -> bool:
    """Attempt to login with the given credentials.

    Args:
        username: The username to login with
        password: The password to login with

    Returns:
        bool: True if login successful, False otherwise
    """
    return authenticate_user(username, password)


def signup(username: str, password: str) -> bool:
    """Register a new user.

    Args:
        username: The username to register
        password: The password to use

    Returns:
        bool: True if signup successful, False otherwise
    """
    try:
        create_user(username, password)
        return True
    except UserAlreadyExistsError:
        return False


def analyze_folder(path: Path) -> dict:
    """Analyze a folder and identify projects.
    
    Args:
        path: Path to the folder to analyze
        
    Returns:
        dict: Analysis results containing project information
    """
    return Folder_traversal(path)


def display_analysis(results: dict) -> None:
    """Display folder analysis results.
    
    Args:
        results: Analysis results from folder traversal
    """
    print("\n📊 Analysis Results:")
    print("-" * 60)
    
    projects = []
    non_projects = []
    
    for directory, info in results.items():
        if info["project"]:
            projects.append(directory)
        else:
            non_projects.append(directory)
    
    print(f"\n🗂️  Found {len(projects)} projects:")
    for proj in projects:
        print(f"   • {proj}")
        
    if non_projects:
        print(f"\n📁 Non-project folders ({len(non_projects)}):")
        for folder in non_projects:
            print(f"   • {folder}")


def main() -> int:
    """Main CLI entry point.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    from .shell import MDAShell
    
    parser = argparse.ArgumentParser(description="Mining Digital Artifacts CLI")
    parser.add_argument("--interactive", "-i", action="store_true", help="Start in interactive mode")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Login command
    login_parser = subparsers.add_parser("login", help="Login to your account")
    login_parser.add_argument("username", help="Your username")
    login_parser.add_argument("password", help="Your password")
    
    # Signup command
    signup_parser = subparsers.add_parser("signup", help="Create a new account")
    signup_parser.add_argument("username", help="Choose a username")
    signup_parser.add_argument("password", help="Choose a password")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a folder")
    analyze_parser.add_argument("path", help="Path to the folder to analyze")
    
    args = parser.parse_args()
    
    try:
        initialize()
        
        # Interactive mode
        if args.interactive or not args.command:
            shell = MDAShell()
            shell.cmdloop()
            return 0
            
        # Session management
        session = {"logged_in": False, "username": None}
        
        # Command line mode
        if args.command == "login":
            if login(args.username, args.password):
                print(f"\n✅ Login successful! Welcome {args.username}!")
                return 0
            else:
                print("\n❌ Invalid username or password")
                return 1
                
        elif args.command == "signup":
            if signup(args.username, args.password):
                print("\n✅ Account created successfully!")
                return 0
            else:
                print("\n❌ Username already exists")
                return 1
                
        elif args.command == "analyze":
            # Session check is now handled in Folder_traversal
                
            path = Path(args.path)
            if not path.exists():
                print(f"\n❌ Path does not exist: {path}")
                return 1
            if not path.is_dir():
                print(f"\n❌ Path is not a directory: {path}")
                return 1
                
            print(f"\n📂 Analyzing folder: {path}")
            results = analyze_folder(path)
            display_analysis(results)
            return 0
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Exiting.")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())