{
  description = "Official reusable Transit application packages";

  inputs = {
    transit-upstream.url = "github:spoke-sh/transit/f31673bbd0fa599c9d2bd98c2ceb47d328c19ae6";
    transitc-upstream.url = "github:spoke-sh/transitc/0dd62605005bec8c0fbb4c1b691bc635c3512244";
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
                transitc build
                transitc test
                touch "$out"
              '';
        }
      );

      formatter = forAllSystems (system: (toolsFor system).pkgs.nixfmt);
    };
}
