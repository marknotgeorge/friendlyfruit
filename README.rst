.. -*- mode: rst;mode: auto-fill -*-

Running FriendlyFruit
=====================

Currently FriendlyFruit is just a proof-of-concept.  There are various
problems around 3D models and RPC that I have been trying to solve,
and FriendlyFruit is the testbed.  However, it does run, and it could
be the foundation for a real Raspberry Pi multi-user game.

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

Prerequisites
-------------

If you want to get FriendlyFruit working, you will need to install
Panda3D (the developer kit, not the runtime) from
http://www.panda3d.org/.  If you want to run your own server (and you
do, because there are no public servers at this time) you will need
the following additional dependencies:

* MongoDB (http://www.mongodb.org/) and PyMongo
  (http://www.mongodb.org/display/DOCS/Python+Language+Center).  I am
  using MongoDB 2.0.4 from
  http://www.mongodb.org/display/DOCS/Ubuntu+and+Debian+packages but
  you should be able to use the version from your distro without
  problems.

  One word of warning is that Mongo tends to waste disk space if you
  aren't storing a large amount of data.  When you create a new
  database, it assumes you will be storing a lot of data, and it
  creates some very large files for it!  For this reason, edit
  /etc/mongodb.conf and add the option

  smallfiles = true

  to the end.  This will cause the largest per-database file to be
  32M.  For the same reason, if you run multiple server instances, try
  to use the same database for all of them (unless they become very
  large).  That way you only take the big file hit once, rather than
  once for each instance.

  It's also worth adding the option

  journal = true

  so you don't lose your data in the event that your machine crashes.
  (This is the default with some configurations of Mongo, but
  specifying it explicitly doesn't hurt.)

* Google Protobuf (https://developers.google.com/protocol-buffers/).
  You should be able to install this from your distro.  You need the
  Python support and the compiler.

* Scons (http://www.scons.org/).  This is used for building the
  Protobuf RPC stubs.  Again you should be able to install it from
  your distro.

* Pyflakes (https://launchpad.net/pyflakes) is a lint tool for
  Python.  You don't need this unless you're making a lot of changes
  to the source files, and you want to check for silly bugs.

  There is a script called run-pyflakes which invokes this program on
  all the manually-written Python files.  It's probably sensible to
  run this before checking changes into git.

Building
--------

Run scons in the top level directory, to build the RPC stubs.  These
are pure Python and presumably cross-platform; nothing is compiled to
machine code.

Configuration
-------------

You should have a file called server.cfg.sample.  You probably don't
need to change this, in which case the simplest thing is to symlink it
to server.cfg.  If you do need to change it, make a copy instead, and
then edit the copy.

The network section allows you to change the addresses that the server
listens on.  You could for example make it listen only on the loopback
address, for extra security during testing.

The database section gives the details of your database server.  The
host and port should normally be left unchanged; you only need them if
you want to run the server on a different machine to Mongo.

The prefix allows you to run more than one instance of FriendlyFruit
with a single database.  The default ('main.fruit') tells the server
to use the database 'main' and to prefix all collection names with
'fruit'.  To run two instances against the same database, you could
give them prefixes like 'main.raspberry' and 'main.strawberry'.  If
they got big enough that you wanted to use different databases, you
could use 'raspberry.fruit' and 'strawberry.fruit'.

Running FriendlyFruit
---------------------

Start by running the server.  It takes no arguments because all its
configuration information comes from server.cfg.

Once the server is running, you need to create a user account.  Run
the client like this:

./client --register -u myname -p mypass localhost

You should see a response from the server indicating that your account
was created.

To play, you do much the same thing:

./client -u myname -p mypass localhost

(I know the handling of the password isn't very secure or convenient,
but it's not the most important thing at the moment.)

Once the client is running, you control the camera with the WASD keys,
plus the left and right arrow keys.

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
