# Elixir definitions for OP-TEE Trusted OS

list_tags_h()
{
    echo "$tags" |
    grep '^[0-9]\.' |
    tac |
    sed -r 's/^([0-9]*)\.([0-9]*)(.*)$/v\1 \1.\2 v\1.\2\3/'
}

list_tags()
{
    echo "$tags" |
    grep '^[0-9]\.'
}

get_latest()
{
    git tag | grep '^[0-9]\.' | grep -v '\-rc' | sort -V | tail -n 1
}
