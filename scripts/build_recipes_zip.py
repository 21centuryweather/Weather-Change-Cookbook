#!/usr/bin/env python3
"""
Create one zip per recipe, saved next to the recipe's notebook.

A "recipe" is any folder under recipes/ that directly contains a .ipynb file.

Only rebuilds a recipe's zip if its files have actually changed, based on a
content hash -- not on file modified-times. Timestamps aren't reliable here:
a fresh `git checkout` resets every file's mtime to "now", and in CI a
restored cache can end up with an even *later* mtime than the source files
it's meant to be checked against. A content hash sidesteps all of that.

Run this BEFORE `myst build --html` (locally and in CI).
"""
import hashlib
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


def content_hash(recipe: Path, files: list[Path]) -> str:
    """Hash of every included file's relative path + content, order-independent
    of filesystem timestamps."""
    h = hashlib.sha256()
    for f in files:  # `files` is already sorted, so this is deterministic
        h.update(str(f.relative_to(recipe)).encode())
        h.update(f.read_bytes())
    return h.hexdigest()


def main():
    dirs = recipe_dirs()
    if not dirs:
        raise SystemExit(f"No recipes found under {RECIPES}")

    for recipe in dirs:
        files = files_in(recipe)
        zip_path = recipe / f"{recipe.name}.zip"
        hash_path = recipe / f"{recipe.name}.zip.sha256"

        if not files:
            print(f"[skip] {recipe.relative_to(ROOT)}: no matching files")
            continue

        current_hash = content_hash(recipe, files)
        previous_hash = hash_path.read_text().strip() if hash_path.exists() else None

        if zip_path.exists() and current_hash == previous_hash:
            print(f"[up to date] {recipe.relative_to(ROOT)}: {zip_path.name}")
            continue

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                zf.write(f, Path(recipe.name) / f.relative_to(recipe))
        hash_path.write_text(current_hash)

        print(f"[built] {recipe.relative_to(ROOT)}: {len(files)} files -> {zip_path.name}")


if __name__ == "__main__":
    main()