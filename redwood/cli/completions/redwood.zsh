if [[ ! -o interactive ]]; then
    return
fi

compctl -K _redwood redwood

_redwood() {
  local word words completions
  read -cA words
  word="${words[2]}"

  if [ "${#words}" -eq 2 ]; then
    completions="$(redwood commands)"
  else
    completions="$(redwood completions "${word}")"
  fi

  reply=("${(ps:\n:)completions}")
}
