#!/usr/bin/env python3
import os
import shutil

from pa_tools.pa import pafs
from pa_tools.pa import paths
from pa_tools.pa import pajson

from pa_tools.mod.checker import check_mod
from pa_tools.mod.generator import process_modinfo, process_changes

from icons import generate_strat_icons

def create_source_fs():
    # setting up source file system
    src = pafs(paths.PA_MEDIA_DIR)
    src.mount('/pa', '/pa_ex1')
    src.mount('/src', '.')

    return src

def load_json(loader, path):
    resolved = loader.resolveFile(path)
    json, warnings = pajson.loadf(resolved)
    for w in warnings:
        print (w)
    return json


def generate_mod(is_titans):
    out_dir = '..'

    # create the base file system
    src = create_source_fs()

    process_modinfo('/src/modinfo.json', src, out_dir)

    # mount the mod directory
    src.mount('/mod', out_dir)

    # remove destination files
    shutil.rmtree(os.path.join(out_dir, 'pa'), ignore_errors=True)

    ## Generate the mod
    process_changes([
            '/ant/ant_patch.json'
        ], src, out_dir)

    # generate the stratigic icon effects
    print ('==== running strategic icon generator')
    src.unmount('/mod')
    src.mount('/', out_dir)
    process_changes(generate_strat_icon(src), src, out_dir)

    # analyse the mod for missing files
    mod_report = check_mod(out_dir)
    print(mod_report.printReport())

    ################# copy mod to pa mod directory
    mod_path = os.path.join(paths.PA_DATA_DIR, modinfo['context'] + '_mods', modinfo['identifier'])
    shutil.rmtree(mod_path, ignore_errors=True)
    shutil.copytree(out_dir, mod_path)

generate_mod(False)
generate_mod(True)
