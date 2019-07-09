# Elixir definitions for BusyBox

version_dir()
{
    tr '_.' '._';
}

version_rev()
{
    tr '._' '_.';
}

list_tags_h()
{
    echo "$tags" |
    tac |
    sed -r 's/^([0-9]*)\.([0-9]*)(.*)$/v\1 \1.\2 \1.\2\3/'
}

