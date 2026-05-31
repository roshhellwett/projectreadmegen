import logging
import time
from typing import Optional
from openai import OpenAI, APIError, APIConnectionError, APITimeoutError
from projectreadmegen import usagetracker
from projectreadmegen.exceptions import APIError as CustomAPIError

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
TIMEOUT = 60  # seconds


class GrokClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.groq.com/openai/v1",
        timeout: int = TIMEOUT,
    ):
        self.api_key = api_key or usagetracker.get_api_key()
        self.base_url = base_url
        self.timeout = timeout
        if not self.api_key:
            logger.warning("No GROQ_API_KEY provided")
        else:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=timeout)

    def generate_readme(
        self,
        project_context: str,
        system_prompt: str = "You are a helpful assistant that writes excellent README files.",
        model: str = "llama-3.3-70b-versatile",
        max_tokens: int = 4000,
    ) -> str:
        """
        Generate README with retry logic and error handling.

        Raises:
            CustomAPIError: If API call fails after retries.
        """
        if not self.api_key:
            raise CustomAPIError(
                "API key not set",
                "API key not configured. Set GROQ_API_KEY environment variable or add via menu option 3.",
            )

        # Validate inputs
        if not project_context or not isinstance(project_context, str):
            raise CustomAPIError(
                "Invalid project context provided",
                "Project context is empty or invalid.",
            )

        if not system_prompt or not isinstance(system_prompt, str):
            raise CustomAPIError(
                "Invalid system prompt provided",
                "System prompt is empty or invalid.",
            )

        if max_tokens < 100 or max_tokens > 8000:
            logger.warning(f"max_tokens {max_tokens} outside recommended range, clamping to valid range")
            max_tokens = max(100, min(8000, max_tokens))

        # Retry logic
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Calling Groq API (attempt {attempt + 1}/{MAX_RETRIES})...")

                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": project_context},
                    ],
                    max_tokens=max_tokens,
                )

                if not response.choices or not response.choices[0].message:
                    raise CustomAPIError(
                        "Empty response from Groq API",
                        "The API returned an empty response. Please try again.",
                    )

                content = response.choices[0].message.content
                if not content:
                    raise CustomAPIError(
                        "No content in API response",
                        "The API returned empty content. Please try again.",
                    )

                logger.info(f"Successfully generated README ({len(content)} characters)")
                return content

            except APITimeoutError as e:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"API timeout, retrying in {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)
                else:
                    raise CustomAPIError(
                        f"API timeout after {MAX_RETRIES} attempts: {e}",
                        "The API took too long to respond. Please check your connection and try again.",
                    )

            except APIConnectionError as e:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Connection error, retrying in {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)
                else:
                    raise CustomAPIError(
                        f"Cannot connect to Groq API after {MAX_RETRIES} attempts: {e}",
                        "Unable to connect to the Groq API. Check your internet connection and try again.",
                    )

            except APIError as e:
                # Check for rate limiting
                if "rate" in str(e).lower() or getattr(e, "status_code", None) == 429:
                    if attempt < MAX_RETRIES - 1:
                        wait_time = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                    else:
                        raise CustomAPIError(
                            f"Rate limited after {MAX_RETRIES} attempts: {e}",
                            "API rate limit exceeded. Please wait a moment and try again.",
                        )
                else:
                    # Other API errors
                    raise CustomAPIError(
                        f"Groq API error: {e}",
                        f"API error: {str(e)[:100]}. Please check your API key and try again.",
                    )

            except Exception as e:
                logger.error(f"Unexpected error calling Groq API: {type(e).__name__}: {e}")
                raise CustomAPIError(
                    f"Unexpected error: {e}",
                    f"An unexpected error occurred: {str(e)[:100]}",
                )


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
    lines.append(
        "2. Features section (fill in with likely features based on project type)"
    )
    lines.append("3. Installation instructions")
    lines.append("4. Usage instructions")
    lines.append("5. Tech stack table")
    lines.append("6. Contributing guidelines if CONTRIBUTING.md exists")
    lines.append("7. License section")

    return "\n".join(lines)


def generate_ai_readme(scan_result: dict, detection: dict, config: dict) -> str:
    """
    Generate AI-powered README with proper error handling.

    Raises:
        CustomAPIError: If API key is missing or API call fails.
    """
    api_key = config.get("groq_api_key") or usagetracker.get_api_key()
    if not api_key:
        raise CustomAPIError(
            "No Groq API key configured",
            "Please set your API key using the menu option 3 'Manage API Key'.",
        )

    if not isinstance(scan_result, dict) or not isinstance(detection, dict):
        raise CustomAPIError(
            "Invalid scan or detection data provided",
            "Internal error: invalid data passed to AI generation.",
        )

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
