# Elixir definitions for Grub

list_tags_h()
{
    echo "$tags" |
    tac |
    sed -r 's/^(grub-)?([0-9]+).([0-9]+)([A-Za-z0-9\.-]*)$/\2 \2.\3 \1\2.\3\4/'
}
