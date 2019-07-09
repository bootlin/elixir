# Elixir definitions for Amazon FreeRTOS

list_tags_h()
{

    echo "$tags" |
    grep '_Major' |
    tac |
    sed -r 's/^(.*)(_Major)$/new \1 \1\2/'

    echo "$tags" |
    grep -v '_Major' |
    tac |
    sed -r 's/^(v[0-9]*)\.([0-9]*)(.*)$/\1 \1.\2 \1.\2\3/'
}

get_latest()
{
    git tag | grep '^20' | sort -V | tail -n 1
}
