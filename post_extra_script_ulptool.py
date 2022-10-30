# Copyright (c) likeablob
# SPDX-License-Identifier: MIT
from pathlib import Path

from SCons.Script import COMMAND_LINE_TARGETS, Import

Import("env", "projenv")
env = globals()["env"]
projenv = globals()["projenv"]

# Do not run extra script when IDE fetches C/C++ project metadata
if "idedata" in COMMAND_LINE_TARGETS:
    env.Exit(0)

project_dir = Path(env["PROJECT_DIR"])
ulptool_dir = Path(env["PROJECT_LIBDEPS_DIR"]) / env["PIOENV"] / "ulptool-pio"


def run_ulptool():
    platform = env.PioPlatform()
    board = env.BoardConfig()
    mcu = board.get("build.mcu", "esp32")
    
    framework_dir = platform.get_package_dir("framework-arduinoespressif32")
    toolchain_ulp_dir = platform.get_package_dir("toolchain-%sulp" % (mcu))
    toolchain_xtensa_dir = platform.get_package_dir(
        "toolchain-%s" % ("xtensa-%s" % mcu)
    )

    cpp_defines = ""
    for raw in env["CPPDEFINES"]:
        k = None
        if type(raw) is tuple:
            k, v = raw
            v = v if type(v) is not str else v.replace(" ", r"\ ")
            flag = f"--D{k}={v} "
        else:
            k = raw
            flag = f"--D{k} "

        if k.startswith("ARDUINO"):
            cpp_defines += flag

    # TODO: Rewrite with process.run()
    res = env.Execute(
        f"""$PYTHONEXE \
         {ulptool_dir}/src/esp32ulp_build_recipe.py \
         $_CPPINCFLAGS \
        -b {project_dir} \
        -p {framework_dir} \
        -u {toolchain_ulp_dir}/bin \
        -x {toolchain_xtensa_dir}/bin \
        -t {ulptool_dir}/src/ \
        -m {mcu} \
        {cpp_defines}
    """
    )
    if res:
        raise Exception("An error returned by ulptool.")


def cb(*args, **kwargs):
    print("Running ulptool")
    run_ulptool()


# Run ulptool just before linking .elf
env.AddPreAction("$BUILD_DIR/${PROGNAME}.elf", cb)
