import os
import re
import json
import logging
from collections import OrderedDict

from PIL import Image

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

logger = logging.getLogger("dmi_tools")

def assertAndGetField(line):
    """ check if line satisfies "name = value" pattern """
    m = re.match("\t?(?P<name>[a-z_]*)\ =\ [\"\']?(?P<value>[A-Za-z0-9_,\-\+\ ><]*)[\"\']?", line)
    assert m
    return m['name'], m['value']

def parse_metainfo(description):
    """ parse .dmi description to metainfo """

    metainfo = {}

    # split Description into strings
    dmi_info = description.split('\n')

    # check headers
    assert dmi_info.pop(0) == '# BEGIN DMI'
    assert dmi_info.pop(0) == 'version = 4.0'

    metainfo["type"] = "Parsed DMI 4.0"
    metainfo["width"] = 32  # default values
    metainfo["height"] = 32

    # get states
    states = {}

    while len(dmi_info) > 2:
        pair = assertAndGetField(dmi_info.pop(0))

        if pair[0] in ["width", "height"]:
            metainfo[pair[0]] = int(pair[1])
        elif pair[0] == "state":
            state = re.sub('[<>]', '', pair[1]).strip() # < and > shouldn't be in folder name
            props = {}
            while dmi_info[0][0] == '\t':
                props_pair = assertAndGetField(dmi_info.pop(0))
                if props_pair[0] in ["dirs", "frames"]:
                    props[props_pair[0]] = int(props_pair[1])
                elif props_pair[0] in ["delay"]:
                    props[props_pair[0]] = [int(a) for a in props_pair[1].split(',')]

            if state in states:
                logger.warning("state '{}' duplicated".format(state))
                num = 1
                while state + str(num) in states:
                    num += 1
                state += str(num) + "duplicate"
            states[state] = props
        else:
            raise Exception("Error: unknown dmi Description attribute!")

    metainfo["states"] = states
    return metainfo

def crop(im, width, height):
    """ cropped icons generator """

    imgwidth, imgheight = im.size
    for i in range(imgheight // height):
        for j in range(imgwidth // width):
            box = (j*width, i*height, (j+1)*width, (i+1)*height)
            yield im.crop(box)

def parse_image(im, res_path_full, metainfo):
    """ parse PIL.Image to .png icons according to metainfo by states

        each state of name.dmi -> name/state/state_frame_dir.png icons
    """

    width = metainfo['width']
    height = metainfo['height']

    im_iter = iter(crop(im, width, height))

    for state, props in metainfo["states"].items():
        stateFolder = os.path.join(res_path_full, state)
        if not os.path.exists(stateFolder):
            os.makedirs(stateFolder)

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

                img = Image.new('RGBA', (height, width), '#FFFFFF00')
                img.paste(im_iter.__next__())
                img.save("{}/{}".format(stateFolder, filename))

def dmi_parse(dmi_path, res_path):
    """ parse .dmi file into folder with states subfolders and metainfo.json file """

    dmi_path_root = dmi_path[0]
    dmi_path_rel = dmi_path[1]
    dmi_path_filename = dmi_path[2]
    dmi_path_fileext = dmi_path[3]

    dmi_path_full = os.path.join(dmi_path_root, dmi_path_rel, dmi_path_filename) + dmi_path_fileext
    res_path_full = os.path.join(res_path, dmi_path_rel, "[pdmi]" + dmi_path_filename)

    if not os.path.exists(res_path_full):
        os.makedirs(res_path_full)

    im = Image.open(os.path.join(dmi_path_full))
    metainfo = parse_metainfo(im.info['Description'])
    parse_image(im, res_path_full, metainfo)

    # sort dict by keys
    metainfo['states'] = OrderedDict(sorted(metainfo['states'].items(), key=lambda t: t[0]))

    with open("{}/metainfo.json".format(res_path_full), "w") as output:
        print(json.dumps(metainfo, indent=4), file=output)
