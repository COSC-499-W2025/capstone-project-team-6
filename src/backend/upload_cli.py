#!/usr/bin/env python3
"""
Command-line tool for uploading files to the FastAPI backend.

Usage:
    python upload_cli.py /path/to/file.txt
    python upload_cli.py /path/to/file1.txt /path/to/file2.pdf
"""

import click
import httpx
from pathlib import Path
from typing import List
import sys


DEFAULT_API_URL = "http://localhost:8000"


@click.group()
def cli():
    """File upload CLI tool for FastAPI backend"""
    pass


@cli.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--url', default=DEFAULT_API_URL, help='Backend API URL')
@click.option('--endpoint', default='/api/upload', help='Upload endpoint')
def upload(files: tuple, url: str, endpoint: str):
    """
    Upload one or more files to the backend server.

    FILES: Path(s) to file(s) to upload
    """
    if not files:
        click.echo("Error: No files specified", err=True)
        sys.exit(1)

    # Convert to list of Path objects
    file_paths = [Path(f) for f in files]

    # Validate all files exist
    for file_path in file_paths:
        if not file_path.exists():
            click.echo(f"Error: File not found: {file_path}", err=True)
            sys.exit(1)
        if not file_path.is_file():
            click.echo(f"Error: Not a file: {file_path}", err=True)
            sys.exit(1)

    # Upload files
    if len(file_paths) == 1:
        upload_single_file(file_paths[0], url, endpoint)
    else:
        upload_multiple_files(file_paths, url)


def upload_single_file(file_path: Path, url: str, endpoint: str):
    """Upload a single file"""
    click.echo(f"\nUploading: {file_path.name}")
    click.echo(f"Size: {file_path.stat().st_size / 1024:.2f} KB")

    try:
        with httpx.Client(timeout=30.0) as client:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'application/octet-stream')}
                response = client.post(f"{url}{endpoint}", files=files)

            if response.status_code == 200:
                data = response.json()
                click.echo(click.style("\n✓ Upload successful!", fg='green', bold=True))
                click.echo(f"  Original: {data['original_filename']}")
                click.echo(f"  Saved as: {data['filename']}")
                click.echo(f"  Size: {data['size_mb']} MB")
                click.echo(f"  Path: {data['path']}")
            else:
                error_detail = response.json().get('detail', 'Unknown error')
                click.echo(click.style(f"\n✗ Upload failed: {error_detail}", fg='red', bold=True))
                sys.exit(1)

    except httpx.ConnectError:
        click.echo(click.style(f"\n✗ Error: Could not connect to {url}", fg='red', bold=True))
        click.echo("Make sure the backend server is running:")
        click.echo("  cd src/backend")
        click.echo("  uvicorn main:app --reload")
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"\n✗ Error: {str(e)}", fg='red', bold=True))
        sys.exit(1)


def upload_multiple_files(file_paths: List[Path], url: str):
    """Upload multiple files"""
    click.echo(f"\nUploading {len(file_paths)} files...")

    try:
        with httpx.Client(timeout=60.0) as client:
            files = []
            for file_path in file_paths:
                f = open(file_path, 'rb')
                files.append(('files', (file_path.name, f, 'application/octet-stream')))

            try:
                response = client.post(f"{url}/api/upload/multiple", files=files)
            finally:
                # Close all file handles
                for _, (_, f, _) in files:
                    f.close()

            if response.status_code == 200:
                data = response.json()
                click.echo(click.style(f"\n✓ Upload completed!", fg='green', bold=True))
                click.echo(f"  Total: {data['total']}")
                click.echo(f"  Successful: {data['successful']}")
                click.echo(f"  Failed: {data['failed']}")

                click.echo("\nResults:")
                for result in data['results']:
                    if result['status'] == 'success':
                        click.echo(click.style(f"  ✓ {result['original_filename']}", fg='green'))
                        click.echo(f"    Saved as: {result['filename']} ({result['size_mb']} MB)")
                    else:
                        click.echo(click.style(f"  ✗ {result['filename']}: {result['message']}", fg='red'))

                if data['failed'] > 0:
                    sys.exit(1)
            else:
                error_detail = response.json().get('detail', 'Unknown error')
                click.echo(click.style(f"\n✗ Upload failed: {error_detail}", fg='red', bold=True))
                sys.exit(1)

    except httpx.ConnectError:
        click.echo(click.style(f"\n✗ Error: Could not connect to {url}", fg='red', bold=True))
        click.echo("Make sure the backend server is running:")
        click.echo("  cd src/backend")
        click.echo("  uvicorn main:app --reload")
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"\n✗ Error: {str(e)}", fg='red', bold=True))
        sys.exit(1)


@cli.command()
@click.option('--url', default=DEFAULT_API_URL, help='Backend API URL')
def health(url: str):
    """Check if the backend server is running"""
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{url}/api/health")
            if response.status_code == 200:
                click.echo(click.style(f"✓ Backend is healthy at {url}", fg='green', bold=True))
            else:
                click.echo(click.style(f"✗ Backend returned status {response.status_code}", fg='red'))
                sys.exit(1)
    except httpx.ConnectError:
        click.echo(click.style(f"✗ Could not connect to {url}", fg='red', bold=True))
        click.echo("Make sure the backend server is running:")
        click.echo("  cd src/backend")
        click.echo("  uvicorn main:app --reload")
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"✗ Error: {str(e)}", fg='red', bold=True))
        sys.exit(1)


if __name__ == '__main__':
    cli()
