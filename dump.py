import os
import json
import fnmatch
from datetime import datetime, UTC

FORCED_IGNORES = {".git"}


def load_gitignore(root_path):
    gitignore_path = os.path.join(root_path, ".gitignore")
    patterns = []

    if not os.path.exists(gitignore_path):
        return patterns

    with open(gitignore_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            patterns.append(line)

    return patterns


def is_ignored(path, root_path, patterns):
    try:
        rel_path = os.path.relpath(path, root_path).replace("\\", "/")
    except ValueError:
        return True  # ignore paths on different mounts / device paths

    parts = rel_path.split("/")

    if parts[0] in FORCED_IGNORES:
        return True

    for pattern in patterns:
        if pattern.endswith("/") and rel_path.startswith(pattern.rstrip("/")):
            return True

        if fnmatch.fnmatch(rel_path, pattern):
            return True

        if fnmatch.fnmatch(os.path.basename(rel_path), pattern):
            return True

    return False



def is_text_file(file_path, blocksize=512):
    try:
        with open(file_path, "rb") as f:
            return b"\0" not in f.read(blocksize)
    except Exception:
        return False


def read_file_content(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().replace("\n", "\\n")
    except Exception:
        return None


def scrape_directory(current_path, root_path, ignore_patterns):
    children = []

    try:
        entries = os.listdir(current_path)
    except PermissionError:
        return children

    for entry in entries:
        full_path = os.path.join(current_path, entry)

        if is_ignored(full_path, root_path, ignore_patterns):
            continue

        if os.path.isdir(full_path):
            children.append({
                "type": "directory",
                "name": entry,
                "path": full_path,
                "children": scrape_directory(full_path, root_path, ignore_patterns)
            })

        elif os.path.isfile(full_path):
            if not is_text_file(full_path):
                continue

            content = read_file_content(full_path)
            if content is None:
                continue

            children.append({
                "type": "file",
                "name": entry,
                "path": full_path,
                "size_bytes": os.path.getsize(full_path),
                "content": content
            })

    return children


def scrape_project(root_path):
    ignore_patterns = load_gitignore(root_path)

    return {
        "root": root_path,
        "generated_at": datetime.now(UTC).isoformat(),
        "structure": {
            "type": "directory",
            "name": os.path.basename(root_path),
            "path": root_path,
            "children": scrape_directory(root_path, root_path, ignore_patterns)
        }
    }


if __name__ == "__main__":
    ROOT_DIR = "./"
    result = scrape_project(os.path.abspath(ROOT_DIR))

    with open("project_dump3.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)

    print("Done → .git ignored, .gitignore respected ✔")
