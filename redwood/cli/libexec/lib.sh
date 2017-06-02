# Usage: peek_env prop
#   Peek at redwood .env property $prop and print value
function peek_env() {
    prop="$1"
    cat "${_REDWOOD_ROOT}/../.env" | grep "^${prop}=" | cut -d= -f 2-
}
