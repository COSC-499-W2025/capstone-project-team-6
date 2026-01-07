from setuptools import setup, find_packages

setup(
    name="mda-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "bcrypt",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "mda=src.backend.cli:main",
        ],
    },
    python_requires=">=3.9",
)