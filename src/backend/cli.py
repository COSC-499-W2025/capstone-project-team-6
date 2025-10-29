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
from .consent import ask_for_consent


def handle_first_time_consent(username: str) -> bool:
    """Handle consent for first-time users.

    Args:
        username: The username to handle consent for

    Returns:
        bool: True if consent was given or already exists, False if denied
    """
    from .database import check_user_consent, save_user_consent

    # Check if user has already given consent
    if check_user_consent(username):
        return True

    print("\nFirst-time Login - Consent Required")
    print("--------------------------------------")
    
    if ask_for_consent():
        save_user_consent(username, True)
        return True
    else:
        save_user_consent(username, False)
        return False

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
        bool: True if signup and consent successful, False otherwise
    """
    try:
        create_user(username, password)
        
        print("\nAccount created successfully!")
        print("\nBefore continuing, please review our consent form:")
        
        # Show consent form for new users
        if ask_for_consent():
            from .database import save_user_consent
            save_user_consent(username, True)
            print("\nThank you for providing consent!")
            return True
        else:
            from .database import save_user_consent
            save_user_consent(username, False)
            print("\nYou have not provided consent. Some features will be limited.")
            print("You can update your consent later using 'mda consent --update'")
            return False
            
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
        if info.is_project:
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
    from .database import check_user_consent, save_user_consent
    from .session import get_session
    
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

    # Consent command
    consent_parser = subparsers.add_parser("consent", help="View or update consent status")
    consent_parser.add_argument("--status", action="store_true", help="Check current consent status")
    consent_parser.add_argument("--update", action="store_true", help="Update consent status")
    
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
            # First verify credentials
            if not authenticate_user(args.username, args.password):
                print("\n❌ Invalid username or password")
                return 1
                
            # Handle consent for first-time users
            if not handle_first_time_consent(args.username):
                # User is authenticated but denied consent
                print("\nDenied Consent.")
                print("You can update your consent later using 'mda consent --update'")
                return 1
                
            print(f"\nLogin successful! Welcome {args.username}!")
            return 0
                
        elif args.command == "signup":
            if signup(args.username, args.password):
                print("\n✅ Account created successfully!")
                return 0
            else:
                print("\n❌ Username already exists")
                return 1
                
        elif args.command == "consent":
            session = get_session()
            if not session["logged_in"]:
                print("\nPlease login first")
                return 1

            username = session["username"]
            has_consented = check_user_consent(username)
            
            if args.status:
                print(f"\nConsent Status for {username}:")
                print("Consented" if has_consented else "✗ Not consented")
                return 0
                
            if args.update:
                if has_consented:
                    print("\nYou have already provided consent.")
                    print("To revoke consent, contact support.")
                    return 0
                    
                print("\n📋 Consent Required")
                print("------------------")
                if ask_for_consent():
                    save_user_consent(username, True)
                    print("\nThank you for providing consent!")
                    return 0
                else:
                    save_user_consent(username, False)
                    print("\nYou have not provided consent. Some features will be limited.")
                    return 1
                
        elif args.command == "analyze":
            session = get_session()
            if not session["logged_in"]:
                print("\nPlease login first")
                return 1
                
            username = session["username"]
            if not check_user_consent(username):
                print("\nPlease provide consent before analyzing files")
                print("Run 'mda consent --update' to view and accept the consent form")
                return 1
                
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