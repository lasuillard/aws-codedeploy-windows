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
            graphviz
            pulumi-bin
            awscli2
            pulumiPackages.pulumi-python
          ];

          shellHook = ''
            export LD_LIBRARY_PATH="${
              pkgs.lib.makeLibraryPath [
                pkgs.stdenv.cc.cc.lib
                pkgs.libxcb
                pkgs.libX11
                pkgs.libGL
                pkgs.glib.out
              ]
            }''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

            pre-commit install

            # Workaround for pre-commit leaking its dependencies into the environment
            unset PYTHONPATH
          '';
        };
      }
    );
}
