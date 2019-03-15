# Super Smash Bros. Ultimate model and animation importers for Blender (io_scene_numdlb)
Imports data referenced by NUMDLB files (binary model format used by some games developed by Bandai-Namco). May work for other games using the same format. Unlike the original MAXScript, this plugin is cross-platform, as it will work on any operating system that Blender and Python exist for. The readability in the rewritten script is also improved, with the main function split into several smaller ones. An importer for animation file (.nuanmb) can be found here, but it cannot actually import anything for now.

**This script is now ready for daily use. However, there are a few limitations in the script:**

* Vertex colors are set, but the alpha channel is not used, as there is no way to set it within the Blender UI.
* UV maps will import, but without images assigned to them. They must be assigned manually; use the material and texture information for hints on the images to assign to each mesh.
* Bone roll is not calculated, so animations imported from files may cause meshes to deform incorrectly. although I'm working a NUANMB importer in hopes of solving this problem.

## Credits
* The NUMDLB importer uses helper functions from the SuperTuxKart SPM importer at <https://sourceforge.net/p/supertuxkart/code/HEAD/tree/media/trunk/blender_26/spm_import.py>.
* Parts of the Python scripts reference snippets of code from <http://steamreview.org/BlenderSourceTools/>.
* The NUANMB importer references code from <https://github.com/SE2Dev/io_anim_seanim>.
* <https://github.com/Ploaj/SSBHLib> - used for checking whether my scripts read the original data correctly or not. The majority of the NUANMB importer references code from here as well.

## License
Everything but the original MAXScript is licensed under the MIT License, found at <./LICENSE>.
