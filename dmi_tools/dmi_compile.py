import os
import json
import re
import math
import logging

from PIL import Image, PngImagePlugin

dir2str = {
	0 : "south",
	1 : "north",
	2 : "east",
	3 : "west",
	4 : "southeast",
	5 : "southwest",
	6 : "northeast",
	7 : "northwest"
}

symsubs = {
    '/': 'SLASH',
    '\\':'BACKSLASH',
    ':': 'COLON',
    '<': 'LESS',
    '>': 'GREATER',
    '|': 'VERTICAL',
    '?': 'QUESTION',
    '*': 'ASTERISK'
}
symsubs = {"[@{}]".format(y):x for x,y in symsubs.items()} # prepare dict

logger = logging.getLogger("dmi_tools")
state = "" # crutch for logging

def unfixStateName(state):
    pattern = re.compile(r'\b(' + '|'.join(symsubs.keys()) + r')\b')
    return pattern.sub(lambda x: symsubs[x.group()], state)

def collectStateMetainfo(statefiles, statePath, framename = 'frame'):
    directions = 1
    frames = 1
    delays = 1
    movement = False

    statemetainfo = None
    if "metainfo.json" in statefiles:
        with open(os.path.join(statePath, "delay.json")) as f:
            statemetainfo = json.load(f)
        statefiles.remove("metainfo.json")
        if 'delay' in statemetainfo:
            delays = len(statemetainfo['delay'])

    for icon in statefiles:
        m = re.match("{}(?P<movement>_\[MOVEMENT\])(_(?P<frame>\d+))?(_(?P<direction>\w+))?\.png".format(framename), icon)
        if not m:
            raise Exception("unknown file!")
        if m['movement'] is not None:
            movement = True
        if m['direction'] is not None:
            if m['direction'] in ["south", "north", "east", "west"]:
                directions = max(directions, 4)
            elif m['direction'] in ["southeast", "southwest", "northeast", "northwest"]:
                directions = 8
        else:
            if directions > 1:
                raise Exception("direction is missing!")
        if m['frame'] is not None:
            frames = max(frames, int(m['frame']) + 1)

    if frames != delays:
        if statemetainfo is None:
            raise Exception("delay.json is missing!")
        else:
            logger.warning("the quantity of delays ({}) and frames ({}) not match for state {}!".format(delays, frames, state))
            statemetainfo['delay'] = statemetainfo['delay'][:delays-frames]

    if len(statefiles) != directions * frames:
        raise Exception("incorrect frames count!")

    result = {
        'dirs': directions,
        'frames': frames
    }
    if statemetainfo is not None:
        result.update(statemetainfo)

    return result

def collectMetainfo(path):
    result = {}

    items = os.listdir(path)
    if 'metainfo.json' in items:
        items.remove('metainfo.json')
    for item in items[:]:
        itempath = os.path.join(path, item)
        if os.path.isdir(itempath):
            statefiles = os.listdir(itempath)
            global state
            state = unfixStateName(item)
            try:
                result[item] = collectStateMetainfo(statefiles, itempath)
            except Exception as e:
                logger.error("(state: {}) ".format(state) + str(e))
            items.remove(item)
    if len(items) > 0:
        result[""] = collectStateMetainfo(items, path, framename='default')

    return result

def metainfo2description(metainfo):
    """Collect description from metainfo. Also counts the number of states"""

    description = "# BEGIN DMI\nversion = 4.0\n"
    description += "\twidth = {}\n".format(metainfo['width'])
    description += "\theight = {}\n".format(metainfo['height'])

    numOfStates = 0

    for state, props in metainfo['states'].items():
        description += "state = \"{}\"\n".format(state)
        curIconStates = 1
        for prop, value in props.items():
            if prop == 'delay':
                description += "\t{} = {}\n".format(prop, ','.join([str(a) for a in value]))
            else:
                description += "\t{} = {}\n".format(prop, value)
                if prop in ['dirs', 'frames']:
                    curIconStates *= value
        numOfStates += curIconStates

    description += "# END DMI\n"

    return description, numOfStates

def dmi_compile(pdmi_path, res_path):
    """open name dir and collect all states there into name.dmi, according to metainfo.json"""

    pdmi_path_root = pdmi_path[0]
    pdmi_path_rel = pdmi_path[1]
    pdmi_path_filename = pdmi_path[2]

    pdmi_path_full = os.path.join(pdmi_path_root, pdmi_path_rel, "[pdmi]" + pdmi_path_filename)
    res_path = os.path.join(res_path, pdmi_path_rel)
    res_name = pdmi_path_filename + ".dmi"
    res_path_full = os.path.join(res_path, res_name)

    print(pdmi_path_full + " -> " + res_path_full)

    if not os.path.exists(res_path):
        os.makedirs(res_path)

    with open(os.path.join(pdmi_path_full, "metainfo.json")) as f:
        old_metainfo = json.load(f)

    metainfo = dict()
    metainfo['type'] = old_metainfo['type']
    metainfo['width'] = old_metainfo['width']
    metainfo['height'] = old_metainfo['height']

    metainfo['states'] = collectMetainfo(pdmi_path_full)

    # prepare necessary information
    description, numOfStates = metainfo2description(metainfo)

    spriteSheetWidthByTiles = math.ceil(math.sqrt(numOfStates))
    spriteSheetWidthByPixel = spriteSheetWidthByTiles * metainfo['width']

    spriteSheetHeightByTiles = math.ceil(numOfStates / spriteSheetWidthByTiles)
    spriteSheetHeightByPixel = spriteSheetHeightByTiles * metainfo['height']

    # create empty image
    result_img = Image.new('RGBA', (spriteSheetWidthByPixel, spriteSheetHeightByPixel), '#FFFFFF00')

    curState = 0

    # for each state, copy it frames to result_img
    for state, props in metainfo['states'].items():
        stateFolder = "{}/{}".format(pdmi_path_full, state)
        assert os.path.exists(stateFolder)

        dirs = 1
        frames = 1

        if "dirs" in props:
            dirs = props["dirs"]
        if "frames" in props:
            frames = props["frames"]

        for frame in range(frames):
            for direction in range(dirs):
                if len(state) == 0:
                    filename = "default"
                else:
                    filename = "frame"

                if frames > 1:
                    filename += "_{}".format(frame)
                if dirs > 1:
                    filename += "_{}".format(dir2str[direction])
                filename += ".png"

                state_img = Image.open("{}/{}".format(stateFolder, filename))


                x = curState  % spriteSheetWidthByTiles * metainfo['width']
                y = curState // spriteSheetWidthByTiles * metainfo['height']

                result_img.paste(state_img, (x, y))
                curState += 1

    # save result (don't forget Description)
    pngInfo = PngImagePlugin.PngInfo()
    pngInfo.add_text('Description', description)
    result_img.save(res_path_full, "png", pnginfo=pngInfo, optimize=True)