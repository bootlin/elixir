// SPDX-License-Identifier: CC0-1.0
// This file is the situation of #186, but with documentation.

#ifdef SOMETHING
/**
 * i186c_fn1 - do something
 */
static int i186c_fn1(struct platform_device *pdev)
{
}
#else
#define i186c_fn1	NULL
#endif

#ifdef SOMETHING
static int i186c_fn2(struct platform_device *pdev)
{
}
#else
/**
 * i186c_fn2 - do something
 */
#define i186c_fn2	NULL
#endif
