export FZF_DEFAULT_OPTS="\
--color=bg+:#363A4F,bg:#24273A,spinner:#F4DBD6,hl:#ED8796 \
--color=fg:#CAD3F5,header:#ED8796,info:#C6A0F6,pointer:#F4DBD6 \
--color=marker:#B7BDF8,fg+:#CAD3F5,prompt:#C6A0F6,hl+:#ED8796 \
--color=selected-bg:#494D64 \
--color=border:#6E738D,label:#CAD3F5 \
"

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

  [[ -n "$file" ]] && code-server "$file"
}


# fhe - repeat history edit
writecmd (){ perl -e 'ioctl STDOUT, 0x5412, $_ for split //, do{ chomp($_ = <>); $_ }' ; }

fhe() {
  local cmd
  cmd=$(
    history |
      fzf +s --tac |
      sed -E 's/^[[:space:]]*[0-9]+[[:space:]]+//'
  ) || return

  [[ -n $cmd ]] || return

  # Replace the current readline buffer
  READLINE_LINE="$cmd"
  READLINE_POINT=${#READLINE_LINE}
}


fkill_listen() {
  local sig="${1:-9}"
  local pids

  pids=$(
    ss -ltnp 2>/dev/null | tail -n +2 |
      fzf -m --prompt='LISTEN> ' --header='Select listener(s) to kill' |
      sed -nE 's/.*pid=([0-9]+).*/\1/p' |
      sort -u
  ) || return

  [[ -n "$pids" ]] && echo "$pids" | xargs -r kill -"${sig}"
}



