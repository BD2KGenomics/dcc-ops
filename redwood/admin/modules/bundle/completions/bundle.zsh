if [[ ! -o interactive ]]; then
    return
fi

compctl -K _bundle bundle

_bundle() {
  local word words completions
  read -cA words
  word="${words[2]}"

  if [ "${#words}" -eq 2 ]; then
    completions="$(bundle commands)"
  else
    completions="$(bundle completions "${word}")"
  fi

  reply=("${(ps:\n:)completions}")
}
