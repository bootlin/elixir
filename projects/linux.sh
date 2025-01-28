# Elixir definitions for Linux

# Enable DT bindings compatible strings support
dts_comp_support=1

get_tags()
{
    git tag |
    version_dir |
    sed -r 's/^(pre|lia64-|)(v?[0-9\.]*)(pre|-[^pf].*?|)(alpha|-[pf].*?|)([0-9]*)(.*?)$/\2#\3@\4@\5@\60@\1.0/' |
    sort -V |
    sed -r 's/^(.*?)#(.*?)@(.*?)@(.*?)@(.*?)0@(.*?)\.0$/\6\1\2\3\4\5/' |
    head -n1000
}

list_tags_h()
{
    echo "$tags" |
    tac |
    sed -r 's/^(pre|lia64-|)(v?)([0-9]*)\.([0-9]*)(.*)$/v\3 v\3.\4 \1\2\3.\4\5/'
}
