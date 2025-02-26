# Elixir definitions for Zephyr

# Enable DT bindings compatible strings support
dts_comp_support=0

list_tags()
{
    echo "$tags" |
    grep -v '^zephyr-v'
}

list_tags_h()
{
    echo "$tags" |
    grep -v '^zephyr-v' |
    tac |
    sed -r 's/^(v[0-9]*)\.([0-9]*)(.*)$/\1 \1.\2 \1.\2\3/'
}

get_latest_tags()
{
    git tag | grep -v '^zephyr-v' | version_dir | grep -v '\-rc' | sort -Vr
}
