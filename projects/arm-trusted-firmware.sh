# Elixir definitions for Arm Trusted Firmware
# https://github.com/ARM-software/arm-trusted-firmware

list_tags_h()
{
    echo "$tags" |
    grep -v 'for-v0\.4' |
    tac |
    sed -r 's/^(v[0-9]*)\.([0-9]*)(.*)$/\1 \1.\2 \1.\2\3/'

    echo "$tags" |
    grep 'for-v0\.4' |
    tac |
    sed -r 's/^/custom for-v0.4 /'
}
