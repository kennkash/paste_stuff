export FZF_DEFAULT_OPTS="\
--style=full \
--border --padding 1,2 \
--border-label ' Demo ' --input-label ' Input ' --header-label ' File Type ' \
--preview 'fzf-preview.sh {}' \
--bind 'result:transform-list-label:
  if [[ -z $FZF_QUERY ]]; then
    echo \" $FZF_MATCH_COUNT items \"
  else
    echo \" $FZF_MATCH_COUNT matches for [$FZF_QUERY] \"
  fi' \
--bind 'focus:transform-preview-label:[[ -n {} ]] && printf \" Previewing [%s] \" {}' \
--bind 'focus:+transform-header:file --brief {} || echo \"No file selected\"' \
--bind 'ctrl-r:change-list-label( Reloading the list )+reload(sleep 2; git ls-files)' \
--color=bg+:#363A4F,bg:#24273A,spinner:#F4DBD6,hl:#ED8796 \
--color=fg:#CAD3F5,header:#ED8796,info:#C6A0F6,pointer:#F4DBD6 \
--color=marker:#B7BDF8,fg+:#CAD3F5,prompt:#C6A0F6,hl+:#ED8796 \
--color=selected-bg:#494D64 \
--color=border:#6E738D,label:#CAD3F5 \
--color=preview-border:#6E738D,preview-label:#CAD3F5 \
--color=list-border:#6E738D,list-label:#CAD3F5 \
--color=input-border:#6E738D,input-label:#CAD3F5 \
--color=header-border:#6E738D,header-label:#CAD3F5 \
"
