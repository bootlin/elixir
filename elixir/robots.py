from itertools import islice
import falcon

from .web_utils import get_projects
from .query import get_query

# NOTE: remember to keep this up to date. This dict should contain older than latest versions 
# that are relevant to most developers
STATIC_PROJECT_VERSIONS = {
        "linux": ["v6.12", "v6.6", "v6.1", "v5.15", "v5.10", "v5.4", "v2.6.39.4"],
}

class RobotsResource:
    def on_get(self, req, resp):
        template = req.context.jinja_env.get_template('robots.txt')
        projects = {}
        for (project, _) in get_projects(req.context.config.project_dir):
            query = get_query(req.context.config.project_dir, project)
            if query is not None:
                latest_three = [tag.decode() for tag in islice(query.get_latest_tags(), 3)]
                projects[project] = STATIC_PROJECT_VERSIONS.get(project, []) + latest_three + ["latest"]
                query.close()

        resp.text = template.render({"projects": projects}) 
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_TEXT

