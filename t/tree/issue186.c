// SPDX-License-Identifier: CC0-1.0
// This file triggers the bug described in #186.

#ifdef SOMETHING
static int undocumented_function(struct platform_device *pdev)
{
}

#else
#define undocumented_function	NULL
#endif
