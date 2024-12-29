import re
from typing import List

from .filters.utils import Filter, FilterContext
from .filters import default_filters
from .projects import projects
from .lexers import default_lexers

# Returns a list of applicable filters for project_name under provided filter context
def get_filters(ctx: FilterContext, project_name: str) -> List[Filter]:
    project_config = projects.get(project_name)
    if project_config is None or 'filters' not in project_config:
        filter_classes = default_filters 
    else:
        filter_classes = project_config['filters']

    filters = []

    for filter_cls in filter_classes:
        if type(filter_cls) == tuple and len(filter_cls) == 2:
            cls, kwargs = filter_cls
            filters.append(cls(**kwargs))
        elif type(filter_cls) == type:
            filters.append(filter_cls())
        else:
            raise ValueError(f"Invalid filter: {filter_cls}, " \
                    "should be either a two element tuple or a type. " \
                    "Make sure project_filters in project.py is valid.")

    return [f for f in filters if f.check_if_applies(ctx)]

def get_lexer(path: str, project_name: str):
    project_config = projects.get(project_name)
    if project_config is None or 'lexers' not in project_config:
        lexers = default_lexers
    else:
        lexers = project_config['lexers']

    path = path.lower()
    for regex, lexer in lexers.items():
        if re.match(regex, path):
            if type(lexer) == tuple:
                lexer_cls, kwargs = lexer
                return lambda code: lexer_cls(code, **kwargs)
            else:
                return lambda code: lexer(code)

