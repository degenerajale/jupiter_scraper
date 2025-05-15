{ pkgs }: {
  deps = [
    pkgs.python310Full
    pkgs.python310Packages.setuptools
    pkgs.python310Packages.wheel
    pkgs.python310Packages.pip
  ];
}
