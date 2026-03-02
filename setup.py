"""
Setup script for Ziora Data Imports
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

setup(
    name="ziora-imports",
    version="1.0.0",
    description="Multi-tenant data import system for Ziora",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Ziora Team",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "sqlalchemy>=2.0.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
        "openpyxl>=3.1.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "ziora-import=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["config/*.yaml"],
    },
)

