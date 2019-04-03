# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
