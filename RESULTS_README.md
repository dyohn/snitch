# Snitch Experiment Results

## Overview
This folder contains the output of the Snitch agentic SAST scanner experiment,
conducted as part of a research project at Florida Institute of Technology.
The experiment compares a traditional SAST tool (Bandit) against an LLM-based
agentic scanner (Snitch) across three open-source Python repositories.

## Target Repositories
| Repository | Description |
|------------|-------------|
| yum | RPM package manager for Linux |
| beaverhabits | Self-hosted habit tracking web app |
| fail2ban | Intrusion prevention framework |

## Bandit Baseline Results
Bandit results are stored in: `../results/bandit/`

| Repository | HIGH | MEDIUM | LOW | TOTAL |
|------------|------|--------|-----|-------|
| yum | 0 | 0 | 6 | 6 |
| beaverhabits | 2 | 2 | 142 | 146 |
| fail2ban | 5 | 32 | 21 | 58 |

## Snitch LLM Scan Results (llama3.1)
| Repository | Files Scanned | Findings | Skipped |
|------------|--------------|----------|---------|
| beaverhabits | 138 | 101 | 37 |
| yum | 198 | 80 | 118 |
| fail2ban | 549 | 388 | 161 |

## Output Folder Structure
Each output folder follows the naming convention:
`output_<repository>_<model>/`

| Folder | Contents |
|--------|----------|
| output_beaverhabits_llama3.1/ | Snitch scan of BeaverHabits using llama3.1 |
| output_yum_llama3.1/ | Snitch scan of Yum using llama3.1 |
| output_fail2ban_llama3.1/ | Snitch scan of Fail2ban using llama3.1 |

## Output File Format
Each folder contains `snitch_results.json` with this structure:
```json
[
  {
    "filename": "example.py",
    "filepath": "../repo/path/to/example.py",
    "where": "example.py:10-15",
    "what": "Description of the security issue",
    "why": "Why this is a security problem",
    "fix": "How to fix or mitigate the issue"
  }
]
```

### Field Descriptions
| Field | Description |
|-------|-------------|
| filename | Name of the scanned file |
| filepath | Full relative path to the file |
| where | File and line numbers where the issue was found |
| what | What the security issue is |
| why | Why it is a security concern |
| fix | Recommended remediation steps |

If the LLM could not process a file, all fields except filename/filepath
will contain the value "skipped".

## Comparison Spreadsheet
`../results/snitch_results_comparison.xlsx` contains three sheets:
- **Bandit Baseline** - Bandit scan results for all three repos
- **LLM Scan Results** - Snitch findings per repo per model
- **Comparison Summary** - Side-by-side comparison of Bandit vs LLM

## Models Used
| Model | Provider | Size |
|-------|----------|------|
| llama3.1 | Meta | 4.9 GB |
| gemma3 | Google | 3.3 GB (planned) |
| qwen2.5 | Alibaba | 4.7 GB (planned) |

## Fix Applied
The original JSON parser in `sast_agent.py` failed to extract findings
because the LLM wraps JSON in explanatory text. A regex-based extractor
was added to pull the JSON object from anywhere in the response.
