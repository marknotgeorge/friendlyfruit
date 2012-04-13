Running FriendlyFruit
=====================

Currently FriendlyFruit is just a proof-of-concept.  There are various
problems around 3D models that I have been trying to solve, and
FriendlyFruit is the testbed.  However, it does run, and it could be
the foundation for a real Raspberry Pi multi-user game.

I've been using Panda3D on the basis that Panda is probably the
easiest game engine to learn.  Currently there is a demo scene that
you can walk around.  When you start the game, you will see a (very
well modelled) building from 3dWarehouse in front of you.

If you walk to the right hand side of the building, you will see a
crude humanoid figure walking up and down with a walk cycle that
doesn't quite work!  He was made in Blender by yours truly.  In spite
of the fact that he's not the world's greatest model, though, I'm very
pleased.  He has a raspberry badge UV-mapped onto his chest,
demonstrating that the textures work.  He also has a walk cycle of
sorts, demonstrating that armatures and animations work.  That's
really all we need.

If you want to get FriendlyFruit working, you will need to install
Panda3D (the developer kit, not the runtime) from
http://www.panda3d.org/.  I don't think you need anything else unless
you intend to modify the models.  In that case, see the next section
for instructions.

To run FriendlyFruit, just change into the 'client' directory and run
the Python script called 'client'.  You then control the camera with
the WASD keys, plus the left and right arrow keys.

I've tested this with Ubuntu 11.10.  If that's what you're running,
and you have a 3D-capable video card, you stand a good chance of
success.  Theoretically Panda supports quite a lot of platforms,
though, so you should stand a reasonable chance on other systems too.

Finally, be aware that this code is at a very early stage.  Don't
expect anything polished, instead expect to mess around quite a bit in
order to get it working.

Please let me know how you get on.


3D Object Notes
===============

3Dwarehouse
-----------

Not all files in 3Dwarehouse are downloadable.  This is annoying
because non-downloadable models clutter up the site and make it
difficult to find what you want.  One tip is that the Advanced Search
screen has an option to ignore models which cannot be downloaded.

Once you have a downloadable model, you have to decide whether you
will be editing it further with Sketchup.  If you won't, download it
in COLLADA format and go to `COLLADA to Panda`_, below.  If you will
be editing it, download it in Sketchup format.  When you have finished
editing, go to `Sketchup to COLLADA`_.

Sketchup to COLLADA
-------------------

If you have a model in Sketchup, and you want to use it in a game, you
should export it as COLLADA.  The export options should be set as
follows::


    [X] Export Two-Sided Faces
    [ ] Export Edges
    [X] Triangulate All Faces
    [ ] Export Only Selection Set
    [ ] Export Hidden Geometry
    [ ] Preserve Component Hierarchies

    [X] Export Texture Maps
    [ ] Use "Color By Layer" Materials

    [X] Preserve Credits


This will give you a usable COLLADA file.  Continue to `COLLADA to
Panda`_ to get it into Panda.

COLLADA to Panda
----------------

Run dae2egg on your file.  This will give you a text file which can be
loaded into Panda.  You can optionally run egg2bam on the egg file, to
compress it and speed up loading.

You may find that the paths to your texture files don't end up
pointing to the place where you want to keep them.  If this happens,
it's often easiest to fix it by editing the egg file (with a text
editor or a script).  It's a simple text format so it's easy to make
this kind of change.

COLLADA to Blender
------------------

If you have a Sketchup model, I would suggest that you edit it in
Sketchup if you can.  Converting it to another format is unlikely to
preserve all the information in the file.  However, you may be forced
to convert, perhaps because you don't run Windows or because you want
to combine it with something that is already in Blender.

Blender ships with a COLLADA importer, but there is a bug which
results in the wrong textures being assigned to some of the faces of
the model.  You could reapply the textures, but this would be rather
tedious for a complex model.

A better option is the Open Asset Import Library,
http://assimp.sourceforge.net .  At the time of writing, you need to
download a pre-release version, like this:

svn co https://assimp.svn.sourceforge.net/svnroot/assimp/trunk assimp

I ended up with revision 1231.  If you try this and it doesn't work,
try checking out this exact revision.

You then build Assimp yourself, following the instructions on the
website.  Once you have built it, convert the COLLADA file to
Wavefront:

assimp export model.dae model.obj

This can be imported into Blender using the Wavefront importer.

(There are other programs which convert COLLADA to Wavefront, but as
usual, many of them give unsatisfactory results.  In particular, many
of them fail to export the textures properly.)

Blender to Panda
----------------

Follow the first option (YABEE) on this page:

http://www.panda3d.org/manual/index.php/Converting_from_Blender

Before exporting you must apply all modifiers except the armature.  Be
very careful that you undo this after exporting, or (assuming the
modifiers are required) you will lose your work.

To create for example a walk cycle, first create it as a regular
Blender animation.  You can have several in the same file, one after
the other.  Then, during export, enter the start and end frames of
each animation into YABEE's dialogue box.

Underneath this dialogue box are various options.  Set them as
follows::


    [ ] Animation only
    [ ] Separate animation files *
	TBS generation: No
	Tex. process:   Simple
    [ ] UV as texture
    [ ] Copy texture files


\* This one is up to you, but I think it's convenient to store
everything in one file.
