/* Function memset should be located as a definition --- #150. */

#include <asm/assembler.h>

    .text

ENTRY(memset)
    nop
ENDPROC(memset)

/* t/tree/issue150.S */
/* SPDX-License-Identifier: CC0-1.0 */
