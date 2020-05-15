# Filter for symbolic links

symlinks = []

def keep_symlinks(m):
    dir_name = os.path.dirname(path)
    rel_path = m.group(1)

    if dir_name != '/':
        dir_name += '/'

    full_path = os.path.abspath(dir_name + rel_path)

    if query('exist', tag, full_path):
        symlinks.append((full_path, rel_path))
        return '__KEEPSYMLINKS__' + encode_number(len(symlinks)) + m.group(2)
    else:
        return m.group(0)

def replace_symlinks(m):
    w, n = symlinks[decode_number(m.group(1)) - 1]
    return '<a href="'+version+'/source'+w+'">'+n+'</a>'

symlinks_filters = {
                'case': 'any',
                'prerex': '((?:\.\./)+[-\w/]+/[-\w\.]+)(\s+|$)',
                'prefunc': keep_symlinks,
                'postrex': '__KEEPSYMLINKS__([A-J]+)',
                'postfunc': replace_symlinks
                }

filters.append(symlinks_filters)
