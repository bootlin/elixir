# Elixir definitions for Freertos

list_tags_h()
{

    echo "$tags" |
    grep -v '_Major' |
    tac |
    sed -r 's/^(v[0-9])\.([0-9]*)(.*)$/\1 \1.\2 \1.\2\3/'

    echo "$tags" |
    grep '_Major' |
    tac |
    sed -r 's/^(.*)(_Major)$/other \1 \1\2/'
}
