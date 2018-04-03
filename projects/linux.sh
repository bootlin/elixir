# Elixir definitions for Linux

list_tags_h()
{
    echo "$tags" |
    tac |
    sed -r 's/^(((v2.6)\.([0-9]*)(.*))|(v[0-9])\.([0-9]*)(.*))$/\3\6 \3\6.\4\7 \3\6.\4\7\5\8/'
}
