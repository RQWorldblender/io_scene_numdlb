# Super Smash Bros. Ultimate model and animation importers for Blender (io_scene_numdlb)
Imports data referenced by NUMDLB files (binary model format used by some games developed by Bandai-Namco). May work for other games using the same format. Unlike the original MAXScript, this plugin is cross-platform, as it will work on any operating system that Blender and Python exist for. The readability in the rewritten script is also improved, with the main function split into several smaller ones. An importer for animation file (.nuanmb) can be found here, but it cannot actually import anything for now.

**This script is now ready for daily use. However, there are a few limitations in the script:**

* Vertex colors are set, but the alpha channel is not used, as there is no way to set it within the Blender UI.
* UV maps will import, but without images assigned to them. They must be assigned manually; use the material and texture information for hints on the images to assign to each mesh.
* Bone roll is not calculated, so animations imported from files may cause meshes to deform incorrectly, although I'm working on a NUANMB importer in hopes of solving this problem.

## Installation
This set of two scripts requires Blender 2.70 or later, but only 2.79 has been tested.
1. Clone or download this repository. If downloaded, extract the files after that.
2. Open Blender and select `File -> User Preferences -> Install from File` and select the newly downloaded scripts.
3. In the search bar in the upper left, search for `Super Smash Bros. Ultimate`. If no results are found, try enabling the `Testing` supported level below the search bar.
4. Enable the plugin by clicking the checkbox next to the plugin name.
5. Select `Save User Settings` in the lower left and close the window.

## Removal
1. Open Blender and select `File -> User Preferences -> Add-ons`.
2. In the search bar in the upper left, search for `Super Smash Bros. Ultimate`. If no results are found, try enabling the `Testing` supported level below the search bar.
3. Disable the plugin by clicking the checkbox next to the plugin name - or uninstall the plugin by clicking `Remove`.
4. Select `Save User Settings` in the lower left and close the window.

## Credits
* The NUMDLB importer uses helper functions from the SuperTuxKart SPM importer at <https://sourceforge.net/p/supertuxkart/code/HEAD/tree/media/trunk/blender_26/spm_import.py>.
* Parts of the Python scripts reference snippets of code from <http://steamreview.org/BlenderSourceTools/>.
* The NUANMB importer references code from <https://github.com/SE2Dev/io_anim_seanim>.
* <https://github.com/Ploaj/SSBHLib> - used for checking whether my scripts read the original data correctly or not. The majority of the NUANMB importer references code from here as well.

## License
Everything but the original MAXScript is licensed under the MIT License, found at <./LICENSE>.
