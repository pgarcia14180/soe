"""
LLM caller helpers for tests.







































































































































































































**Good luck! 🚀**- The `--integration` test flag has been removed (it was unused)- Code samples have been updated with correct imports- The articles in `ai_docs/MEDIUM_*.md` are ready to copy-paste to Medium## Notes---- Docs: https://github.com/pgarcia14180/soe/tree/main/docs- PyPI: https://pypi.org/project/soe/- GitHub: https://github.com/pgarcia14180/soe## Quick Links---4. **Wait for organic discovery:** Good tools get found eventually3. **Build in public:** Tweet/post about features as you add them2. **Find champions:** DM developers who might find it useful1. **Iterate on positioning:** Try different angles (testing story, infrastructure story)**Don't panic.** Most launches are quiet. Options:## If Things Don't Get Traction---- Accept PRs for backend implementations (PostgreSQL, etc.)- Write tutorials for common patterns- Create Discord/Slack if >100 stars### Community Building:- Post `MEDIUM_ARTICLE_TESTING.md` - the testing philosophy resonates with many- Post `MEDIUM_ARTICLE_ARCHITECTURE.md` - deep dive for interested readers### Follow-up content (next week):## If Things Go Well---- HN points- Medium views/claps- PyPI downloads: `pip show soe` or check pypistats.org- GitHub stars### Metrics to Track- [ ] Note feature requests for future- [ ] Fix any bugs reported- [ ] Thank early adopters### First 24 Hours- [ ] Monitor GitHub for stars/issues- [ ] Check Reddit every 30 min - answer questions- [ ] Check HN every 15 min - respond to all comments### First 4 Hours (Critical)## Monitoring & Engagement---| LinkedIn | Professional network | B2B visibility | Your network size || Twitter/X | Tech Twitter | Quick visibility | Depends on followers || Reddit | Niche communities | Targeted feedback | 1-10k per sub || Hacker News | Engineers, founders | Technical discussion | 10-100k if frontpage || Medium | Developers, tech readers | Long-form explanation | 1-5k views ||----------|----------|----------|----------------|| Platform | Audience | Best For | Expected Reach |## Platform Comparison---**Format:** Similar to Twitter thread but as single long-form post**When:** Good for professional network, especially if you have industry connections### Step 5: LinkedIn (Optional, same day)---**Hashtags:** #AI #Python #LLM #AgentAI #OpenSource7. Ask: "What patterns would you build with signal-driven orchestration?"6. Link: "Full article + repo: [Medium link] | [GitHub link]"5. Key benefit: "Same workflow runs locally, in tests, in production. Swap PostgreSQL for DynamoDB. Replace OpenAI with local LLM. The YAML never changes."4. Code snippet: Show a simple YAML workflow (screenshot or code block)3. The solution: "Signal-driven orchestration. Nodes emit events. Other nodes listen. Zero coupling."2. The problem: "Chains are tightly coupled. Step B knows about Step A. Change one, break the other."1. Hook: "Most AI agent frameworks got orchestration wrong. Here's why chains fail at scale →"**Thread structure (5-7 tweets):****Create account if needed:** Use your real name for credibility### Step 4: Twitter/X (Same day)---- Cross-post strategically (don't spam)- Include a code snippet in the post body- Different subs have different cultures - r/Python likes practical, r/ML likes novel**Tips:**"[P] SOE: Why signal-driven orchestration beats chains for multi-agent systems"**Title for r/MachineLearning:**"SOE: Signal-driven orchestration for AI workflows - an alternative to chain-based frameworks"**Title for r/Python:**- r/LocalLLaMA (300k members) - for self-hosted LLM users- r/Python (1.3M members) - for the library announcement- r/MachineLearning (900k members) - for the architecture angle**Best subreddits:**### Step 3: Reddit (1 hour after HN)---```Happy to answer questions about the architecture or signal-driven patterns.infrastructure portability without framework lock-in.they should emit signals. This unlocks parallelism, testability, and chain abstraction. The key insight: nodes shouldn't call each other, I built this during vacation after getting frustrated with LangChain's ```**Sample first comment:**- Respond to all comments quickly (first 2 hours are critical)- Don't be salesy - HN values technical substance- First comment should be from you explaining the "why"- Link directly to GitHub repo, not Medium**Tips:****Best timing:** Weekdays 9-11 AM EST (highest traffic)- "Show HN: Signal-driven orchestration for AI workflows (Python)"- "Why most agent frameworks got orchestration wrong"- "SOE: A signal-driven alternative to chain-based agent frameworks"**Title options (pick one):****URL:** [news.ycombinator.com/submit](https://news.ycombinator.com/submit)### Step 2: Hacker News (30 min after Medium)---**Key excerpt for preview:** The opening paragraph about chains being wrong.**Tags to use:** `ai`, `python`, `llm`, `agents`, `software-architecture`  - "The Startup"  - "Better Programming"   - "Towards Data Science"- Submit to publications (optional, takes days for approval):- Publish to your profile first- [Medium.com](https://medium.com) - Create free account**Where to post:****Which article?** Start with `MEDIUM_ARTICLE_INTRO.md` - it's the hook.### Step 1: Medium Article (Primary Content)**Timing matters.** Post in this order with 30-60 min gaps to maximize visibility.## Content Publishing Order---- [ ] Verify installation works: `pip install soe` in a fresh virtualenv- [ ] Publish: `uv publish` (requires PyPI token configured)### 3. PyPI Publication- [ ] Write release notes on GitHub (can be brief - link to Medium article)- [ ] Create a release tag: `git tag v0.1.0 && git push --tags`- [ ] Update README.md if needed (imports are now fixed)### 2. GitHub Repository- [ ] Verify package builds: `uv build`- [ ] Build docs: `uv run python scripts/build_docs.py`- [ ] Run tests: `cd soe && uv run pytest tests/ -x`### 1. Final Code Verification## Pre-Launch (30 min)---This is your launch day guide. Follow in order.**Date**: January 4, 2026
Provides a call_llm that can use either a stub or real model.
Verbose logging via --show=prompt,response

API Options:
- Copilot Chat API (default): Uses your Copilot subscription, much higher rate limits
- GitHub Models API: Strict rate limits, for occasional testing only

Set SOE_LLM_BACKEND=github_models to use GitHub Models API instead of Copilot.
"""

