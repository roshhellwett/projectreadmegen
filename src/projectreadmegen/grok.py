import logging
from typing import Optional
from openai import OpenAI
from projectreadmegen import usagetracker

logger = logging.getLogger(__name__)


class GrokClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.groq.com/openai/v1"):
        self.api_key = api_key or usagetracker.get_api_key()
        self.base_url = base_url
        if not self.api_key:
            logger.warning("No GROQ_API_KEY provided")
        else:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate_readme(
        self,
        project_context: str,
        system_prompt: str = "You are a helpful assistant that writes excellent README files.",
        model: str = "llama-3.3-70b-versatile",
        max_tokens: int = 4000,
    ) -> str:
        if not self.api_key:
            raise ValueError("API key not set. Set GROQ_API_KEY environment variable or pass api_key.")

        try:
            response = self.client.responses.create(
                model=model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": project_context},
                ],
                max_output_tokens=max_tokens,
            )
            
            return response.output_text
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise


def build_project_context(scan_result: dict, detection: dict, config: dict) -> str:
    lines = []
    lines.append(f"# Project: {scan_result['name']}")
    lines.append(f"Type: {detection['project_type']}")
    lines.append(f"Primary Language: {detection['primary_lang']}")
    lines.append(f"Languages: {', '.join(detection['languages'])}")
    lines.append("")
    lines.append("## Files")
    for f in scan_result["files"][:100]:
        lines.append(f"- {f}")
    if len(scan_result["files"]) > 100:
        lines.append(f"... and {len(scan_result['files']) - 100} more files")
    lines.append("")
    lines.append("## Directories")
    for d in scan_result["dirs"][:30]:
        lines.append(f"- {d}")
    if len(scan_result["dirs"]) > 30:
        lines.append(f"... and {len(scan_result['dirs']) - 30} more directories")
    lines.append("")
    lines.append("## Folder Structure")
    lines.append("```")
    lines.append(scan_result["tree"])
    lines.append("```")
    lines.append("")
    lines.append("## Special Files Detected")
    if scan_result.get("has_license"):
        lines.append("- LICENSE file detected")
    if scan_result.get("has_contributing"):
        lines.append("- CONTRIBUTING.md detected")
    if scan_result.get("has_tests"):
        lines.append("- Tests directory detected")
    if scan_result.get("has_docs"):
        lines.append("- Documentation directory detected")
    lines.append("")
    lines.append("## Detected Install Command")
    lines.append(f"```\n{detection.get('install_cmd', 'N/A')}\n```")
    lines.append("")
    lines.append("## Detected Run Command")
    lines.append(f"```\n{detection.get('run_cmd', 'N/A')}\n```")
    lines.append("")
    lines.append("Write a comprehensive README.md for this project. Include:")
    lines.append("1. Project title and description")
    lines.append("2. Features section (fill in with likely features based on project type)")
    lines.append("3. Installation instructions")
    lines.append("4. Usage instructions")
    lines.append("5. Tech stack table")
    lines.append("6. Contributing guidelines if CONTRIBUTING.md exists")
    lines.append("7. License section")

    return "\n".join(lines)


def generate_ai_readme(scan_result: dict, detection: dict, config: dict) -> str:
    api_key = config.get("groq_api_key") or usagetracker.get_api_key()
    if not api_key:
        raise ValueError("GROQ_API_KEY not set. Please set it in config or environment.")

    client = GrokClient(api_key=api_key)

    context = build_project_context(scan_result, detection, config)

    system_prompt = """You are an expert technical writer specializing in creating README files for software projects.
Your READMEs are clear, concise, and professional.
- Use Markdown formatting properly
- Include code blocks with language hints
- Keep sections organized with clear headings
- Write in present tense for instructions
- Be specific but not verbose"""

    return client.generate_readme(context, system_prompt=system_prompt)
