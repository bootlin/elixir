import re
from urllib import parse
import falcon

from .lib import validFamily

def validate_project(project):
    if project is not None and re.match(r'^[a-zA-Z0-9_.,:/-]+$', project):
        return project.strip()

# Validates and unquotes project parameter
class ProjectConverter(falcon.routing.BaseConverter):
    def convert(self, value: str):
        value = parse.unquote(value)
        project = validate_project(value)
        if project is None:
            raise falcon.HTTPBadRequest('Error', 'Invalid project name')
        return project

def validate_version(version):
    if version is not None and re.match(r'^[a-zA-Z0-9_.,:/-]+$', version):
        return version.strip()

# Validates and unquotes version parameter
class VersionConverter(falcon.routing.BaseConverter):
    def convert(self, value: str):
        value = parse.unquote(value)
        version = validate_version(value)
        if version is None:
            raise falcon.HTTPBadRequest('Error', 'Invalid version name')
        return version

def validate_ident(ident):
    if ident is not None and re.match(r'^[A-Za-z0-9_,.+?#-]+$', ident):
        return ident.strip()

# Validates and unquotes identifier parameter
class IdentConverter(falcon.routing.BaseConverter):
    def convert(self, value: str):
        value = parse.unquote(value)
        return validate_ident(value)

# Returns default family if family is not valid
class FamilyConverter(falcon.routing.BaseConverter):
    def convert(self, value: str):
        value = parse.unquote(value)
        if not validFamily(value):
            value = 'C'
        return value

