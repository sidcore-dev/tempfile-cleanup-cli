# tempfile-cleanup-cli

A small, dependency-free command-line tool that finds files older than a
given age in directories you specify, reports how much space they're
taking up, and — only if you ask it to — deletes them.

## Why

Scratch directories, build caches, and log dumps quietly grow forever.
`tempfile-cleanup-cli` gives you a quick way to see what's old and how much
it would free up before anything gets removed. It never touches a path you
didn't name on the command line, and it never deletes anything unless you
pass `--apply`.

## Install

```bash
pip install .
```

This installs a `tempfile-cleanup-cli` command on your PATH.

## Usage

```bash
tempfile-cleanup-cli ./build/tmp ./logs --older-than 30d
```

Example output:

```
  2.1MB  ./build/tmp/cache-a1b2.bin
340.0KB  ./logs/debug-2026-01-04.log
 12.0KB  ./logs/debug-2026-01-05.log

3 file(s), 2.4MB reclaimable
(dry run — pass --apply to delete these files)
```

Once you're happy with the list, actually delete the files:

```bash
tempfile-cleanup-cli ./build/tmp ./logs --older-than 30d --apply
```

### Options

| Flag            | Description                                                        |
|-----------------|----------------------------------------------------------------------|
| `paths`         | One or more files/directories to scan — required, never defaulted   |
| `--older-than`  | Age threshold, e.g. `7d`, `12h`, `30m`, `45s` (default: `7d`)        |
| `--apply`       | Actually delete matched files (default is a dry-run listing only)   |

`paths` must always be given explicitly — the tool will never scan a system
temp directory (like `/tmp`) on your behalf.

### Exit codes

- `0` — ran successfully (dry run, or apply with no delete errors)
- `1` — `--apply` was used and at least one file failed to delete
- `2` — bad arguments (invalid `--older-than` value)

## Development

```bash
pip install -e .
python -m unittest discover -s tests -v
```

## License

All rights reserved. This code is public for viewing and reference only —
no license is granted to use, copy, modify, or redistribute it. See
[LICENSE](LICENSE) for details.
