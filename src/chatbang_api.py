#!/usr/bin/env python3
"""
chatbang_api.py

A CLI similar to "chatbang" but using the OpenAI Chat Completions API directly (no browser).

Features:
- Accepts prompt from CLI args, stdin (pipe), or interactive REPL.
- Supports system prompt, model, temperature, max tokens, top_p.
- Streaming output with graceful fallback if streaming is unavailable.
- Conversation session persistence to JSONL files under ~/.chatbang/sessions.
- Ability to start a new session, clear, or list sessions.

Requirements:
- openai (v1 client preferred; legacy fallback supported)
- python-dotenv (optional; loads .env)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, List, Optional


def print_err(message: str) -> None:
    print(message, file=sys.stderr)


def load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv()
    except Exception:
        # Silently ignore if dotenv is not installed or fails
        pass


def default_sessions_dir() -> Path:
    return Path(os.path.expanduser("~/.chatbang/sessions"))


def list_sessions(sessions_dir: Path) -> List[Path]:
    if not sessions_dir.exists():
        return []
    return sorted([p for p in sessions_dir.glob("*.jsonl") if p.is_file()])


def load_session_history(session_file: Path) -> List[Dict[str, str]]:
    if not session_file.exists():
        return []
    messages: List[Dict[str, str]] = []
    with session_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict) and "role" in obj and "content" in obj:
                    messages.append({"role": obj["role"], "content": obj["content"]})
            except json.JSONDecodeError:
                continue
    return messages


def append_session_message(session_file: Path, role: str, content: str) -> None:
    session_file.parent.mkdir(parents=True, exist_ok=True)
    record = {"role": role, "content": content}
    with session_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chatbang-api",
        description="Chat from the terminal using the OpenAI API with chatbang-like UX.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            Examples:
              echo "What is the capital of France?" | chatbang-api
              chatbang-api -p "Write a haiku about the sea." -m gpt-4o-mini
              chatbang-api -i --session notes --system "You are a terse assistant." --stream
            """
        ),
    )

    # Input modes
    parser.add_argument(
        "-p",
        "--prompt",
        type=str,
        help="Prompt text (if omitted, reads from stdin when piped or enters interactive mode)",
    )
    parser.add_argument(
        "--prompt-file",
        type=str,
        help="Path to a file whose entire contents will be used as the prompt",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Start interactive chat REPL (default if no prompt provided and stdin is a TTY)",
    )

    # Model params
    parser.add_argument(
        "-m",
        "--model",
        default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        help="Model name (default: env OPENAI_MODEL or gpt-4o-mini)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
        help="Sampling temperature (default: 0.7)",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=None,
        help="Nucleus sampling top_p (optional)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help="Max tokens for the response (optional)",
    )
    parser.add_argument(
        "--system",
        type=str,
        default=os.getenv("OPENAI_SYSTEM", "You are a helpful assistant."),
        help="System prompt to steer the assistant",
    )
    parser.add_argument(
        "--no-system",
        action="store_true",
        help="Do not include any system message",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional seed for deterministic sampling (if supported)",
    )

    # Session management
    parser.add_argument(
        "--session",
        type=str,
        help="Name of the session to persist conversation history under ~/.chatbang/sessions/<name>.jsonl",
    )
    parser.add_argument(
        "--new",
        action="store_true",
        help="Start a new session (ignores any existing history)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear the specified session and exit",
    )
    parser.add_argument(
        "--list-sessions",
        action="store_true",
        help="List available sessions and exit",
    )

    # Output behavior
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Stream tokens as they arrive (falls back to non-streaming if unsupported)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress extra logs; print only the assistant response",
    )

    # API key
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.getenv("OPENAI_API_KEY"),
        help="OpenAI API key (or set env OPENAI_API_KEY)",
    )

    return parser


def is_input_from_pipe() -> bool:
    return not sys.stdin.isatty()


def read_prompt_from_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_messages(system_prompt: Optional[str], history: List[Dict[str, str]], user_prompt: Optional[str]) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(history)
    if user_prompt is not None:
        messages.append({"role": "user", "content": user_prompt})
    return messages


