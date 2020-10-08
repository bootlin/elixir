/*
 * issue134.c: tests exhibiting problems noted in
 * https://github.com/bootlin/elixir/issues/134#issue-624392766
 *
 * t/tree/issue134.c
 * SPDX-License-Identifier: CC0-1.0
 */

/**
 * issue134_function1:
 *	Do something magical
 *	and something quotidian
 *
 * @p1: Param
 *
 * Do something
 *
 * Returns whatever
 */
int issue134_function1(int p1)
{
    write_test_cases();
}

/**
 * issue134_function2: - does what it does
 * @param:  something
 *
 * Whatever
 *
 * Whatever, paragraph 2.
 */
void __sched issue134_function2(struct completion *x)
{
	take_action();
}

/**
 * issue134_function3() - something
 * @param: whatever
 * @paramii: whatever else
 *
 * Description
 *
 * Return: %magic or
 *	   %-EIEIO if the farm bought
 */
int issue134_function3(struct issue134_struct1 *param,
			       struct issue134_struct2 *paramii);
