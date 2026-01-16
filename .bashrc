In my .bashrc file I have this function for fzf to basically open a file when I press enter: 

fo() {
  local file
  file=$(
    find . \
      -type f \
      -not -path '*/.git/*' \
      2>/dev/null |
    fzf --query="$1" --select-1 --exit-0 \
      --header-label ' File Type ' \
      --preview 'bat --color=always --style=numbers {} 2>/dev/null || cat {}' \
      --bind 'focus:+transform-header:file --brief {} 2>/dev/null || echo "No file selected"' \
      --bind 'focus:transform-preview-label:[[ -n {} ]] && printf " Previewing [%s] " {}' \
      \
      --color 'header-border:#ED8796,header-label:#ED8796' \
      --color 'preview-border:#C6A0F6,preview-label:#C6A0F6'
  )

  # Check if a file was actually selected
  if [[ -n "$file" ]]; then
    # 1. Try code-server first (specific to your VS Code host)
    if command -v code-server >/dev/null 2>&1; then
      code-server "$file"
    # 2. Try the standard 'code' command (VS Code Desktop)
    elif command -v code >/dev/null 2>&1; then
      code "$file"
    # 3. Fallback to the system's default editor (vi, nano, etc.)
    else
      ${EDITOR:-vi} "$file"
    fi
  fi
}


I want to be able to also make an alias called "code" that first tries to use "code {filename}" to open a file and if that fails then try "code-server {filename}" to open it up. I need this because sometimes I am using the web IDE which needs code-server and other times i am using just the regular IDE that accepts code. Can you help me with this?
