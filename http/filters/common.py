# Common filters

def encode_number(number):
    result = ''

    while number != 0:
        number, rem = divmod(number, 10)

        rem = chr(ord('A') + rem)

        result = rem + result

    return result


def decode_number(string):
    result = ''

    while string != '':
        string, char = string[:-1], string[-1]

        char = str(ord(char) - ord('A'))

        result = char + result

    return int(result)


filters = []
exec(open('dtscomp.py').read())
exec(open('ident.py').read())
exec(open('cppinc.py').read())
