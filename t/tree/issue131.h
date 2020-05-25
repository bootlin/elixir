/* This file triggers the bug described in #131. */

/**
 * struct class - structure
 * @member:     A member
 *
 * Description.
 */
struct class {
    int member;
};

void foo(struct class *klass)
{
    klass->member = 42;
}

/* t/tree/issue131.c */
/* SPDX-License-Identifier: CC0-1.0 */
