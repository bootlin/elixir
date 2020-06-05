# Elixir definitions for Barebox

# Enable DT bindings compatible strings support
dts_comp_support=1

list_tags_h()
{
    echo "$tags" |
    grep '^v20' |
    tac |
    sed -r 's/^(v20..)\.([0-9][0-9])\.(.*)$/\1 \1.\2 \1.\2.\3/'

    echo "$tags" |
    grep '^v2\.0' |
    tac |
    sed -r 's/^(v2\.0)(.*)$/old \1 \1\2/'

    echo "$tags" |
    grep '^freescale' |
    tac |
    sed -r 's/^(freescale)(.*)$/old \1 \1\2/'
}
