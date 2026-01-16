code() {
  # Try the standard 'code' command first
  if command -v /usr/local/bin/code >/dev/null 2>&1 || command -v /usr/bin/code >/dev/null 2>&1; then
    command code "$@"
  # Fallback to code-server
  elif command -v code-server >/dev/null 2>&1; then
    code-server "$@"
  else
    echo "Neither 'code' nor 'code-server' found in PATH" >&2
    return 1
  fi
}
