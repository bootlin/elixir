# Elixir definitions for LLVM

list_tags()
{
    echo "$tags" |
    tac |
    grep ^llvmorg-[0-9]*[\.][0-9]*
}

list_tags_h()
{
    echo "$tags" |
    grep ^llvmorg |
    grep -v init |
    tac |
    sed -r 's/^llvmorg-([0-9]*)\.([0-9]*)(.*)$/v\1 v\1.\2 llvmorg-\1.\2\3/'
}

get_latest_tags()
{
    git tag | grep 'llvmorg' | grep -v init | sort -Vr
}
