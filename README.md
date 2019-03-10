# Super Smash Bros. Ultimate model importer for Blender (io_scene_numdlb)
Imports data referenced by NUMDLB files (binary model format used by some games developed by Bandai-Namco). May work for other games using the same format. Unlike the original MAXScript, this plugin is cross-platform, as it will work on any operating system that Blender and Python exist for. The readability in the rewritten script is also improved, with the main function split into several smaller ones. An importer for animation file (.nuanmb) can be found here, but it cannot actually import anything for now.
**This script is a work-in-progress; it's not yet ready for daily use!**

## Credits
* The NUMDLB importer uses helper functions from the SuperTuxKart SPM importer at <https://sourceforge.net/p/supertuxkart/code/HEAD/tree/media/trunk/blender_26/spm_import.py>.
* Parts of the Python scripts reference snippets of code from <http://steamreview.org/BlenderSourceTools/>.
* The NUANMB importer references code from <https://github.com/SE2Dev/io_anim_seanim>.
## License
Everything but the original MAXScript is licensed under the MIT License, found at <./LICENSE>.
