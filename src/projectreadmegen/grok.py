# src/projectreadmegen/grok.py
#
# DEPRECATED — backwards-compatibility shim.
# All logic has moved to ai_provider.py.  This file re-exports everything
# so that existing ``from projectreadmegen.grok import ...`` continues to work.

from projectreadmegen.ai_provider import (  # noqa: F401
    GroqClient as GrokClient,
    GroqClient,
    build_project_context,
    generate_ai_readme,
    MAX_RETRIES,
    RETRY_DELAY,
    TIMEOUT,
)
