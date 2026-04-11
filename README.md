# Snitch

Snitch is an agentic application security scanner, developed as part of research efforts at Florida Institute of Technology

## Setup

You will need to setup Ollama to use this:

```bash
# Mac
curl -fsSL https://ollama.com/install.sh | sh

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

or for Windows, paste the following into PowerShell:

```powershell
irm https://ollama.com/install.ps1 | iex
```

You will then need to pull and serve the model we are currently using:

```bash
ollama pull llama3.1
ollama serve  # if not already running"
```
