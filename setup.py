"""
Telegram Chat Analyzer - Open source tool for cleaning and analyzing Telegram chat exports
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README.md
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="telegram-chat-analyzer",
    version="0.1.0",
    author="Pavel Shershnev",
    author_email="pvutrix@gmail.com",
    description="Open source tool for cleaning and analyzing Telegram chat exports",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/telegram-chat-analyzer",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Chat",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.9",
    install_requires=[
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "click>=8.0.0",
        "rich>=13.0.0",
        "typer>=0.9.0",
        "openai>=1.0.0",
        "anthropic>=0.7.0",
        "google-generativeai>=0.3.0",
        "groq>=0.4.0",
        "supabase>=2.0.0",
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.23.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "chardet>=5.0.0",
        "tiktoken>=0.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.5.0",
        ],
        "web": [
            "python-multipart>=0.0.6",
        ],
        "local-llm": [
            "ollama>=0.1.0",
        ],
        "advanced": [
            "watchdog>=3.0.0",
            "psutil>=5.9.0",
            "python-dateutil>=2.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "tg-analyzer=tg_analyzer.cli.main:main",
            "telegram-chat-analyzer=tg_analyzer.cli.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
