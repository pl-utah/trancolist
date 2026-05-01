# Copyright 2026 The University of Utah
# SPDX-License-Identifier: MIT

import argparse
import datetime
import json
from pathlib import Path
import sys
from tap import Tap, Positional
from typing import Any, Literal

import block
import credentials
import tranco


class ArgParser(Tap):
    list_id: str | None = None
    """
    The list ID of an existing or pending list to get. Mutually exclusive with
    --config.
    """
    config: Path = Path("default.json")
    """
    The path to a json file that configures a new Tranco list. The json file
    should follow the schema at
    https://tranco-list.eu/api_documentation#datatypes-configuration, with one
    exception. If "pastDays": N is set, will request the last N days of data from
    today (this option is incompatible with "startDate" and "endDate").
    Mutually exclusive with --list-id.
    """
    creds: Path = Path("credentials.json")
    """
    The path to a json file with values for the keys "email" and "api_key".
    Environment variables `TRANCO_EMAIL` and `TRANCO_API_KEY` take precedence,
    so this option will be ignored if both are specified.
    """
    blocklists: set[Path] = {Path('adult-blocklist.txt')}
    """
    A list of files. Each file is a list of domains to exclude from the
    final list, one on each line.
    """
    top_n: int | Literal['full'] = 200
    """The number of domains to include"""
    force: bool = False
    """Overwrite `out_dir` if it already exists"""
    out_dir: Positional[Path]
    """The directory to write the list and metadata into"""

    def configure(self):
        self.add_argument('--config', action=ExplicitAction)
        self.add_argument('-b', '--blocklists')
        self.add_argument('-t', '--top-n', type=lambda s: s if s == 'all' else int(s))
        self.add_argument('-f', '--force')
    
    def process_args(self):
        # https://stackoverflow.com/a/50936474/3882118
        if self.list_id and hasattr(self, 'config_nondefault'):
            print("Cannot specify both --list-id and --config.")
            sys.exit(1)


class ExplicitAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        setattr(namespace, self.dest+'_nondefault', True)


def load_config(config: Path) -> dict[str, Any]:
    with open(config, 'r') as f:
        conf = json.load(f)
    if 'pastDays' in conf:
        if ('startDate' in conf) or ('endDate' in conf):
            print('Cannot specify "pastDays" with "startDate" or "endDate" in the config.')
            sys.exit(1)
        delta = datetime.timedelta(days=int(conf['pastDays']))
        conf['endDate'] = datetime.date.today().isoformat()
        conf['startDate'] = (datetime.date.today() - delta).isoformat()
        del conf['pastDays']
    return conf
    

def handle_tranco_list(list: tranco.TrancoList, blocklist: block.Blocklist, top_n_after_blocking: int | Literal['full'], out_dir: Path):
    # Write the webpage URL
    with (out_dir / f"{list.id()}_webpage.txt").open('w') as f:
        f.write(f"https://tranco-list.eu/list/{list.id()}/{list.top_n}")
    # Write the lists
    full_path = out_dir / f"{list.id()}_full.txt"
    filtered_path = out_dir / f"{list.id()}_filtered.txt"
    blocked_path = out_dir / f"{list.id()}_blocked.txt"
    with full_path.open('w') as full, filtered_path.open('w') as filtered, blocked_path.open('w') as blocked:
        domains = map(tranco.parse_tranco_line, list.stream)
        num_included = 0
        for domain in domains:
            if domain is None:
                continue
            full.write(f"{domain.inner}\n")
            if blocklist.blocks(domain):
                blocked.write(f"{domain.inner}\n")
            else:
                filtered.write(f"{domain.inner}\n")
                num_included += 1
            if top_n_after_blocking != 'full' and num_included >= top_n_after_blocking:
                break
        if top_n_after_blocking != 'full' and num_included < top_n_after_blocking:
            print(f"Warning: Could only get {num_included} out of {top_n_after_blocking} requested domains after filtering.", file=sys.stderr)


def filter_and_output_result(result: tranco.DownloadResult, blocklist: block.Blocklist, top_n_after_blocking: int | Literal['full'], out_dir: Path):
    try:
        out_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        files = out_dir.iterdir()
        try:
            file = next(files)
            if file.name == result.id():
                next(files)
            (out_dir / f"{result.id()}.out_dir_exists").touch()
            raise FileExistsError(f"Directory {out_dir} exists and contains files other than one with the current pending list ID {result.id()}. Refusing to overwrite.")
        except StopIteration:
            pass
    # Write the metadata json whether pending or finished
    with (out_dir / f"{result.id()}_metadata.json").open('w') as f:
        json.dump(result.metadata, f)
    pending_file = out_dir / f"{result.id()}.pending"
    match result:
        case tranco.InProgress(_) as in_progress:
            pending_file.touch()
        case tranco.TrancoList(_) as tranco_list:
            pending_file.unlink(missing_ok=True)
            handle_tranco_list(tranco_list, blocklist, top_n_after_blocking, out_dir)


def try_load_creds(creds_file: Path) -> credentials.Credentials | None:
    try:
        return credentials.load_credentials(creds_file)
    except credentials.MissingCredentialsError:
        return None


def maybe_request_email(tranco: tranco.Tranco, maybe_creds: credentials.Credentials | None, list_id: str) -> str:
    if maybe_creds is not None:
        tranco.request_email(maybe_creds.email, list_id, 'full')
        return " You will get an email when it is ready."
    else:
        return ""


def main():
    args = ArgParser(underscores_to_dashes=True).parse_args()
    # Try building blocklist first.
    blocklist = block.parse_blocklists(map(open, args.blocklists))
    # Then create the Tranco session.
    t = tranco.Tranco()
    if args.list_id is not None:
        creds = None
        metadata = t.get_list_id(args.list_id)
    else:
        creds = credentials.load_credentials(args.creds)
        assert args.config is not None
        metadata = t.request_custom_list(creds, load_config(args.config))
    
    result = t.download_if_available(metadata, 'full') # Download full list. We want to get top_n domains _after_ blocking some.
    match result:
        case tranco.InProgress(_) as in_progress:
            if creds is None:
                creds = try_load_creds(args.creds)
            email_msg = maybe_request_email(t, creds, in_progress.id())
            print(f"Tranco is generating list {in_progress.id()}.{email_msg} Rerun with --list-id once it is available.", file=sys.stderr)
        case tranco.TrancoList(_):
            pass
    filter_and_output_result(result, blocklist, args.top_n, args.out_dir)
    sys.exit(0)


if __name__ == "__main__":
    main()