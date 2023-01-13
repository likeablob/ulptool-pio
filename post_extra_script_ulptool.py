# Copyright (c) likeablob
# SPDX-License-Identifier: MIT
from pathlib import Path
import tempfile

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
    toolchain_ulp_dir = platform.get_package_dir("toolchain-esp32ulp")
    toolchain_xtensa_dir = platform.get_package_dir(
        "toolchain-%s" % ("xtensa-%s" % mcu)
    )

    cpp_defines = ""
    for raw in env["CPPDEFINES"]:
        k = None
        if type(raw) is tuple:
            k, v = raw
            v = str(v)
            v = v.replace(" ", "\\ ")
            flag = "-D%s=%s " % (k, v)
        else:
            k = raw
            flag = f"-D{k} "

        if k.startswith("ARDUINO"):
            cpp_defines += flag

    # create a tempfile to store all include paths, forward it to GCC as an optionfile
    # see https://gcc.gnu.org/onlinedocs/gcc/Overall-Options.html
    inc_file = tempfile.NamedTemporaryFile(delete=False)
    for path in env["CPPPATH"]:
        inc_file.write(bytes("-I\"" + str(path).replace("\\","\\\\") + "\" ", "utf-8"))
    # also write defines in it
    inc_file.write(cpp_defines.encode('utf-8'))
    inc_file.flush()
    inc_file.close()
    #print("Wrote option file to " + inc_file.name)

    res = env.Execute(
        f""""$PYTHONEXE" \
         "{ulptool_dir}/src/esp32ulp_build_recipe.py" \
        --incfile "{inc_file.name}" \
        -b "{project_dir}" \
        -p "{framework_dir}" \
        -u "{toolchain_ulp_dir}/bin" \
        -x "{toolchain_xtensa_dir}/bin" \
        -t "{ulptool_dir}/src/" \
        -m {mcu}
    """
    )

    if res:
        raise Exception("An error returned by ulptool.")
    # remove tempfile again if everything went right (otherwise debug info)
    Path(inc_file.name).unlink()


# Run ulptool immediately to generate needed header files
print("Running ulptool")
run_ulptool()