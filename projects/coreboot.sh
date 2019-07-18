# Elixir definitions for Coreboot

list_tags_h()
{
    echo "$tags" |
    tac |
    sed -r 's/^([0-9]*)\.([0-9]*)(.*)$/\1 \1.\2 \1.\2\3/'
}
