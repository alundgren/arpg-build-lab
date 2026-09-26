"""One isolated LEB calculation in a fresh Python and Lua process."""

import json
import math
import platform
import sys
from importlib import import_module
from importlib.metadata import version
from pathlib import Path


def metrics_from_output(output: dict) -> dict[str, dict]:
    if not isinstance(output, dict) or not isinstance(output.get("metrics"), dict):
        raise ValueError("LEB metric output is missing")
    result = {}
    for name, source, unit in (
        ("health", "Life", "health points"),
        ("armour", "Armour", "armour rating"),
    ):
        value = output["metrics"].get(source)
        try:
            valid = type(value) in (int, float) and math.isfinite(value) and value >= 0
        except OverflowError:
            valid = False
        if not valid:
            raise ValueError(f"LEB {source} must be a nonnegative finite number")
        result[name] = {"value": value, "unit": unit}
    return result


def main() -> int:
    try:
        try:
            lua_runtime = import_module("lupa.luajit21").LuaRuntime
        except ModuleNotFoundError as exc:
            if exc.name != "lupa.luajit21":
                raise
            lua_runtime = import_module("lupa.lua").LuaRuntime

        lua = lua_runtime(unpack_returned_tuples=True)
        jit_version = lua.eval("jit and jit.version or nil")
        if not isinstance(jit_version, str) or not jit_version.startswith("LuaJIT 2.1"):
            raise ValueError("Lupa must use LuaJIT 2.1 for this calculator")
        globals_ = lua.globals()
        globals_.arg = lua.table()
        globals_.package.path = (
            "../runtime/lua/?.lua;../runtime/lua/?/init.lua;" + globals_.package.path
        )
        globals_.dofile("HeadlessWrapper.lua")
        globals_.loadBuildFromXML(sys.stdin.read(), "ARPG Build Lab")
        build = globals_.build
        spec = build.spec
        nodes = {
            str(key): node.alloc for key, node in spec.allocNodes.items() if node.alloc
        }
        equipped = {
            str(name): slot.selItemId
            for name, slot in build.itemsTab.slots.items()
            if slot.selItemId and slot.selItemId != 0
        }
        output = {
            "loaded": {
                "class_id": spec.curClassId,
                "class_name": spec.curClassName,
                "mastery_id": spec.curAscendClassId,
                "level": build.characterLevel,
                "target_version": build.targetVersion,
                "tree_version": spec.treeVersion,
                "auto_level": bool(build.characterLevelAutoMode),
                "nodes": nodes,
                "skills": len(list(build.skillsTab.socketGroupList.items())),
                "items": len(list(build.itemsTab["items"].items())),
                "equipped": equipped,
                "combat_inputs": {
                    str(key): value for key, value in build.configTab.input.items()
                },
            },
            "metrics": {
                "Life": build.calcsTab.mainOutput.Life,
                "Armour": build.calcsTab.mainOutput.Armour,
            },
            "runtime": "Lupa LuaJIT 2.1",
            "runtime_version": jit_version
            + " / Lupa "
            + version("lupa")
            + " / Python "
            + platform.python_version(),
            "rounding": bool(globals_.itemLib.useLEToolsRounding),
        }
        Path(sys.argv[1]).write_text(
            json.dumps(output, sort_keys=True, allow_nan=False)
        )
        return 0
    except Exception as exc:
        print(f"LEB worker: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
