"""CLI for standalone chat using langchain_adapters.

Example:
python -m langchain_adapters.cli --provider deepseek --prompt "Explain RAG in 3 bullets"
"""

from __future__ import annotations

import argparse

from .bridge import UnifiedToolboxLLM


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified chat CLI for langchain_adapters")
    parser.add_argument("--provider", required=True, choices=["ollama", "gemini", "openai", "deepseek"])
    parser.add_argument("--prompt", required=True, help="User prompt")
    parser.add_argument("--model", default=None, help="Model override")
    parser.add_argument("--system", default=None, help="Optional system prompt")
    parser.add_argument("--backend", default="auto", choices=["auto", "llm_toolbox", "langchain"])
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--log", action="store_true", help="Enable my_toolbox log_calls when available")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    llm = UnifiedToolboxLLM(
        provider=args.provider,
        model=args.model,
        backend=args.backend,
        use_my_toolbox_logging=args.log,
        temperature=args.temperature,
    )
    output = llm.invoke(prompt=args.prompt, system_prompt=args.system)
    print(output)


if __name__ == "__main__":
    main()
