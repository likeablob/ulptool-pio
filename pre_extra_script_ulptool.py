# Copyright (c) likeablob
# SPDX-License-Identifier: MIT
import os
from pathlib import Path

from SCons.Node import FS
from SCons.Script import Import

Import("env", "env")
env = globals()["env"]  # For flake8

project_dir = Path(env["PROJECT_DIR"])
ulptool_dir = Path(env["PROJECT_LIBDEPS_DIR"]) / env["PIOENV"] / "ulptool-pio"

# Add linker flags
env.Append(LINKFLAGS=["-L", "ulp", "-T", "ulp_main.ld", "ulp/ulp_main.bin.bin.o"])

# Add values for -I and -D
env.Append(
    CPPPATH=[
        project_dir / "ulp",
        ulptool_dir / "src/include/ulptool",
        ulptool_dir / "src/ulpcc/include",
    ],
    CPPDEFINES=[("_ULPCC_", 1)],
)


def skip_ulp_s(node: FS.Dir):
    if str(node.get_dir().name) == "ulp":
        return None

    return node


# Exclude ./ulp/*.s because they should be handled by ulptool.
# Note that, however, here we let ./ulp/*.c files be compiled by the default toolchain
# just for the build-time dependency tracking.
# All the ulp/*.o will be overwritten by ulptool afterwards.
env.AddBuildMiddleware(skip_ulp_s, "*.s")

# Add ./ulp/ as a BuildSource. This triggers the middleware above.
env.BuildSources(os.path.join("$BUILD_DIR", "ulp"), os.path.join("$PROJECT_DIR", "ulp"))
