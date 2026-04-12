from pathlib import Path


def read_sourcecode(path: Path) -> str:
    """Return the contents of a file as a single string. This is the way to grab it all
    for feeding the LLM
    """
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def read_all_from_folder(path: Path) -> list[tuple[str, str]]:
    """Return a list of the contents of a folder, where each entry in the listing is a
    tuple of the form (filename, file_content)
    """
    results = []
    for entry in path.iterdir():
        if entry.is_symlink():
            continue
        if entry.is_file():
            results.append((entry.name, read_sourcecode(entry)))
        elif entry.is_dir():
            results.extend(read_all_from_folder(entry))
    return results