import os
import re
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Union, Set

# Global clients (lazy loaded)
_openai_client = None
_copilot_client = None

# Default model for Copilot Chat API
DEFAULT_MODEL = os.environ.get("SOE_TEST_MODEL", "gpt-4o")

# Which backend to use: "copilot" (default) or "github_models"
LLM_BACKEND = os.environ.get("SOE_LLM_BACKEND", "copilot")


def _get_verbose_flags() -> Set[str]:
    """Get enabled verbose flags from SOE_VERBOSE environment variable"""
    verbose = os.environ.get("SOE_VERBOSE", "")
    if not verbose:
        return set()
    return set(flag.strip() for flag in verbose.split(","))


def _wrap_with_verbose(call_llm_fn: Callable) -> Callable:
    """Wrap call_llm with verbose logging if enabled"""

    def wrapped(prompt: str, config: Dict[str, Any]) -> str:
        verbose_flags = _get_verbose_flags()
        log_prompt = "prompt" in verbose_flags
        log_response = "response" in verbose_flags

        if log_prompt:
            truncated = prompt[:2000] + "..." if len(prompt) > 2000 else prompt
            print(f"\n[PROMPT]\n{truncated}")

        result = call_llm_fn(prompt, config)

        if log_response:
            print(f"\n[RESPONSE]\n{result}")

        return result

    return wrapped


def create_call_llm(
    stub: Optional[Callable[[str, Dict[str, Any]], str]] = None,
    model: Optional[Union[str, bool]] = None,
) -> Callable[[str, Dict[str, Any]], str]:
    """
    Create an LLM caller for tests.

    Uses stub for fast, predictable tests. Use model=True for real LLM calls.

    Args:
        stub: Function that returns mock responses for tests
        model: Model name. If True, uses DEFAULT_MODEL.

    Returns:
        A call_llm function

    Usage:
        # Test with stub (fast, predictable)
        def my_stub(prompt, config):
            return '{"action": "finish"}'
        call_llm = create_call_llm(stub=my_stub)

        # Use real model
        call_llm = create_call_llm(model=True)
    """
    if model is True:
        model = DEFAULT_MODEL

    if model:
        # Choose backend based on environment variable
        if LLM_BACKEND == "github_models":
            return _wrap_with_verbose(_create_github_model_caller(model))
        else:
            return _wrap_with_verbose(_create_copilot_caller(model))
    elif stub:
        return _wrap_with_verbose(stub)
    else:
        raise ValueError("Either stub or model must be provided")


