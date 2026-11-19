{
  description = "Official reusable Transit application packages";

  inputs = {
    transit-upstream.url = "github:spoke-sh/transit/c1f2680d9353175e58ad503e750e7b4da76a84c5";
    transitc-upstream.url = "github:spoke-sh/transitc/61536eaa510e2ba8826c08b4f41072ed66f41ed5";
    nixpkgs.follows = "transit-upstream/nixpkgs";
  };

  outputs =
    {
      nixpkgs,
      transit-upstream,
      transitc-upstream,
      ...
    }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
      toolsFor = system: {
        pkgs = import nixpkgs { inherit system; };
        transit = transit-upstream.packages.${system}.transit;
        transitc = transitc-upstream.packages.${system}.transitc;
      };
    in
    {
      devShells = forAllSystems (
        system:
        let
          inherit (toolsFor system) pkgs transit transitc;
        in
        {
          default = pkgs.mkShellNoCC {
            packages = [
              transit
              transitc
              pkgs.just
              pkgs.git
              pkgs.nixfmt
              pkgs.python3
            ];
          };
        }
      );

      checks = forAllSystems (
        system:
        let
          inherit (toolsFor system) pkgs transit transitc;
        in
        {
          format =
            pkgs.runCommand "tpackages-format-check"
              {
                nativeBuildInputs = [
                  pkgs.nixfmt
                  pkgs.just
                ];
              }
              ''
                cp ${./flake.nix} flake.nix
                cp ${./justfile} justfile
                nixfmt --check flake.nix
                just --fmt --check
                touch "$out"
              '';
          bootstrap =
            pkgs.runCommand "tpackages-bootstrap-check"
              {
                nativeBuildInputs = [
                  transit
                  transitc
                  pkgs.just
                ];
              }
              ''
                cp -r ${./tests/bootstrap}/. .
                chmod -R u+w .
                transitc --help
                transitc --version
                transit build
                transit test
                touch "$out"
              '';
        }
      );

      formatter = forAllSystems (system: (toolsFor system).pkgs.nixfmt);
    };
}
