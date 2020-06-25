# Filter for kconfig identifier in defconfigs

defconfigidents = []

def keep_defconfigidents(m):
    defconfigidents.append(m.group(1))
    return '__KEEPDEFCONFIGIDENTS__' + encode_number(len(defconfigidents))

def replace_defconfigidents(m):
    i = defconfigidents[decode_number(m.group(1)) - 1]

    return '<a href="'+version+'/K/ident/'+i+'">'+i+'</a>'

defconfigident_filters = {
                'case': 'filename_extension',
                'match': {'defconfig'},
                'prerex': '(CONFIG_[\w]+)',
                'prefunc': keep_defconfigidents,
                'postrex': '__KEEPDEFCONFIGIDENTS__([A-J]+)',
                'postfunc': replace_defconfigidents
                }

filters.append(defconfigident_filters)
