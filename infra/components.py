from abc import ABC, abstractmethod
from collections.abc import Awaitable, Sequence
from typing import Any, Self
from urllib.parse import urlparse

import pulumi_aws as aws
from pulumi import ComponentResource, Input, Inputs, ResourceOptions


class Component(ComponentResource, ABC):
    """Custom base class for all component resources."""

    @property
    @abstractmethod
    def type_(self) -> str:
        """Component resource type."""

    def __init__(  # noqa: D107
        self,
        resource_name: str,
        *,
        props: Inputs | None = None,
        opts: ResourceOptions | None = None,
        remote: bool = False,
        package_ref: Awaitable[str | None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(self.type_, resource_name, props, opts, remote, package_ref)
        self._kwargs = kwargs


class Role(Component):
    """AWS IAM role component."""

    type_ = "custom:aws/iam:Role"

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D107
        super().__init__(*args, **kwargs)

        # AWS context
        self._partition = aws.get_partition().partition
        self._account_id = aws.get_caller_identity().account_id

        # Properties
        self._assume_role_policy = aws.iam.get_policy_document(
            statements=[
                {
                    "actions": ["sts:AssumeRole"],
                    "principals": [{"type": "AWS", "identifiers": ["*"]}],
                },
            ],
        )
        self._policy_arns: Sequence[Input[str]] = ()
        self._policy_documents: Sequence[aws.iam.AwaitableGetPolicyDocumentResult] = ()
        self._policy_attachment_exclusive: bool = True

    def assumable(
        self,
        *,
        role_arns: Sequence[Input[str]] = (),
        services: Sequence[Input[str]] = (),
        actions: Sequence[Input[str]] = ("sts:AssumeRole", "sts:TagSession"),
    ) -> Self:
        """Specify assume role policy for AWS services or roles."""
        self._assume_role_policy = aws.iam.get_policy_document(
            statements=[
                {
                    "effect": "Allow",
                    "principals": [
                        {"type": "AWS", "identifiers": role_arns},
                        {"type": "Service", "identifiers": services},
                    ],
                    "actions": actions,
                },
            ],
        )
        return self

    def assumable_with_oidc(
        self,
        provider_domain_or_url: str,
        *,
        oidc_subjects_with_wildcards: Sequence[Input[str]],
    ) -> Self:
        """Specify assume role policy for OIDC provider."""
        if (url := urlparse(provider_domain_or_url)) and url.hostname:
            provider_domain = str(url.hostname)
        else:
            provider_domain = provider_domain_or_url

        self._assume_role_policy = aws.iam.get_policy_document(
            statements=[
                {
                    "effect": "Allow",
                    "principals": [
                        {
                            "type": "Federated",
                            "identifiers": [
                                f"arn:{self._partition}:iam::{self._account_id}:oidc-provider/{provider_domain}",
                            ],
                        },
                    ],
                    "conditions": [
                        {
                            "test": "StringEquals",
                            "variable": f"{provider_domain}:aud",
                            "values": ["sts.amazonaws.com"],
                        },
                        {
                            "test": "StringLike",
                            "variable": f"{provider_domain}:sub",
                            "values": oidc_subjects_with_wildcards,
                        },
                    ],
                    "actions": ["sts:AssumeRoleWithWebIdentity"],
                },
            ],
        )
        return self

    def with_policies(
        self,
        *,
        arns: Sequence[Input[str]] = (),
        documents: Sequence[dict | aws.iam.AwaitableGetPolicyDocumentResult] = (),
        exclusive: bool = True,
    ) -> Self:
        """Specify policies to attach to the role.

        Args:
            arns: The ARNs of the policies to attach.
            documents: The policy documents to create and attach.
            exclusive: Whether to use exclusive policy attachment.

        """
        self._policy_arns = arns
        self._policy_documents = [
            aws.iam.get_policy_document(**document)
            if isinstance(document, dict)
            else document
            for document in documents
        ]
        self._policy_attachment_exclusive = exclusive
        return self

    def build(self) -> aws.iam.Role:
        """Create and return the IAM role."""
        role = aws.iam.Role(
            self._name,
            opts=ResourceOptions(parent=self),
            assume_role_policy=self._assume_role_policy.json,
            **self._kwargs,
        )

        # Create document policies
        document_policy_arns: list[Input[str]] = []
        for idx, policy_document in enumerate(self._policy_documents):
            policy = aws.iam.Policy(
                f"{self._name}-inline-{idx}",
                opts=ResourceOptions(parent=self),
                policy=policy_document.json,
            )
            document_policy_arns.append(policy.arn)

        # Attach policies
        self._policy_arns = [*self._policy_arns, *document_policy_arns]
        if self._policy_attachment_exclusive:
            aws.iam.RolePolicyAttachmentsExclusive(
                f"{self._name}-attachments",
                opts=ResourceOptions(parent=self),
                role_name=role.name,
                policy_arns=self._policy_arns,
            )
        else:
            for idx, arn in enumerate(self._policy_arns):
                aws.iam.RolePolicyAttachment(
                    f"{self._name}-attachment-{idx}",
                    opts=ResourceOptions(parent=self),
                    role=role.name,
                    policy_arn=arn,
                )

        return role
