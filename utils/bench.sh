#!/bin/sh

oha="oha -z5s -c10 -r0 --json"
host="$1"

if test -z "$host"; then
    >&2 echo "usage: $0 <host>"
    exit 1
fi

run()
{
    url="$1"
    res="$($oha "$host$url")"

    if echo "$res" | jq -e '.summary.successRate != 1.0' > /dev/null; then
        >&2 echo "some requests failed, please investigate $url"
        exit 1
    fi

    printf "%7.2f\t%s\n" "$(echo "$res" | jq -r '.summary.requestsPerSec')" "$url"
}

# Stats are something like 54% .c/.h rendering and .42% ident pages.
# Directories, autocomplete and others are insignifiant.

run "/linux/v5.15.48/C/ident/ENOKEY"
run "/linux/v6.13-rc3/source/drivers/clk/clk-eyeq.c"
run "/linux/latest/C/ident/ENOKEY"
run "/linux/v6.12.6/source"
run "/linux/v5.11.20/source/drivers/net/ethernet/hisilicon/hns/hnae.c"
run "/linux/v4.5-rc5/source/drivers/scsi/lpfc/lpfc_sli.c"
