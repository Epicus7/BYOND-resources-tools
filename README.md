# BYOND-resources-tools

Tools for parsing and compiling DMI files. It can be useful for artists, which prefer to work with raw PNG then DMI. 
Also these scripts can be involved to use as merge tools.

# Using

To use these tools you need Python 3.6 installed.

## Parse

```python dmi_tools.py parse [dmi files directory] [directory for result png files]```

## Compile

```python dmi_tools.py compile [png files directory] [directory for result dmi files]```

# Logging

dmi_tools write logs to working directory. There you can find list of processed files and errors if any occurs.

# Parsed DMI files structure

* dmi_tools preserves relative .dmi files paths. Each .dmi file is parsed to one [pdmi] directory with all its png icons.
* For each .dmi state dmi_tools creates separate folder.
* For each state dmi_tools writes metainformation about it directly to icons names (directions, frames).
* For each .dmi dmi_tools also creates metainfo.json file with extra information that 
can't be placed at files names, for example animation delays and icons resolution.

# Problems

There are some problems, why these tools can't be used instead of DMI files for SS13 server as a full substitute:

* Tools generate a huge number of png files, causes significally git slow down. So it's bad idea try to index them with git as-is.
* Tools can be used for convinient work with PNG, but DMI provides cool general overview of .dmi states, which is lacking 
when working with [pdmi] states-folders.
