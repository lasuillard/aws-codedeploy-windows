from pulumi import Config

config = Config()

repository_fullname = config.get("github-repository-fullname")
