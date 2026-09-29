#!/usr/bin/env python3
"""
Create one zip per recipe, saved next to the recipe's notebook.

A "recipe" is any folder under recipes/ that directly contains a .ipynb file.
For recipes/cold-fronts/cold-front-analysis.ipynb this produces
recipes/cold-fronts/cold-fronts.zip (named after the folder), which the
notebook's `downloads:` frontmatter points at.

Only rebuilds a recipe's zip if something inside it has changed since the
zip was last created -- this keeps local rebuilds and CI runs fast once a
project has many recipes.

Run this BEFORE `myst build --html` (locally and in CI).
"""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECIPES = ROOT / "recipes"

# Only these are bundled into each recipe's zip. Downloaded/generated data
# is deliberately excluded -- recipes should fetch data at run time from
# the public source, not ship a stale copy.
INCLUDE = ["*.ipynb", "*.py", "requirements.txt", "environment.yml", "README.md"]

# Skipped wherever they appear *inside a recipe folder* -- "data" holds
# downloaded datasets, the rest are build/cache artifacts. Checked against
# paths relative to the recipe (or to recipes/), never the full absolute
# path, so this can't accidentally match a folder name that happens to sit
# somewhere above the repo on disk (e.g. a clone path like ~/data/repo/...).
EXCLUDE_DIRS = {".ipynb_checkpoints", "__pycache__", "data", "_build", ".git"}


def recipe_dirs():
    """Every folder under recipes/ that directly contains a notebook."""
    found = set()
    for nb in RECIPES.rglob("*.ipynb"):
        rel_parts = nb.relative_to(RECIPES).parts
        if not any(part in EXCLUDE_DIRS for part in rel_parts):
            found.add(nb.parent)
    return sorted(found)


def files_in(recipe: Path):
    """Files to bundle for one recipe, deduplicated and sorted."""
    seen = set()
    for pattern in INCLUDE:
        for f in recipe.rglob(pattern):
            if f.suffix == ".zip":
                continue
            rel_parts = f.relative_to(recipe).parts
            if f in seen or any(part in EXCLUDE_DIRS for part in rel_parts):
                continue
            seen.add(f)
    return sorted(seen)


def needs_rebuild(zip_path: Path, files: list[Path]) -> bool:
    """True if the zip is missing or older than any of its source files."""
    if not zip_path.exists():
        return True
    zip_mtime = zip_path.stat().st_mtime
    return any(f.stat().st_mtime > zip_mtime for f in files)


def build_zip(recipe: Path, files: list[Path], zip_path: Path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(f, Path(recipe.name) / f.relative_to(recipe))


def main():
    dirs = recipe_dirs()
    if not dirs:
        raise SystemExit(f"No recipes found under {RECIPES}")

    for recipe in dirs:
        files = files_in(recipe)
        zip_path = recipe / f"{recipe.name}.zip"

        if not files:
            print(f"[skip] {recipe.relative_to(ROOT)}: no matching files")
            continue

        if not needs_rebuild(zip_path, files):
            print(f"[up to date] {recipe.relative_to(ROOT)}: {zip_path.name}")
            continue

        build_zip(recipe, files, zip_path)
        print(f"[built] {recipe.relative_to(ROOT)}: {len(files)} files -> {zip_path.name}")


if __name__ == "__main__":
    main()