Extra scripts mainly to aid in collecting information about the supported files, or to clean up Blender files.
All of the Python scripts must be run within Blender. They cannot be run outside of it.

* cleanup-meshes.py: Open this file in the text editor, and execute this script after import to move most kinds of meshes not part of a character's default face. Also changes the image file paths to be relative to the current Blender file.

* numdlb-info-py: Run in a terminal/command prompt to retrieve information about NUMDLB, NUMATB, NUMSHB, NUSKTB files without a GUI. It must be run with `blender --background --python`.

* nuanmb-info-py: Run in a terminal/command prompt to retrieve information about NUMANMB files. It must be run with `blender --background --python`.
