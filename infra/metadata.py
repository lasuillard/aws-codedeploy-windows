from pulumi import get_project, get_stack

project, env = get_project(), get_stack()

name = project
full_name = f"{project}-{env}"

# GitHub
gha_oidc_provider_domain = "token.actions.githubusercontent.com"
