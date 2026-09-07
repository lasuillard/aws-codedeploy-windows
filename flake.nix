{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        packages = {
          # Tools used in CI/CD pipelines
          inherit (pkgs)
            ;
        };

        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            pre-commit
            just
            uv
            pulumi-bin
            awscli2
            pulumiPackages.pulumi-python
          ];

          shellHook = ''
            pre-commit install

            # Workaround for pre-commit leaking its dependencies into the environment
            unset PYTHONPATH
          '';
        };
      }
    );
}
