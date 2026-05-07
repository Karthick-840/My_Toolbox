# PROVIDER_EXAMPLES

Converted from PROVIDER_EXAMPLES.md

```python
"""
Examples for using Deepseek and Kimi with the unified adapter layer.

This file demonstrates how to use the newly added Deepseek and Kimi providers
alongside existing providers (Ollama, Gemini, Groq).
"""

from llm_toolbox.clients import get_llm_client, ChatMessage

# ═══════════════════════════════════════════════════════════════════════════════════
# DEEPSEEK EXAMPLES
# ═══════════════════════════════════════════════════════════════════════════════════

def deepseek_simple_completion():
    """Simple completion using Deepseek API."""
    client = get_llm_client("deepseek", api_key="sk-...")
    
    messages = [
        ChatMessage(role="system", content="You are a helpful assistant."),
        ChatMessage(role="user", content="What is 2 + 2?"),
    ]
    
    response = client.complete(messages, temperature=0.7)
    print(f"Deepseek response: {response}")


def deepseek_custom_model():
    """Use a custom model with Deepseek."""
    client = get_llm_client(
        "deepseek",
        model="deepseek-coder-33b-instruct",
        api_key="sk-..."
    )
    
    messages = [
        ChatMessage(role="user", content="Write a Python hello world"),
    ]
    
    response = client.complete(messages)
    print(f"Code from Deepseek: {response}")


def deepseek_streaming():
    """Stream completions from Deepseek."""
    client = get_llm_client("deepseek", api_key="sk-...")
    
    messages = [
        ChatMessage(role="user", content="Explain quantum computing in 3 sentences."),
    ]
    
    for chunk in client.stream(messages):
        print(chunk, end="", flush=True)
    print()


def deepseek_custom_base_url():
    """Use a custom base URL (e.g., local proxy or alternative endpoint)."""
    client = get_llm_client(
        "deepseek",
        api_key="sk-...",
        base_url="https://api.custom-proxy.com/v1"
    )
    
    messages = [ChatMessage(role="user", content="Hello")]
    response = client.complete(messages)
    return response


# ═══════════════════════════════════════════════════════════════════════════════════
# KIMI (MOONSHOT) EXAMPLES
# ═══════════════════════════════════════════════════════════════════════════════════

def kimi_simple_completion():
    """Simple completion using Kimi/Moonshot API."""
    client = get_llm_client("kimi", api_key="...")
    
    messages = [
        ChatMessage(role="system", content="You are a helpful assistant."),
        ChatMessage(role="user", content="What is the capital of France?"),
    ]
    
    response = client.complete(messages, temperature=0.5)
    print(f"Kimi response: {response}")


def kimi_with_context_window():
    """Use Kimi's extended context window (128K tokens)."""
    client = get_llm_client(
        "kimi",
        model="moonshot-v1-128k",  # 128K context window
        api_key="..."
    )
    
    # You can now pass very long documents
    messages = [
        ChatMessage(role="user", content="Summarize this very long document: [document here]"),
    ]
    
    response = client.complete(messages)
    print(f"Summary: {response}")


def kimi_streaming():
    """Stream completions from Kimi."""
    client = get_llm_client("kimi", api_key="...")
    
    messages = [
        ChatMessage(role="user", content="Tell me a story about a robot."),
    ]
    
    for chunk in client.stream(messages):
        print(chunk, end="", flush=True)
    print()


def kimi_all_models():
    """Examples of all available Kimi models."""
    models = [
        "moonshot-v1-8k",      # 8K context - fastest, cheapest
        "moonshot-v1-32k",     # 32K context - balanced
        "moonshot-v1-128k",    # 128K context - best for long documents
    ]
    
    for model in models:
        client = get_llm_client(model=model, provider="kimi", api_key="...")
        messages = [ChatMessage(role="user", content="Hi")]
        # response = client.complete(messages)
        # print(f"Response from {model}: {response}")
        print(f"Created client for {model}")


# ═══════════════════════════════════════════════════════════════════════════════════
# COMPARISON ACROSS ALL PROVIDERS
# ═══════════════════════════════════════════════════════════════════════════════════

def compare_all_providers():
    """Compare responses from all available providers."""
    providers = [
        ("ollama", {"model": "llama3.2:latest"}),  # Local, free
        ("gemini", {"api_key": "API_KEY_HERE"}),  # Google
        ("groq", {"api_key": "API_KEY_HERE"}),  # Fast LPU
        ("deepseek", {"api_key": "API_KEY_HERE"}),  # Budget-friendly
        ("kimi", {"api_key": "API_KEY_HERE"}),  # High context window
    ]
    
    question = "What makes Python popular?"
    messages = [ChatMessage(role="user", content=question)]
    
    for provider_name, kwargs in providers:
        try:
            client = get_llm_client(provider_name, **kwargs)
            response = client.complete(messages, temperature=0.7)
            print(f"\n{provider_name.upper()}:\n{response[:200]}...\n")
        except Exception as e:
            print(f"{provider_name}: Error - {e}")


# ═══════════════════════════════════════════════════════════════════════════════════
# ENVIRONMENT VARIABLES (for secure credential management)
# ═══════════════════════════════════════════════════════════════════════════════════

"""
Set these environment variables to use providers securely without hardcoding keys:

For Deepseek:
    export DEEPSEEK_API_KEY="sk-..."
    export DEEPSEEK_MODEL="deepseek-chat"  # Optional, defaults to deepseek-chat
    export DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"  # Optional

For Kimi/Moonshot:
    export KIMI_API_KEY="..."
    export KIMI_MODEL="moonshot-v1-8k"  # Optional, defaults to moonshot-v1-8k
    export KIMI_BASE_URL="https://api.moonshot.cn/v1"  # Optional

Then use without passing kwargs:
    client = get_llm_client("deepseek")  # Reads DEEPSEEK_API_KEY from env
    client = get_llm_client("kimi")      # Reads KIMI_API_KEY from env
"""


if __name__ == "__main__":
    # Uncomment to run examples (requires API keys):
    # deepseek_simple_completion()
    # kimi_simple_completion()
    # deepseek_streaming()
    # kimi_streaming()
    # compare_all_providers()
    
    print("✅ Provider examples file loaded successfully")
    print("\nAvailable functions:")
    print("  - deepseek_simple_completion()")
    print("  - deepseek_custom_model()")
    print("  - deepseek_streaming()")
    print("  - deepseek_custom_base_url()")
    print("  - kimi_simple_completion()")
    print("  - kimi_with_context_window()")
    print("  - kimi_streaming()")
    print("  - kimi_all_models()")
    print("  - compare_all_providers()")
```
