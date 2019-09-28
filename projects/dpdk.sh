# Elixir definitions for DPDK

list_tags_h()
{
    echo "$tags" |
    grep -vE '^v1\.|^v2\.' |
    tac |
    sed -r 's/^v([0-9]*)\.([0-9]*)(.*)$/v\1 v\1.\2 v\1.\2\3/'

    echo "$tags" |
    grep -E '^v1\.|^v2\.' |
    tac |
    sed -r 's/^v(1|2)\.([0-9])(.*)$/old v\1.\2 v\1.\2\3/'
}
