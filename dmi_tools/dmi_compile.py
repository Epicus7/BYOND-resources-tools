import sys

import os
import json
import math

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

def dmi_compile(name):
    """open name dir and collect all states there into name.dmi, according to metainfo.json"""

    assert os.path.exists(name)

    with open('{}/metainfo.json'.format(name)) as f:
        metainfo = json.load(f)

    # prepare nessesary information
    description, numOfStates = metainfo2description(metainfo)

    spriteSheetWidthByTiles = math.ceil(math.sqrt(numOfStates))
    spriteSheetWidthByPixel = spriteSheetWidthByTiles * metainfo['width']

    spriteSheetHeightByTiles = math.ceil(numOfStates / spriteSheetWidthByTiles)
    spriteSheetHeightByPixel = spriteSheetHeightByTiles * metainfo['height']

    # create empty image
    result_img = Image.new('RGBA', (spriteSheetHeightByPixel, spriteSheetWidthByPixel), '#FFFFFF00')

    curState = 0

    # for each state, copy it frames to result_img
    for state, props in metainfo['states'].items():
        stateFolder = "{}/{}".format(name, state)
        assert os.path.exists(stateFolder)

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

                state_img = Image.open("{}/{}".format(stateFolder, filename))


                x = curState  % (spriteSheetWidthByTiles - 1) * metainfo['width']
                y = curState // (spriteSheetWidthByTiles - 1) * metainfo['height']

                result_img.paste(state_img, (x, y))
                curState += 1

    # save result (don't forget Description)
    pngInfo = PngImagePlugin.PngInfo()
    pngInfo.add_text('Description', description)
    result_img.save("{}.dmi".format(name), "png", pnginfo=pngInfo)

def main():
    name = sys.argv[1]
    dmi_compile(name)

if __name__ == "__main__":
    main()