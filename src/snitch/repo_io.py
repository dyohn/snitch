from dataclasses import dataclass
from pathlib import Path


@dataclass
class SourceCodeFile:
    filename: str
    filepath: Path
    content: str


class RepositoryIO:
    """Class for reading/processing a source code repository"""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.files: list[SourceCodeFile] = list()

    def read_repository(self, path: Path) -> list[SourceCodeFile]:
        """Walk the contents of a provided folder path, gathering up the contents of all the
        source code files into a listing that can be used to communicate with the SastAgent
        """
        # TODO implement
        pass
