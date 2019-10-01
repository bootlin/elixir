# Elixir definitions for Amazon FreeRTOS

list_tags_h()
{

    echo "$tags" |
    grep -v '^v' |
    tac |
    sed -r 's/^([0-9][0-9][0-9][0-9])([0-9][0-9])(.*)$/\1 \1\2 \1\2\3/'

    echo "$tags" |
    grep '^v' |
    tac |
    sed -r 's/^(v[0-9]*)\.([0-9]*)(.*)$/\1 \1.\2 \1.\2\3/'
}

get_latest()
{
    git tag | grep '^20' | sort -V | tail -n 1
}
