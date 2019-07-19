# Elixir definitions for LLVM

list_tags_h()
{
    echo "$tags" |
    tac |
    sed -r 's/^llvmorg-([0-9]*)\.([0-9]*)(.*)$/\1 \1.\2 llvmorg-\1.\2\3/'
}
