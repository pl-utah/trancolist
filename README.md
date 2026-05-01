# trancolist

A script for the browser people to get a list of the top webpages.

## Usage

`uv run trancolist.py <out_dir>` to use default settings (ensure your email and API key are in `credentials.json`).

`uv run trancolist.py --help` for more usage information.

`uv run block.py [blocklist1.txt ...] <trancolist.txt>` to filter an already downloaded tranco list through a set of blocklists.
