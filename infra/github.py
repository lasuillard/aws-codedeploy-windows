from __future__ import annotations

import pulumi_aws as aws
import pulumi_github as github
import pulumi_tls as tls
from pulumi import Config, Output, log

from . import codedeploy, codedeploy_application, components, metadata

config = Config()

repository_fullname = config.get("github-repository-fullname")


def main() -> None:
    repository = github.get_repository(full_name=repository_fullname)
    certificate = tls.get_certificate(
        url=f"https://{metadata.gha_oidc_provider_domain}/.well-known/openid-configuration",
    )

    # Create GitHub OIDC provider if not exists
    try:
        aws.iam.get_open_id_connect_provider(
            url=f"https://{metadata.gha_oidc_provider_domain}"
        )
    except Exception as err:
        if "not found" not in str(err):
            raise

        _gha_oidc_provider = aws.iam.OpenIdConnectProvider(
            "github-actions",
            url=f"https://{metadata.gha_oidc_provider_domain}",
            thumbprint_lists=[
                # https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc_verify-thumbprint.html
                certificate.certificates[0].sha1_fingerprint,
            ],
            client_id_lists=["sts.amazonaws.com"],
        )

    gha_oidc_role = (
        components.Role(
            "github-actions",
            name_prefix="GitHub-Actions-",
        )
        .assumable_with_oidc(
            metadata.gha_oidc_provider_domain,
            oidc_subjects_with_wildcards=[
                Output.format(
                    "repo:{full_name}:*",
                    full_name=repository.full_name,
                ),
            ],
        )
        .with_policies(
            arns=[
                # TODO(lasuillard): Limit the permissions to mandatory permissions
                aws.iam.ManagedPolicy.ADMINISTRATOR_ACCESS
            ],
        )
        .build()
    )

    # Deployment environment
    environment = github.RepositoryEnvironment(
        "codedeploy",
        repository=repository.name,
        environment="codedeploy",
        deployment_branch_policy={
            "protected_branches": False,
            "custom_branch_policies": True,
        },
    )
    github.RepositoryEnvironmentDeploymentPolicy(
        "codedeploy",
        repository=repository.name,
        environment=environment.environment,
        branch_pattern=repository.default_branch,
    )

    # Actions variables
    for key, value in {
        "AWS_REGION": aws.get_region().name,
        "S3_BUCKET": codedeploy.build_artifacts.bucket,
        "CODEDEPLOY_APPLICATION_NAME": codedeploy_application.app.name,
        "CODEDEPLOY_DEPLOYMENT_GROUP_NAME": codedeploy_application.deployment_group.deployment_group_name,
    }.items():
        github.ActionsEnvironmentVariable(
            key,
            repository=repository.name,
            environment=environment.environment,
            variable_name=key,
            value=value,
        )

    # Actions secrets
    for key, value in {
        "AWS_ROLE_TO_ASSUME": gha_oidc_role.arn,
    }.items():
        github.ActionsEnvironmentSecret(
            key,
            repository=repository.name,
            environment=environment.environment,
            secret_name=key,
            plaintext_value=value,
        )


if repository_fullname:
    main()
else:
    log.warn("GitHub repository is not provided, skip provisioning relevant resources.")
