# aws-codedeploy-windows

[![CI](https://github.com/lasuillard/aws-codedeploy-windows/actions/workflows/ci.yaml/badge.svg)](https://github.com/lasuillard/aws-codedeploy-windows/actions/workflows/ci.yaml)
[![Dev Container](https://github.com/lasuillard/aws-codedeploy-windows/actions/workflows/devcontainer.yaml/badge.svg)](https://github.com/lasuillard/aws-codedeploy-windows/actions/workflows/devcontainer.yaml)
[![codecov](https://codecov.io/gh/lasuillard/aws-codedeploy-windows/graph/badge.svg?token=iKNLWbgUtD)](https://codecov.io/gh/lasuillard/aws-codedeploy-windows)

Example deploying a Python application to AWS Windows EC2 instances with CodeDeploy.

## 🏗️ Provisioning Infrastructure

1. Move to the `infra` directory:

    ```bash
    cd infra
    ```

2. Install infra dependencies:

    ```bash
    uv sync --group infra
    ```

3. Configure AWS credentials

    ```bash
    aws configure
    ```

4. Log in to GitHub CLI (if you want to manage GitHub resources):

    ```bash
    gh auth login --skip-ssh-key
    ```

    Follow the prompts to authenticate with your GitHub account.

5. Configure Pulumi local backend

    ```bash
    pulumi login
    ```

    Or, login to a local backend if you prefer not to use the Pulumi service:

    ```bash
    pulumi login --local
    ```

6. Set up stack:

    ```bash
    pulumi stack init dev
    ```

    And if you want to provision GitHub resources (environment, CI secrets & variables, etc.), set config:

    ```bash
    pulumi config set github-repository-fullname <your-github-username>/<your-repository-name>
    ```

7. Provision the infrastructure:

    ```bash
    pulumi up
    ```

8. Do something with the infrastructure, such as deploying an application or testing the setup.

9. Clean up the resources & delete the stack when you are done:

    ```bash
    pulumi destroy
    pulumi stack rm dev
    ```
