import dmi_tools as tools
import sys
import os
import logging
import datetime
from shutil import copyfile

def main():
    if len(sys.argv) == 0:
        raise Exception("Please, specify correct command by first argument: 'getinfo', 'compile' or 'parse'!")
    command = sys.argv[1]

    # setup logger
    logger = logging.getLogger("dmi_tools")
    logger.setLevel(logging.INFO)

    date = datetime.datetime.now().strftime("%d%m%y-%H.%M.%S")

    handler = logging.FileHandler('{}.log'.format(date), 'w')
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

    if command == "getinfo":
        dmi_path = sys.argv[2]
        assert os.path.exists(dmi_path)
        tools.dmi_getinfo(dmi_path)
    elif command == "parse":
        root_path = sys.argv[2]
        result_path = sys.argv[3]

        assert os.path.exists(root_path)
        if not os.path.exists(result_path):
            os.makedirs(result_path)

        for path, subdirs, files in os.walk(root_path):
            for name, ext in [os.path.splitext(file) for file in files]:
                relPath = os.path.relpath(path, root_path)
                #print(os.path.join(relPath, name + ext))

                FORMAT = '%(levelname)s: [{}] %(message)s'.format(os.path.join(relPath, name + ext))
                formatter = logging.Formatter(FORMAT)
                handler.setFormatter(formatter)

                if ext == '.dmi':
                    logger.info("start parsing.")
                    try:
                        tools.dmi_parse((root_path, relPath, name, ext), result_path)
                    except Exception as e:
                        logger.error(str(e))

                else:
                    newPath = os.path.join(result_path, relPath)
                    if not os.path.exists(newPath):
                        os.makedirs(newPath)
                    copyfile(os.path.join(path, name + ext), os.path.join(newPath, name + ext))
                    logger.info("copied.")
    elif command == "compile":
        root_path = sys.argv[2]
        result_path = sys.argv[3]

        assert os.path.exists(root_path)
        if not os.path.exists(result_path):
            os.makedirs(result_path)

        paths = [root_path, ]
        for path in paths:
            for item in os.listdir(path):
                itempath = os.path.join(path, item)
                relPath = os.path.relpath(path, root_path)

                FORMAT = '%(levelname)s: [{}] %(message)s'.format(os.path.join(relPath, item))
                formatter = logging.Formatter(FORMAT)
                handler.setFormatter(formatter)

                if os.path.isdir(itempath):
                    if item.startswith("[pdmi]"):
                        name = item[6:]

                        logger.info("start compiling.")
                        tools.dmi_compile((root_path, relPath, name), result_path)
                    else:
                        paths.append(path + "\\" + item)
                else:
                    newPath = os.path.join(result_path, relPath)
                    if not os.path.exists(newPath):
                        os.makedirs(newPath)
                    copyfile(os.path.join(path, item), os.path.join(newPath, item))
                    logger.info("copied.")
    else:
        raise Exception("Please, specify correct command by first argument: 'getinfo', 'compile' or 'parse'!")

if __name__ == "__main__":
    main()

