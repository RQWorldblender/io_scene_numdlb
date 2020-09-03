# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1] - 2020-09-03
* Multiply nodes have a default factor of 1.0
* The B/Blue value for all normal map combine RGB nodes are set to 1.0
* UV maps are now linked to normal maps (1st layer only)

## [2.0.0] - 2020-08-22
* First numbered version for Blender 2.80 and later. Older Blender versions are no longer supported. Material setup is now done with nodes.
* Support for texturing two UV maps with materials. Especially allows to render most characters' eyes OOTB.
* Normal maps, PRM maps (Used with Principled BSDF shaders), and Emissive maps are now supported, but disabled by default.
* In relationship to the above, added options for toggling each of the three kinds of extra textures.
* Image alpha determined by specific keywords (most commonly "alp") in material names and/or texture names, instead of being set unilaterally for every texture. The option to unilaterally set image alpha has been subsequently removed.
* Alpha channel of vertex colors supported.
* Added undo history support.
* No longer create rest poses, as they are already embedded per armature during import.

## [1.3.3] - 2019-08-14
* Adding experimental support for blender 2.80

## [1.3.2] - 2019-05-06
* Fix how vertex indices are determined when importing vertices. This prevents vertex weights from being shared unintentionally with multiple vertices in the same location.
* Removed the remove_doubles option, as this operation would interfere with the above change and cause animations to distort certain models.

## [1.3.1] - 2019-04-20
* Fix visibility tracks not being properly keyed; previously every frame but the last one was being overwritten with new actions.
* Implement method to return the exact name of an object - used to determine if a mesh name matches a given track name.
* Change warning for NUANMB importer to warn about models that don't have bones aligned correctly.

## [1.3.0] - 2019-04-04
* Stop overwriting object origins; this is needed so that everything will properly rotate around the X axis.
* Improved method of storing vertex color and UV values, theoretically allowing for more than five of color maps or UV maps to be read.
* Duplicate UV coordinates are made unique; this allows for things like some assist fighters' eyes to be properly textured.
* Add new UI option to allow importing black vertex colors; they are not imported by default as they can cause meshes to become too difficult to see.

## [1.2.1] - 2019-04-04
* Fix image-loading method so that it does not error out on Windows systems
* Mesh cleanup script now changes image filepaths to be relative to saved Blender files

## [1.2.0] - 2019-04-03
* NUANMB importer script is now declared stable/ready-to-use, as the model importer has been fixed to properly support it.
* Bump minimum Blender version to 2.77, based on information in <https://blender.stackexchange.com/q/63116>.
* Bone length and axises are now taken into account.
* Improved method for retrieving images for UV maps, where in case they are not found, placeholders are created for them.
* Parenting will no longer fail for models that do not have a skeleton file.
* Store original bone matrix rows, single bind names as custom properties where applicable.
* Store vertex color alpha as float layers; this doesn't mean that they are actually used, but it allows them to be retrieved later on.
* Meshes have their origins set to their single bind bones only if they have one.
* Removed the connect_bones option as it would conflict with bone axis fixes (NUMDLB importer).
* Removed the ability to change import method, as it wasn't well-tested; actions are created for every animation file (NUANMB importer).

## [1.1.0] - 2019-03-29 (NUMDLB importer only)
* Images are actually assigned to UV maps automatically if they have been found.
* An action is created by default to backup the rest pose; useful for going back to a clean state.
* Materials have fake users set so that they do not get removed if they are not used.
* Meshes have their origins set to their geometrical medians after they have been transformed.
* Texture filename extension can no longer be arbitrary strings - now limited to a predefined list of formats that Blender supports.

## [1.0.0] - 2019-03-14
* Initial versioned release - normal operation of the model importer script should be stable.
