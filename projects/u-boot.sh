# Elixir definitions for U-Boot

list_tags_h()
{
    echo "$tags" |
    grep '^v20' |
    tac |
    sed -r 's/^(v20..)(.*)$/new \1 \1\2/'

    echo "$tags" |
    grep -E '^(v1|U)' |
    tac |
    sed -r 's/^/old by-version /'

    echo "$tags" |
    grep -E '^(LABEL|DENX)' |
    tac |
    sed -r 's/^/old by-date /'
}
