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
    sort -rV |
    sed -E 's/^([0-9]*)\.([0-9]*)$/v\1 v\1.\2 \1.\2/'
}

get_latest_tags()
{
    git tag | grep '^[0-9]\.' | sort -Vr
}