def call_openai_chat(
    api_key: str,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.7,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
    stream: bool = False,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Call OpenAI Chat API with compatibility across SDK versions.

    Returns a dict with keys:
      - "content": str (full assistant content, present when stream=False or after streaming completes)
      - "stream_iter": optional iterator of string deltas when stream=True
    """
    # Try modern v1 client first
    try:
        from openai import OpenAI  # type: ignore

        client = OpenAI(api_key=api_key)
        if stream:
            try:
                def generator() -> Generator[str, None, None]:
                    stream_resp = client.chat.completions.create(
                        model=model,
                        messages=messages,  # type: ignore[arg-type]
                        temperature=temperature,
                        top_p=top_p,
                        max_tokens=max_tokens,
                        seed=seed,
                        stream=True,
                    )
                    for chunk in stream_resp:
                        try:
                            delta_content = chunk.choices[0].delta.content  # type: ignore[attr-defined]
                        except Exception:
                            delta_content = None
                        if isinstance(delta_content, str) and delta_content:
                            yield delta_content

                return {"stream_iter": generator()}
            except Exception:
                # Fallback to non-streaming if streaming path fails
                pass

        # Non-streaming modern call
        resp = client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            seed=seed,
        )
        content = resp.choices[0].message.content or ""
        return {"content": content}
    except Exception:
        # Legacy SDK fallback
        try:
            import openai  # type: ignore

            openai.api_key = api_key
            if stream:
                try:
                    def legacy_stream_generator() -> Generator[str, None, None]:
                        stream_resp = openai.ChatCompletion.create(
                            model=model,
                            messages=messages,  # type: ignore[arg-type]
                            temperature=temperature,
                            top_p=top_p,
                            max_tokens=max_tokens,
                            stream=True,
                        )
                        for chunk in stream_resp:
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content_piece = delta.get("content")
                            if content_piece:
                                yield content_piece

                    return {"stream_iter": legacy_stream_generator()}
                except Exception:
                    pass

            completion = openai.ChatCompletion.create(
                model=model,
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )
            content = completion["choices"][0]["message"]["content"] or ""
            return {"content": content}
        except Exception as e:
            raise RuntimeError(f"Failed to call OpenAI API: {e}")


def interactive_loop(
    api_key: str,
    model: str,
    temperature: float,
    top_p: Optional[float],
    max_tokens: Optional[int],
    seed: Optional[int],
    system_prompt: Optional[str],
    session_file: Optional[Path],
    stream: bool,
    quiet: bool,
) -> int:
    history: List[Dict[str, str]] = []
    if session_file and session_file.exists():
        history = load_session_history(session_file)

    if not quiet:
        print("Entering interactive mode. Type Ctrl-D or Ctrl-C to exit.")

    while True:
        try:
            user_input = input("You: ")
        except (EOFError, KeyboardInterrupt):
            if not quiet:
                print()
                print("Bye.")
            return 0

        user_input = user_input.strip()
        if not user_input:
            continue

        # Persist user message and build messages
        current_history: List[Dict[str, str]]
        if session_file:
            append_session_message(session_file, "user", user_input)
            current_history = load_session_history(session_file)
        else:
            history.append({"role": "user", "content": user_input})
            current_history = history

        messages = get_messages(system_prompt, current_history, None)
        # The last entry in current_history is the just-added user message, so no extra append here

        try:
            result = call_openai_chat(
                api_key=api_key,
                model=model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                stream=stream,
                seed=seed,
            )
        except Exception as e:
            print_err(f"Error: {e}")
            continue

        if "stream_iter" in result and result["stream_iter"] is not None:
            assistant_text_parts: List[str] = []
            for delta in result["stream_iter"]:  # type: ignore[index]
                sys.stdout.write(delta)
                sys.stdout.flush()
                assistant_text_parts.append(delta)
            print()
            assistant_text = "".join(assistant_text_parts)
        else:
            assistant_text = result.get("content", "")
            print(assistant_text)

        if session_file:
            append_session_message(session_file, "assistant", assistant_text)
        else:
            history.append({"role": "assistant", "content": assistant_text})

    # Unreachable
    # return 0


def main(argv: Optional[List[str]] = None) -> int:
    load_dotenv_if_available()
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.list_sessions:
        sessions_dir = default_sessions_dir()
        sessions = list_sessions(sessions_dir)
        if not sessions:
            print("No sessions found.")
            return 0
        for p in sessions:
            size = p.stat().st_size
            mtime = datetime.fromtimestamp(p.stat().st_mtime).isoformat(sep=" ", timespec="seconds")
            print(f"{p.stem}\t{size}B\t{mtime}")
        return 0

    # Resolve API key
    api_key: Optional[str] = args.api_key
    if not api_key:
        print_err("Missing OpenAI API key. Set --api-key or env OPENAI_API_KEY.")
        return 2

    # Resolve session file
    session_file: Optional[Path] = None
    if args.session:
        sessions_dir = default_sessions_dir()
        session_file = sessions_dir / f"{args.session}.jsonl"
        if args.clear:
            try:
                if session_file.exists():
                    session_file.unlink()
                print(f"Cleared session '{args.session}'.")
            except Exception as e:
                print_err(f"Failed to clear session: {e}")
                return 1
            return 0
        if args.new and session_file.exists():
            try:
                session_file.unlink()
            except Exception as e:
                print_err(f"Failed to reset session: {e}")
                return 1

    # Prepare input prompt
    prompt: Optional[str] = args.prompt
    if args.prompt_file:
        prompt = read_prompt_from_file(args.prompt_file)
    elif prompt is None and is_input_from_pipe():
        prompt = sys.stdin.read()

    system_prompt: Optional[str] = None if args.no_system else args.system

    # Decide mode
    if args.interactive or (prompt is None and sys.stdin.isatty()):
        return interactive_loop(
            api_key=api_key,
            model=args.model,
            temperature=args.temperature,
            top_p=args.top_p,
            max_tokens=args.max_tokens,
            seed=args.seed,
            system_prompt=system_prompt,
            session_file=session_file,
            stream=args.stream,
            quiet=args.quiet,
        )

    if prompt is None:
        print_err("No prompt provided. Use -p/--prompt, --prompt-file, pipe stdin, or -i for interactive mode.")
        return 2

    # Single-turn mode
    history: List[Dict[str, str]] = []
    if session_file and session_file.exists():
        history = load_session_history(session_file)

    messages = get_messages(system_prompt, history, prompt)

    try:
        result = call_openai_chat(
            api_key=api_key,
            model=args.model,
            messages=messages,
            temperature=args.temperature,
            top_p=args.top_p,
            max_tokens=args.max_tokens,
            stream=args.stream,
            seed=args.seed,
        )
    except Exception as e:
        print_err(f"Error: {e}")
        return 1

    if "stream_iter" in result and result["stream_iter"] is not None:
        assistant_text_parts: List[str] = []
        for delta in result["stream_iter"]:  # type: ignore[index]
            sys.stdout.write(delta)
            sys.stdout.flush()
            assistant_text_parts.append(delta)
        print()
        assistant_text = "".join(assistant_text_parts)
    else:
        assistant_text = result.get("content", "")
        print(assistant_text)

    # Persist session if requested
    if session_file:
        append_session_message(session_file, "user", prompt)
        append_session_message(session_file, "assistant", assistant_text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

