# Elixir definitions for U-Boot

# Enable DT bindings compatible strings support
dts_comp_support=1

list_tags_h()
{
    echo "$tags" |
    grep '^v20' |
    tac |
    sed -r 's/^(v20..)\.([0-9][0-9])(.*)$/\1 \1.\2 \1.\2\3/'

    echo "$tags" |
    grep -E '^(v1|U)' |
    tac |
    sed -r 's/^/old by-version /'

    echo "$tags" |
    grep -E '^(LABEL|DENX)' |
    tac |
    sed -r 's/^/old by-date /'
}
