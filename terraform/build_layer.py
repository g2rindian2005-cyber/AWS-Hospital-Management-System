#!/usr/bin/env python3
"""Build build/deps-layer.zip for the Lambda dependency layer.

Downloads Lambda-compatible wheels (manylinux, CPython 3.11) for
PyMySQL + cryptography on any host OS — including Windows — and zips
them under python/, the layout Lambda layers expect.

Terraform runs this automatically via the null_resource in main.tf;
you only need it by hand if you build the zip outside Terraform.
"""
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REQUIREMENTS = HERE.parent / "backend" / "patient-lambda" / "requirements.txt"
BUILD = HERE / "build"
TARGET = BUILD / "layer" / "python"
ARCHIVE = BUILD / "deps-layer"  # .zip is appended by make_archive


def main() -> None:
    if TARGET.exists():
        shutil.rmtree(TARGET)
    TARGET.mkdir(parents=True)
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install",
            "-r", str(REQUIREMENTS),
            "--target", str(TARGET),
            "--platform", "manylinux2014_x86_64",
            "--implementation", "cp",
            "--python-version", "3.11",
            "--only-binary", ":all:",
            "--upgrade",
        ],
        check=True,
    )
    for cache in TARGET.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    zip_path = ARCHIVE.with_suffix(".zip")
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(ARCHIVE), "zip", root_dir=BUILD / "layer", base_dir="python")
    print(f"Built {zip_path}")


if __name__ == "__main__":
    main()
