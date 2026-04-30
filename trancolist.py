# Copyright 2026 The University of Utah
# SPDX-License-Identifier: MIT

from pathlib import Path
from tap import Tap, Positional
from tranco import Tranco

from credentials import load_credentials

DEFAULT_CONFIG_JSON = Path("default.json")

class ArgParser(Tap):
    list_id: str | None = None
    """
    The list ID of an existing or pending list to get. Mutually exclusive with
    --config.
    """
    config: Path | None = DEFAULT_CONFIG_JSON
    """
    The path to a json file that configures a new Tranco list. The json file
    should follow the schema at
    https://tranco-list.eu/api_documentation#datatypes-configuration. Mutually
    exclusive with --list-id.
    """
    creds: Path | None = Path("credentials.json")
    """
    The path to a json file with values for the keys "email" and "api_key".
    Environment variables `TRANCO_EMAIL` and `TRANCO_API_KEY` take precedence,
    so this option will be ignored if both are specified.
    """
    blocklists: set[Path] | None = {Path('adult-blocklist.txt')}
    """
    A list of files. Each file is a list of domains to exclude from the
    final list, one on each line.
    """
    top_n: int | None = 200
    """The number of domains to include"""
    force: bool = False
    """Overwrite `out_dir` if it already exists"""
    out_dir: Positional[Path]
    """The directory to write the list and metadata into"""

    def configure(self):
        self.add_argument('-b', '--blocklists')
        self.add_argument('-t', '--top-n')
        self.add_argument('-f', '--force')


def main():
    args = ArgParser(underscores_to_dashes=True).parse_args()
    if args.list_id and args.config == DEFAULT_CONFIG_JSON:
        args.config = None


if __name__ == "__main__":
    main()