#!/usr/bin/env python3
"""Package the Atlantean Sovereignty content into a production-ready bundle.

This script gathers the Atlantean data files, documentation, optional
production server, and deployment assets into a single distribution artifact
that can be shipped to players. By default it produces a zip archive under
``dist/atlantean_prod.zip``; alternatively, a directory tree can be created with
``--format dir`` for installers that expect unpacked assets.

Usage examples::

    python3 utils/package_atlantean_release.py
    python3 utils/package_atlantean_release.py --format dir --output build/prod

Run the script from any working directory inside the repository. The tool
ensures that only Atlantean-specific assets (data and documentation) are
included so the resulting bundle can be distributed alongside a stock Endless
Sky build without leaking unrelated development files.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Iterable, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Package the Atlantean Sovereignty content for release.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output",
        "-o",
        default="dist/atlantean_prod.zip",
        help="Location of the generated archive or directory.",
    )
    parser.add_argument(
        "--format",
        choices={"zip", "dir"},
        help=(
            "Type of artifact to create. If omitted, the format is guessed from "
            "the output path extension ('.zip' => zip, otherwise directory)."
        ),
    )
    parser.add_argument(
        "--include-docs",
        dest="include_docs",
        action="store_true",
        help="Include Atlantean documentation alongside the data pack.",
    )
    parser.add_argument(
        "--no-include-docs",
        dest="include_docs",
        action="store_false",
        help="Exclude Atlantean documentation from the bundle.",
    )
    parser.set_defaults(include_docs=True)
    parser.add_argument(
        "--include-server",
        dest="include_server",
        action="store_true",
        help="Bundle the Atlantean production service alongside the content.",
    )
    parser.add_argument(
        "--no-include-server",
        dest="include_server",
        action="store_false",
        help="Omit the production service from the bundle.",
    )
    parser.set_defaults(include_server=True)
    parser.add_argument(
        "--include-ops",
        dest="include_ops",
        action="store_true",
        help="Include Docker Compose deployment assets.",
    )
    parser.add_argument(
        "--no-include-ops",
        dest="include_ops",
        action="store_false",
        help="Skip the deployment assets (ops/atlantean).",
    )
    parser.set_defaults(include_ops=True)
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite the output if it already exists.",
    )
    return parser.parse_args(argv)


def resolve_sources(
    include_docs: bool,
    include_server: bool,
    include_ops: bool,
) -> Tuple[Path, ...]:
    """Return the Atlantean content resources to package."""

    sources = [REPO_ROOT / "data" / "atlantean"]
    if include_docs:
        sources.append(REPO_ROOT / "docs" / "atlantean")
    if include_server:
        sources.append(REPO_ROOT / "server" / "atlantean_server.py")
    if include_ops:
        sources.append(REPO_ROOT / "ops" / "atlantean")

    missing = [path for path in sources if not path.exists()]
    if missing:
        joined = ", ".join(str(path.relative_to(REPO_ROOT)) for path in missing)
        raise FileNotFoundError(
            f"Missing required Atlantean resources: {joined}. "
            "Verify that you are packaging from the Endless Sky repository."
        )

    return tuple(sources)


def iter_files(sources: Iterable[Path]) -> Iterable[Tuple[Path, Path]]:
    """Yield ``(absolute_path, relative_path)`` for Atlantean files."""

    for source in sources:
        if source.is_dir():
            for path in source.rglob("*"):
                if path.is_file():
                    yield path, path.relative_to(REPO_ROOT)
        elif source.is_file():
            yield source, source.relative_to(REPO_ROOT)


def make_zip(files: Iterable[Tuple[Path, Path]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for absolute, relative in files:
            archive.write(absolute, arcname=str(relative))


def make_directory(files: Iterable[Tuple[Path, Path]], output_path: Path) -> None:
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    for absolute, relative in files:
        destination = output_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(absolute, destination)


def determine_format(args: argparse.Namespace) -> str:
    if args.format:
        return args.format
    return "zip" if args.output.lower().endswith(".zip") else "dir"


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    output_path = (Path(args.output)).expanduser().resolve()
    artifact_format = determine_format(args)

    if output_path.exists() and not args.force:
        print(
            f"Error: {output_path} already exists. Use --force to overwrite.",
            file=sys.stderr,
        )
        return 1

    try:
        sources = resolve_sources(
            include_docs=args.include_docs,
            include_server=args.include_server,
            include_ops=args.include_ops,
        )
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    files = tuple(iter_files(sources))

    if not files:
        print(
            "No Atlantean files were found to package. Ensure the data pack is present.",
            file=sys.stderr,
        )
        return 3

    if artifact_format == "zip":
        make_zip(files, output_path)
        print(f"Created Atlantean release archive at {output_path}")
    else:
        make_directory(files, output_path)
        print(f"Copied Atlantean release directory to {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
