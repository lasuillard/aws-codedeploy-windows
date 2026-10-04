import pulumi_aws as aws
import pulumi_github as github
import pulumi_tls as tls
from pulumi import Output, log
from pulumi_github.get_repository import AwaitableGetRepositoryResult

import common
import config
import deployment
import deployment_artifact
from components.iam import Role


def _create_resources(repository_fullname: str) -> None:
    repository: AwaitableGetRepositoryResult = github.get_repository(
        full_name=repository_fullname
    )
    certificate = tls.get_certificate(
        url=f"https://{common.gha_oidc_provider_domain}/.well-known/openid-configuration",
    )

    # GitHub Actions OIDC
    aws.iam.OpenIdConnectProvider(
        "github-actions",
        url=f"https://{common.gha_oidc_provider_domain}",
        thumbprint_lists=[
            # https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc_verify-thumbprint.html
            certificate.certificates[0].sha1_fingerprint,
        ],
        client_id_lists=["sts.amazonaws.com"],
    )
    gha_oidc_role = (
        Role(
            "github-actions",
            name_prefix="GitHub-Actions-",
        )
        .assumable_with_oidc(
            common.gha_oidc_provider_domain,
            oidc_subjects_with_wildcards=[
                Output.format(
                    "repo:{full_name}:*",
                    full_name=repository.full_name,
                ),
            ],
        )
        .with_policies(
            documents=[
                aws.iam.get_policy_document(
                    statements=[
                        aws.iam.GetPolicyDocumentStatementArgsDict(
                            sid="UploadBundle",
                            effect="Allow",
                            actions=["s3:PutObject", "s3:AbortMultipartUpload"],
                            resources=[
                                Output.concat(
                                    deployment_artifact.build_artifacts.arn, "/*"
                                )
                            ],  # ty: ignore[invalid-argument-type]
                        ),
                        aws.iam.GetPolicyDocumentStatementArgsDict(
                            sid="ReadDeployments",
                            effect="Allow",
                            actions=[
                                "codedeploy:GetDeployment",
                                "codedeploy:GetDeploymentConfig",
                            ],
                            resources=["*"],
                        ),
                        aws.iam.GetPolicyDocumentStatementArgsDict(
                            sid="CreateDeployment",
                            effect="Allow",
                            actions=["codedeploy:CreateDeployment"],
                            resources=[deployment.deployment_group.arn],  # ty: ignore[invalid-argument-type]
                        ),
                        aws.iam.GetPolicyDocumentStatementArgsDict(
                            sid="Revisions",
                            effect="Allow",
                            actions=[
                                "codedeploy:GetApplicationRevision",
                                "codedeploy:RegisterApplicationRevision",
                            ],
                            resources=[deployment.app.arn],  # ty: ignore[invalid-argument-type]
                        ),
                    ]
                ),
            ]
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
        "AWS_REGION": aws.get_region().region,
        "S3_BUCKET": deployment_artifact.build_artifacts.bucket,
        "CODEDEPLOY_APPLICATION_NAME": deployment.app.name,
        "CODEDEPLOY_DEPLOYMENT_GROUP_NAME": deployment.deployment_group.deployment_group_name,
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


if config.repository_fullname:
    _create_resources(config.repository_fullname)
else:
    log.warn("GitHub repository is not provided, skip provisioning relevant resources.")
