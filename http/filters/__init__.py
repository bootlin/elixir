from typing import List

from .utils import Filter, FilterContext
from .projects import project_filters, default_filters

# Retrns a list of applicable filters for project_name under provided filter context
def get_filters(ctx: FilterContext, project_name: str) -> List[Filter]:
    filter_classes = project_filters.get(project_name, default_filters)
    filters = []

    for filter_cls in filter_classes:
        if type(filter_cls) == tuple:
            cls, kwargs = filter_cls
            filters.append(cls(**kwargs))
        elif type(filter_cls) == type:
            filters.append(filter_cls())
        else:
            raise ValueError(f"invalid filter type: {filter}")

    return [f for f in filters if f.check_if_applies(ctx)]

