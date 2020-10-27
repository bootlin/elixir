/* t/tree/issue192.c */
/* SPDX-License-Identifier: CC0-1.0 */
/* This file triggers the bug described in #192. */

/**
 * issue192a: - do something
 **/
int
issue192a(const struct foo **bar, const char *bat,
         struct baz *quux)
{
    return 0;
}

/**
 * issue192b()
 *
 * Allow an uppercase return type
 */
AMAZING_RETURN_TYPE
issue192b(void *parameter)
{
    return (AMAZING_RETURN_TYPE)31337;
}
