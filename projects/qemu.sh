# Elixir definitions for QEMU

list_tags_h()
{
    echo "$tags" |
    grep -E "^v[0-9].*" |
    tac |
    sed -r 's/^(v[0-9])\.([0-9]*)(.*)$/\1 \1.\2 \1.\2\3/'

    echo "$tags" |
    grep "release" |
    tac |
    sed -r 's/^(release)_([0-9_]*)$/old \1 \1_\2/'

    echo "old initial initial"
}
