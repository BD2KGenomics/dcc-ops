if [[ ! -o interactive ]]; then
    return
fi

compctl -K _project project

_project() {
  local word words completions
  read -cA words
  word="${words[2]}"

  if [ "${#words}" -eq 2 ]; then
    completions="$(project commands)"
  else
    completions="$(project completions "${word}")"
  fi

  reply=("${(ps:\n:)completions}")
}
