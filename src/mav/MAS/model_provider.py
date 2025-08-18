import os
import subprocess
from agents.extensions.models.litellm_model import LitellmModel


support_models = {
    "gpt_model": ["gpt-5", "gpt-5-mini", "gpt-5-nano", "o4-mini", "o3-mini", "gpt-4o", "gpt-4o-mini", "gpt-4o-turbo-preview"],
    "gemini_model": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"],
    "anthropic_model": ["claude-3.7", "claude-sonnet-4", "claude-opus-4", "claude-opus-4-1"],
    "deepseek_model": ["deepseek-r1", "deepseek-v3"],
    "ollama_models": ["ollama/gpt-oss:20b","ollama/gpt-oss:120b"]
}

def model_loader(model_name, max_tokens = 2000, temperature = 0.7):
    if model_name in support_models["gpt_model"]:
        return model_name
    elif model_name in support_models["gemini_model"]:
        return LitellmModel(model=f"gemini/{model_name}", api_key=os.getenv("GEMINI_API_KEY"))
    elif model_name in support_models["anthropic_model"]:
        if model_name == "claude-3.7":
            return LitellmModel(model=f"anthropic/claude-3-7-sonnet-20250219", api_key=os.getenv("ANTHROPIC_API_KEY"))
        elif model_name == "claude-sonnet-4":
            return LitellmModel(model=f"anthropic/claude-sonnet-4-20250514", api_key=os.getenv("ANTHROPIC_API_KEY"))
        elif model_name == "claude-opus-4":
            return LitellmModel(model=f"anthropic/claude-opus-4-20250514", api_key=os.getenv("ANTHROPIC_API_KEY"))
        elif model_name == "claude-opus-4-1":
            return LitellmModel(model=f"anthropic/claude-opus-4-1-20250805", api_key=os.getenv("ANTHROPIC_API_KEY"))
        else:
            raise ValueError(f"Unsupported Anthropic model: {model_name}")
    elif model_name in support_models["deepseek_model"]:
        if model_name == "deepseek-r1":
            return LitellmModel(model=f"deepseek/deepseek-reasoner", api_key=os.getenv("DEEPSEEK_API_KEY"))
        elif model_name == "deepseek-v3":
            return LitellmModel(model=f"deepseek/deepseek-chat", api_key=os.getenv("DEEPSEEK_API_KEY"))
        else:
            raise ValueError(f"Unsupported DeepSeek model: {model_name}")
    elif model_name in support_models["ollama_models"]:
        # Check if Ollama is installed
        if not check_ollama_installation():
            raise ValueError(f"Ollama is not installed or not running. Please install Ollama first.")
        
        # Check if the specific model is available
        if not check_ollama_model_available(model_name):
            model_only = model_name.replace("ollama/", "")
            raise ValueError(f"Ollama model '{model_only}' is not available. Please pull it first with: ollama pull {model_only}")
        
        if model_name == "ollama/gpt-oss:20b":
            return LitellmModel(model="ollama/gpt-oss:20b")
        elif model_name == "ollama/gpt-oss:120b":
            return LitellmModel(model="ollama/gpt-oss:120b")
        else:
            raise ValueError(f"Unsupported Ollama model: {model_name}")
    else:
        # Get all supported models for error message
        all_supported = []
        for models in support_models.values():
            all_supported.extend(models)
        raise ValueError(f"Model '{model_name}' is not supported. Supported models: {all_supported}")


def print_supported_models():
    """Print all supported models organized by provider."""
    print("Supported Models:")
    print("=" * 50)
    
    for provider, models in support_models.items():
        # Format provider name nicely
        provider_name = provider.replace("_", " ").title()
        print(f"\n{provider_name}:")
        print("-" * len(provider_name + ":"))
        
        for model in models:
            print(f"  • {model}")
    
    print(f"\nTotal: {sum(len(models) for models in support_models.values())} models")


def get_supported_models():
    """Return a dictionary of all supported models organized by provider."""
    return support_models.copy()


def check_ollama_model_available(model_name):
    """Check if an Ollama model is pulled and available locally."""
    try:
        # Extract just the model name (remove ollama/ prefix)
        model_only = model_name.replace("ollama/", "")
        
        # Run ollama list to get available models
        result = subprocess.run(
            ["ollama", "list"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if result.returncode == 0:
            # Check if model is in the list of available models
            available_models = result.stdout.lower()
            return model_only.lower() in available_models
        else:
            return False
            
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        # If ollama command fails or doesn't exist, return False
        return False


def check_ollama_installation():
    """Check if Ollama is installed and running."""
    try:
        result = subprocess.run(
            ["ollama", "--version"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return False