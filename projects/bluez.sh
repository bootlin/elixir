# Elixir definitions for BlueZ
list_tags()
{
    echo "$tags" |
    grep '^[0-9]'
}

list_tags_h()
{
    echo "$tags" |
    grep '^[0-9]' |
    sed -r 's/^([0-9]*)\.([0-9]*)$/v\1 v\1.\2 \1.\2/'
}

get_latest()
{
    git tag | grep '^[0-9]\.' | sort -V | tail -n 1
}