class CopilotChatClient:
    """
    Client for the Copilot Chat API - the same API that VS Code and CopilotChat.nvim use.
    Much higher rate limits than GitHub Models API since it's part of your Copilot subscription.
    """

    TOKEN_ENDPOINT = "https://api.github.com/copilot_internal/v2/token"
    CHAT_ENDPOINT = "https://api.githubcopilot.com/chat/completions"

    def __init__(self):
        self.oauth_token = self._load_oauth_token()
        self._api_token = None
        self._token_expires_at = 0

    def _load_oauth_token(self) -> str:
        """Load the OAuth token from Copilot's config files."""
        config_paths = [
            Path.home() / ".config/github-copilot/hosts.json",
            Path.home() / ".config/github-copilot/apps.json",
        ]

        # Also check XDG_CONFIG_HOME
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            config_paths.insert(0, Path(xdg_config) / "github-copilot/hosts.json")
            config_paths.insert(1, Path(xdg_config) / "github-copilot/apps.json")

        for path in config_paths:
            if path.exists():
                try:
                    data = json.loads(path.read_text())
                    for key, value in data.items():
                        if "github.com" in key and isinstance(value, dict):
                            if "oauth_token" in value:
                                return value["oauth_token"]
                except (json.JSONDecodeError, KeyError):
                    continue

        raise RuntimeError(
            "No Copilot OAuth token found. "
            "Run ':Copilot setup' in Neovim or sign in to Copilot in VS Code first.\n"
            "Token is expected in ~/.config/github-copilot/hosts.json or apps.json"
        )

    def _get_api_token(self) -> str:
        """Exchange OAuth token for short-lived API token."""
        import requests

        if self._api_token and time.time() < self._token_expires_at - 60:
            return self._api_token

        response = requests.get(
            self.TOKEN_ENDPOINT,
            headers={"Authorization": f"Token {self.oauth_token}"}
        )
        response.raise_for_status()
        data = response.json()

        self._api_token = data["token"]
        self._token_expires_at = data["expires_at"]

        return self._api_token

    def chat(self, messages: list, model: str = "gpt-4o") -> str:
        """Send a chat completion request to Copilot API."""
        import requests

        token = self._get_api_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Editor-Version": "Neovim/0.10.0",
            "Editor-Plugin-Version": "soe-tests/1.0.0",
            "Copilot-Integration-Id": "vscode-chat",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 2048,
            "temperature": 0.7,
        }

        response = requests.post(
            self.CHAT_ENDPOINT,
            headers=headers,
            json=payload,
        )
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]


def _create_copilot_caller(model: str) -> Callable[[str, Dict[str, Any]], str]:
    """Create a call_llm using Copilot Chat API (same as VS Code/CopilotChat.nvim)."""

    def call_llm(prompt: str, config: Dict[str, Any]) -> str:
        global _copilot_client

        # Lazy load the client
        if _copilot_client is None:
            _copilot_client = CopilotChatClient()

        result_text = _copilot_client.chat(
            messages=[{"role": "user", "content": prompt}],
            model=model
        )

        # Clean the output: remove markdown code blocks if present
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", result_text, re.DOTALL)
        if json_match:
            result_text = json_match.group(1)
        else:
            start = result_text.find('{')
            end = result_text.rfind('}')
            if start != -1 and end != -1:
                result_text = result_text[start:end+1]

        return result_text

    return call_llm


def _create_github_model_caller(model: str) -> Callable[[str, Dict[str, Any]], str]:
    """Create a call_llm using GitHub Models API (strict rate limits)."""

    def call_llm(prompt: str, config: Dict[str, Any]) -> str:
        global _openai_client

        # Lazy load the client
        if _openai_client is None:
            from openai import OpenAI

            github_token = os.environ.get("GITHUB_TOKEN")
            if not github_token:
                raise ValueError("GITHUB_TOKEN environment variable required for GitHub Models API")

            _openai_client = OpenAI(
                base_url="https://models.github.ai/inference/v1",
                api_key=github_token
            )

        response = _openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        result_text = response.choices[0].message.content

        # Clean the output: remove markdown code blocks if present
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", result_text, re.DOTALL)
        if json_match:
            result_text = json_match.group(1)
        else:
            start = result_text.find('{')
            end = result_text.rfind('}')
            if start != -1 and end != -1:
                result_text = result_text[start:end+1]

        return result_text

    return call_llm
