# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
* NUANMB importer script is still work-in-progress - the following are known to work correctly:
    * Creating an action and setting its name.
    * Collecting how many frames to set and keying each one.
    * Visibility animations are the only kind of animation that are imported correctly. All other kinds are unsupported, or fail to import correctly.

The NUANMB importer is not yet deemed to be stable/ready-to-use as bones are not transformed correctly. The only workaround for this is to create custom animations (only for those who know how to animate objects).

## [1.1.0] - 2019-03-29 (NUMDLB importer only)
* Images are actually assigned to UV maps automatically if they have been found.
* An action is created by default to backup the rest pose; useful for going back to a clean state.
* Materials have fake users set so that they do not get removed if they are not used.
* Meshes have their origins set to their geometrical medians after they have been transformed.

## [1.0.0] - 2019-03-14
* Initial versioned release - normal operation of the model importer script should be stable.
