import dmi_tools as tools
import sys
import os
import logging
from shutil import copyfile

def main():
    command = sys.argv[1]
    root_path = sys.argv[2]
    result_path = sys.argv[3]

    assert os.path.exists(root_path)
    if not os.path.exists(result_path):
        os.makedirs(result_path)

    # setup logger
    logger = logging.getLogger("dmi_tools")
    logger.setLevel(logging.INFO)

    handler = logging.FileHandler('dmi_tools.log', 'w')
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

    if command == "parse":
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
        paths = [root_path, ]
        for path in paths:
            for item in os.listdir(path):
                if item.startswith("[pdmi]"):
                    relPath = os.path.relpath(path, root_path)
                    name = item[6:]

                    FORMAT = '%(levelname)s: [{}] %(message)s'.format(os.path.join(relPath, item))
                    formatter = logging.Formatter(FORMAT)
                    handler.setFormatter(formatter)

                    logger.info("start compiling.")
                    tools.dmi_compile((root_path, relPath, name), result_path)
                else:
                    paths.append(path + "\\" + item)
    else:
        raise Exception("Please, specify correct command by first argument: 'compile' or 'parse'!")

if __name__ == "__main__":
    main()

