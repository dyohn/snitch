from dataclasses import dataclass
from pathlib import Path
from typing import Generator

from snitch.file_utils import read_all_from_folder


@dataclass
class SourceCodeFile:
    filename: str
    filepath: Path
    content: str


class RepositoryIO:
    """Class for reading/processing a source code repository"""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path

    def read_repository(self) -> Generator[SourceCodeFile, None, None]:
        """Yield a SourceCodeFile for every file found under repo_path.
        Symlinks are skipped. Directories are walked recursively.
        """
        for filepath, content in read_all_from_folder(self.repo_path):
            yield SourceCodeFile(
                filename=filepath.name,
                filepath=filepath,
                content=content,
            )
