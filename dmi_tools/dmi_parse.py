import sys

import os
import re
import json
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

def assertAndGetField(line):
    """ check if line satisfies "name = value" pattern """
    m = re.match("\t?(?P<name>[a-z_]*)\ =\ [\"\']?(?P<value>[A-Za-z0-9_,]*)[\"\']?", line)
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

    # get common info
    metainfo["width"] = int(assertAndGetField(dmi_info.pop(0))[1])
    metainfo["height"] = int(assertAndGetField(dmi_info.pop(0))[1])

    # get states
    states = {}

    while len(dmi_info) > 2:
        state = assertAndGetField(dmi_info.pop(0))[1]
        props = {}
        while dmi_info[0][0] == '\t':
            props_pair = assertAndGetField(dmi_info.pop(0))
            if props_pair[0] in ["dirs", "frames"]:
                props[props_pair[0]] = int(props_pair[1])
            elif props_pair[0] in ["delay"]:
                props[props_pair[0]] = [int(a) for a in props_pair[1].split(',')]

        if state in states:
            print("Warning! State '{}' duplicated".format(state))
            num = 1
            while state + str(num) in states:
                num += 1
            state += str(num)
        states[state] = props

    metainfo["states"] = states
    return metainfo

def crop(im, width, height):
    """ cropped icons generator """

    imgwidth, imgheight = im.size
    for i in range(imgheight // height):
        for j in range(imgwidth // width):
            box = (j*width, i*height, (j+1)*width, (i+1)*height)
            yield im.crop(box)

def parse_image(im, name, metainfo):
    """ parse PIL.Image to .png icons according to metainfo by states

        each state of name.dmi -> name/state/state_frame_dir.png icons
    """

    width = metainfo['width']
    height = metainfo['height']

    im_iter = iter(crop(im, width, height))

    for state, props in metainfo["states"].items():
        stateFolder = "{}/{}".format(name, state)
        if not os.path.exists(stateFolder):
            os.makedirs(stateFolder)

        dirs = 1
        frames = 1

        if "dirs" in props:
            dirs = props["dirs"]
        if "frames" in props:
            frames = props["frames"]

        for frame in range(frames):
            for dir in range(dirs):
                filename = state
                if len(filename) == 0:
                    filename = "default"

                if frames > 1:
                    filename += "_{}".format(frame)
                if dirs > 1:
                    filename += "_{}".format(dir2str[dir])
                filename += ".png"

                img = Image.new('RGBA', (height, width), '#FFFFFF00')
                img.paste(im_iter.__next__())
                img.save("{}/{}".format(stateFolder, filename))

def dmi_parse(name):
    """ parse .dmi file into folder with states subfolders and metainfo.json file """

    im = Image.open(name)
    dmi_name = name.rsplit(".", 1)[0] # "mob.vasya.dmi" -> "mob.vasya"

    metainfo = parse_metainfo(im.info['Description'])

    parse_image(im, dmi_name, metainfo)

    # sort dict by keys
    metainfo['states'] = OrderedDict(sorted(metainfo['states'].items(), key=lambda t: t[0]))

    with open("{}/metainfo.json".format(dmi_name), "w") as output:
        print(json.dumps(metainfo, indent=4), file=output)


def main():
    name = sys.argv[1]
    dmi_parse(name)

if __name__ == "__main__":
    main()