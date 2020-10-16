// SPDX-License-Identifier: CC0-1.0
// This file triggers the bug described in #188.

static int undocumented_function(struct platform_device *pdev)
{
    int foo;
    #define BAR (42)
    foo=1;
    return foo;
}
