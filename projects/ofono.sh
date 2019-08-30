# Elixir definitions for Ofono

list_tags_h()
{
    echo "$tags" |
    tac |
    sed -r 's/^([0-9]*)\.([0-9]*)(.*)$/v\1 v\1.\2 \1.\2\3/'
}
