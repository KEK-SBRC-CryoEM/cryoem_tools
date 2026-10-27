# Bash completion for cspa (loaded by the modulefile).
# Based on: https://opensource.com/article/18/3/creating-bash-completion-script

_cspa_completions(){
    # guard: CSPA_ROOT not set and to prevent repeated suggestions
    local dir="${CSPA_ROOT:-}/src/spa/analyses"
    if [[ ! -d $dir || ${#COMP_WORDS[@]} != 2 ]]; then
        return  
    fi

    # get available scripts
    local f names=""
    for f in "$dir"/*.py; do
        f=${f##*/}; f=${f%.py}
        [[ $f == _* ]] || names+=" $f" # ignore _*.py, __init__
    done

    # generate completion and filter based on what user has already typed
    COMPREPLY=($(compgen -W "$names" -- "${COMP_WORDS[1]}"))
}

complete -F _cspa_completions cspa
