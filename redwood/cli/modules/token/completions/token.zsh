if [[ ! -o interactive ]]; then
    return
fi

compctl -K _token token

_token() {
  local word words completions
  read -cA words
  word="${words[2]}"

  if [ "${#words}" -eq 2 ]; then
    completions="$(token commands)"
  else
    completions="$(token completions "${word}")"
  fi

  reply=("${(ps:\n:)completions}")
}
