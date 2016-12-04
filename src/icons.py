import os
import copy

from pa_tools.pa import pajson
from pa_tools.pa import spec


def generate_dot_effects():
    # use string loading to make it ordered
    base_dot, warnings = pajson.loads("""{
      "spec": {
        "shader": "particle_transparent_screensize_nohdr",
        "facing" : "camera",
        "red": 1,
        "green": 1,
        "blue": 0,
        "alpha": 1,
        "baseTexture": "/pa/effects/textures/particles/dot.papa"
      },
      "offsetY": 2.5,
      "sizeX": 2,
      "emissionBurts": 1,
      "lifetime": 127,
      "killOnDeactivate": true,
      "startDistance" : 700,
      "endDistance": -1
    }""", '<dot effect file>')

    list(map(print, warnings))

    dot_small = copy.deepcopy(base_dot)
    dot_small['sizeX'] = 1

    dot_medium = copy.deepcopy(base_dot)
    dot_medium['sizeX'] = 2

    dot_large = copy.deepcopy(base_dot)
    dot_large['sizeX'] = 3

    dot_huge = copy.deepcopy(base_dot)
    dot_huge['sizeX'] = 4

    return {
        "small" : dot_small,
        "medium" : dot_medium,
        "large" : dot_large,
        "huge" : dot_huge
    }

def compute_size(damage):
    if damage <= 24:
        return "small"
    elif damage <= 200:
        return "medium"
    elif damage <= 400:
        return "large"
    else:
        return "huge"

def generate_strat_icon(loader):
    #  - get each weapon on the unit
    #  - get each ammo type
    #       - use damage to decide dot size
    #         (small, medium, large)

    # we have to clear the spec cache
    spec.clear_cache()
    dots = generate_dot_effects()

    # going to store the effect file patches here
    patches = []

    visited_fx_files = {}
    checked_ammo_ids = {}

    unit_file = '/pa/units/land/tank_light_laser/tank_light_laser.json'
    # get unit data
    unit = spec.parse_spec(loader, unit_file)

    # iterate over unit weapons
    for tool_obj in unit.get('tools', []):
        tool = spec.parse_spec(loader, tool_obj['spec_id'])

        # ignore tools which are not weapons
        if tool.get('tool_type', 'TOOL_BuildArm') == 'TOOL_BuildArm':
            continue

        # we might get an actual ammo_id here or an array of them
        ammo_id_list = tool.get('ammo_id', None)

        if ammo_id_list:
            # if we have a list, map to the ammo_id values
            if isinstance(ammo_id_list, list):
                ammo_id_list = map(lambda item: item['id'], ammo_id_list)
            else:
                ammo_id_list = [ammo_id_list]

            for ammo_id in ammo_id_list:
                # doing ammo id caching
                if ammo_id in checked_ammo_ids: continue
                checked_ammo_ids[ammo_id] = True

                ammo = spec.parse_spec(loader, ammo_id)

                # must be ammo_projectile type, or its the uber cannon projectile
                if ammo['ammo_type'] == 'AMMO_Projectile' or (ammo['ammo_type'] == 'Projectile' and 'uber' in ammo_id):
                    fx_id = ammo['fx_trail']['filename']

                    size = compute_size(ammo['damage'])

                    # get destination from the ammo name
                    fx_name = ammo_id[:-5] + '_trail.pfx'
                    # make sure we only generate the effect once
                    if fx_name not in visited_fx_files:
                        visited_fx_files[fx_name] = True
                        patches.append({
                            "target" : fx_id,
                            "destination" : fx_name,
                            "patch" : [
                                {"op" : "add", "path" : "/emitters/-", "value": dots[size]}
                            ]
                        })

                    if 'base_spec' in ammo:
                        base_ammo, warnings = pajson.loadf(loader.resolveFile(ammo_id))
                        ammo = spec.prune_spec(ammo, base_ammo)

                    patch_value = ammo.get('fx_trail', {})
                    patch_value['filename'] = fx_name

                    patches.append({
                        "target": ammo_id,
                        "patch" : [
                            {"op": "add", "path": "/fx_trail", "value": patch_value}
                        ]
                    })
    return patches