{pkgs}: {
  deps = [
    pkgs.xorg.libXrender
    pkgs.xorg.libXext
    pkgs.glib
    pkgs.libGL
    pkgs.xorg.libX11
    pkgs.xorg.libxcb
  ];
}
