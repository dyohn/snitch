import json
import logging
import re
from collections.abc import Iterator
from typing import Any, Dict

import requests

from snitch.models import SastResult
from snitch.prompts import LLM_SAST_PROMPT, LLM_USER_TEMPLATE
from snitch.repo_io import RepositoryIO

logger = logging.getLogger(__name__)


class SastAgent:
    def __init__(
        self,
        model_name: str = "llama3.1",
        base_url: str = "http://localhost:11434",
    ):
        """Local FREE detector powered by Ollama
        Requirements:
          - Ollama installed (https://ollama.com)
          - Ollama server running:  `ollama serve`
          - Model pulled, e.g.,:    `ollama pull llama3.1`
        """
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.chat_url = f"{self.base_url}/api/chat"

    def _call_llm_raw(self, text: str) -> str:
        """Call Ollama chat API and return raw text response"""
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": LLM_SAST_PROMPT},
                {
                    "role": "user",
                    "content": LLM_USER_TEMPLATE.format(text=text),
                },
            ],
            "stream": False,
        }
        resp = requests.post(self.chat_url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        raw = data.get("message", {}).get("content", "")
        if not raw:
            raw = "{}"
        return raw

    def _parse_json(self, raw: str) -> Dict[str, Any]:
        logger.debug("Raw LLM response:\n%s", raw)
        raw = raw.strip()
        match = re.search(r'\{[^{}]*"where"[^{}]*\}', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception as exc:
                logger.warning(
                    "Regex-extracted JSON failed to parse (%s): %s",
                    exc,
                    match.group(),
                )
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()
        try:
            return json.loads(raw)
        except Exception as exc:
            logger.warning(
                "JSON parse failed (%s). Raw content was:\n%s",
                exc,
                raw,
            )
            return {
                "where": "skipped",
                "what": "skipped",
                "why": "skipped",
                "fix": "skipped",
            }

    def run(self, repo: RepositoryIO) -> Iterator[SastResult]:
        """Iterate every file in repo and yield a SastResult for each."""
        for src_file in repo.read_repository():
            finding = self.analyze(src_file.content)
            yield SastResult(
                filename=src_file.filename,
                filepath=src_file.filepath,
                finding=finding,
            )

    def analyze(self, text: str) -> Dict[str, Any]:
        """Return a dict with where/what/why/fix keys."""
        raw = self._call_llm_raw(text)
        return self._parse_json(raw)
