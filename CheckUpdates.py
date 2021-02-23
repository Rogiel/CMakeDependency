import json, sys
from urllib.parse import urlparse
import requests
from github import Github

j = json.load(open('dependencies.json'))
github = Github()

for (name, dep_info) in j.items():
    # sys.stderr.write('Checking dependency definitions for ' + name + '\n')
    if "git" in dep_info:
        git_info = dep_info["git"]
        git_repo = git_info["repository"]
        git_tag = git_info["tag"]

        git_url_parsed = urlparse(git_repo)
        if git_url_parsed.hostname == 'github.com':
            parts = git_url_parsed.path.split("/")
            user = parts[1]
            repo = parts[2]
            repo = repo[:-4] if repo.endswith('.git') else repo

            gh_repo = github.get_repo(user + '/' + repo)
            tags = gh_repo.get_tags()

            latest_tag = tags[0] if tags.totalCount > 0 else None
            if latest_tag is not None:
                if latest_tag.name != git_tag:
                    print('Upgrade {name} from {old_version} to {new_version}'.format(name=name, old_version=git_tag, new_version=latest_tag.name))

        else:
            print('git is only supported for github repositories at the moment.', file=sys.stderr)
            exit(-1)

