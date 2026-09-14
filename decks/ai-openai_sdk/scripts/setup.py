#!/usr/bin/env python3
"""Cross-platform environment setup and preflight script for ai-openai_sdk deck.

Works on Linux, macOS, and Windows without external dependencies (pure standard library).
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

MIN_PYTHON_VERSION = (3, 10)
DEFAULT_OLLAMA_URL = "http://localhost:11434/v1"
DEFAULT_OLLAMA_API_KEY = "ollama"
DEFAULT_OLLAMA_MODEL = "nemotron-3-nano:4b"
DEFAULT_OPENAI_MODEL = "gpt-5.6-luna"

DECK_ROOT = Path(__file__).resolve().parent.parent
PLAYGROUND_SCRIPT = DECK_ROOT / "playground" / "request_response.py"


def is_windows() -> bool:
    return platform.system().lower() == "windows"


def check_python_version() -> bool:
    current = sys.version_info[:2]
    formatted_current = f"{current[0]}.{current[1]}"
    formatted_min = f"{MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}"

    if current < MIN_PYTHON_VERSION:
        print(f"❌ Python {formatted_min}+ is required, but found {formatted_current}.")
        return False
    print(f"✔️ Python version: {formatted_current} (>= {formatted_min})")
    return True


def check_uv_installed() -> bool:
    uv_path = shutil.which("uv")
    if uv_path:
        try:
            version_out = subprocess.check_output(
                [uv_path, "--version"], text=True
            ).strip()
            print(f"✔️ uv installed: {version_out}")
            return True
        except Exception:
            print(f"✔️ uv found at: {uv_path}")
            return True

    print("⚠️  'uv' is not installed or not in PATH.")
    if is_windows():
        print("   Install uv: powershell -ExecutionPolicy ByPass -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
    else:
        print("   Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
    return False


def probe_ollama(base_url: str = DEFAULT_OLLAMA_URL) -> tuple[bool, list[str]]:
    """Check if local Ollama server is running and fetch available models."""
    root_url = base_url.rstrip("/").removesuffix("/v1")
    tags_url = f"{root_url}/api/tags"

    try:
        req = urllib.request.Request(tags_url, headers={"User-Agent": "adudeck-setup"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", []) if "name" in m]
                return True, models
    except (urllib.error.URLError, TimeoutError, OSError):
        pass
    return False, []


def run_preview_check() -> bool:
    if not PLAYGROUND_SCRIPT.is_file():
        print(f"❌ Playground script not found at {PLAYGROUND_SCRIPT}")
        return False

    print("\n==> Running local preview check (0 network / 0 token cost)...")
    cmd = [sys.executable, str(PLAYGROUND_SCRIPT), "--preview"]
    try:
        proc = subprocess.run(cmd, cwd=str(DECK_ROOT), capture_output=True, text=True, check=True)
        if "preview only" in proc.stdout:
            print("✔️ Local application argument preview verified successfully.")
            return True
        print("⚠️ Preview ran, but unexpected output received:")
        print(proc.stdout)
        return False
    except subprocess.CalledProcessError as exc:
        print(f"❌ Preview run failed: {exc}")
        print(exc.stderr)
        return False


def print_env_instructions(provider: str, base_url: str, api_key: str, model: str) -> None:
    print("\n" + "=" * 60)
    print(f"  Configuration for Provider: {provider.upper()}")
    print("=" * 60)

    if is_windows():
        print("\n[Windows PowerShell]")
        if base_url:
            print(f'$env:OPENAI_BASE_URL = "{base_url}"')
        print(f'$env:OPENAI_API_KEY = "{api_key}"')
        print(f'$env:OPENAI_MODEL = "{model}"')

        print("\n[Windows CMD (Command Prompt)]")
        if base_url:
            print(f'set OPENAI_BASE_URL={base_url}')
        print(f'set OPENAI_API_KEY={api_key}')
        print(f'set OPENAI_MODEL={model}')
    else:
        print("\n[Linux / macOS (bash / zsh)]")
        if base_url:
            print(f'export OPENAI_BASE_URL="{base_url}"')
        print(f'export OPENAI_API_KEY="{api_key}"')
        print(f'export OPENAI_MODEL="{model}"')

    print("\nRun playground with:")
    print("  uv run playground/request_response.py")
    print("=" * 60)


def write_env_file(path: Path, base_url: str, api_key: str, model: str) -> None:
    lines = []
    if base_url:
        lines.append(f'OPENAI_BASE_URL="{base_url}"')
    lines.append(f'OPENAI_API_KEY="{api_key}"')
    lines.append(f'OPENAI_MODEL="{model}"')
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✔️ Wrote environment file to: {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Setup and verify environment for OpenAI Python SDK deck."
    )
    parser.add_argument(
        "--provider",
        choices=["auto", "ollama", "openai"],
        default="auto",
        help="Provider choice (default: auto detects Ollama, falls back to OpenAI instructions)",
    )
    parser.add_argument(
        "--base-url",
        default="",
        help=f"Custom API Base URL (defaults to {DEFAULT_OLLAMA_URL} when provider is ollama)",
    )
    parser.add_argument(
        "--api-key",
        default="",
        help="API Key (defaults to 'ollama' for Ollama, or checks OPENAI_API_KEY for openai)",
    )
    parser.add_argument(
        "--model",
        default="",
        help="Target model identifier (defaults to detected Ollama model or deck baseline)",
    )
    parser.add_argument(
        "--write-env",
        action="store_true",
        help="Write configured variables to decks/ai-openai_sdk/.env file",
    )
    parser.add_argument(
        "--test-live",
        action="store_true",
        help="Run live API call test against configured provider after checks",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("==================================================")
    print("  adudeck: ai-openai_sdk Environment Setup")
    print(f"  Platform: {platform.system()} {platform.release()} ({platform.machine()})")
    print("==================================================")

    # 1. System checks
    py_ok = check_python_version()
    uv_ok = check_uv_installed()
    preview_ok = run_preview_check()

    # 2. Provider resolution
    provider = args.provider
    ollama_running, ollama_models = probe_ollama(args.base_url or DEFAULT_OLLAMA_URL)

    if provider == "auto":
        if ollama_running:
            provider = "ollama"
            print(f"\n✔️ Detected running local Ollama service with {len(ollama_models)} model(s).")
        else:
            provider = "openai"
            print("\nℹ️  Local Ollama not detected. Falling back to OpenAI API configuration.")

    base_url = args.base_url
    api_key = args.api_key
    model = args.model

    if provider == "ollama":
        base_url = base_url or DEFAULT_OLLAMA_URL
        api_key = api_key or DEFAULT_OLLAMA_API_KEY
        if not model:
            if DEFAULT_OLLAMA_MODEL in ollama_models:
                model = DEFAULT_OLLAMA_MODEL
            elif ollama_models:
                model = ollama_models[0]
            else:
                model = DEFAULT_OLLAMA_MODEL
        print(f"✔️ Selected provider: OLLAMA")
        print(f"   Base URL : {base_url}")
        print(f"   Model    : {model}")
        if ollama_models:
            print(f"   Installed models in Ollama: {', '.join(ollama_models)}")
        else:
            print(f"   ⚠️ No models detected. Make sure to run: ollama pull {model}")

    else:  # openai
        base_url = base_url  # keep empty if standard openai endpoint
        api_key = api_key or os.getenv("OPENAI_API_KEY", "sk-...")
        model = model or os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        print(f"✔️ Selected provider: OPENAI")
        print(f"   Model : {model}")
        if api_key.startswith("sk-...") or not api_key:
            print("   ⚠️  OPENAI_API_KEY is not set yet. Please supply a valid key before live calls.")
        else:
            print("   ✔️ OPENAI_API_KEY is detected in environment.")

    # 3. Output instructions or write .env
    print_env_instructions(provider, base_url, api_key, model)

    if args.write_env:
        env_path = DECK_ROOT / ".env"
        write_env_file(env_path, base_url, api_key, model)

    # 4. Optional Live test
    if args.test_live:
        print("\n==> Running live API call test...")
        env = os.environ.copy()
        if base_url:
            env["OPENAI_BASE_URL"] = base_url
        env["OPENAI_API_KEY"] = api_key
        env["OPENAI_MODEL"] = model

        cmd = [sys.executable, str(PLAYGROUND_SCRIPT)]
        if uv_ok:
            uv_bin = shutil.which("uv")
            if uv_bin:
                cmd = [uv_bin, "run", str(PLAYGROUND_SCRIPT)]

        try:
            res = subprocess.run(cmd, cwd=str(DECK_ROOT), env=env, text=True, check=True)
            print("\n🎉 Live API call succeeded!")
        except subprocess.CalledProcessError as exc:
            print(f"\n❌ Live API test failed with code {exc.returncode}")
            sys.exit(exc.returncode)

    print("\nSetup verification complete!")


if __name__ == "__main__":
    main()
