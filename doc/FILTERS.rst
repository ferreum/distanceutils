**************
.bytes Filters
**************

This is a list of filters provided by the ``distance.filter`` module.

These filters can be applied from the command line using the
``dst-filterlevel`` script.

Filters provide a ``:help`` argument, which lists the filter's available
arguments.


filter: ``rm``
''''''''''''''

Remove objects with matching type, index or sections.

For example, to remove all roads from "my_level.bytes"::

  $ dst-filterlevel my_level.bytes result.bytes -o rm:type=Road


filter: ``goldify``
'''''''''''''''''''

Replace old simples (``[Emissive]<shape>[WithCollision]``) with golden simples.

Opaque simples are replaced with equal-looking golden simples. Emissive simples
on the other hand look different, because the texture of old simples is not
available for golden simples.

Not all simples have exact golden counterparts. The quality of the replacement
differs depending on the shape and other properties of the simple. For this
reason the replacements are put into categories:

* ``safe`` (default); all exact replacements:
  ``Cube``, ``Hexagon``, ``Octahedron``.

  These shapes are exact matches with their golden counterparts, and are
  scaled to exactly match the original.

* ``inexact``; scale, rotation or position may not be exact:
  ``Pyramid``, ``Dodecahedron``, ``Icosahedron``, ``Ring``, ``RingHalf``,
  ``TearDrop``, ``Tube``, ``IrregularCapsule001``, ``IrregularCapsule002``
  and all ``safe`` replacements.

  The transformations of these objects were estimated by binary-search. The
  lower precision may be noticeable for objects with very large scale, but
  generally, this category should be safe to use.

  ``Dodecahedron`` and ``Icosahedron`` need to be rotated in a way that they
  cannot retain independent scale on y and z axes. The filter skips the
  replacement if this is the case, retaining the old object.

* ``unsafe``; objects that don't have the correct shape:
  ``Sphere``, ``Cone``, ``Cylinder``, ``Wedge``, ``TrueCone``, ``Plane``,
  ``Capsule``, ``FlatDrop``, ``CylinderTapered`` and all ``inexact``
  replacements.

  The shape differences may be noticeable depending on the scale:

  The rounded surfaces of ``Sphere``, ``Cone``, ``TrueCone`` and ``Cylinder``
  are made of a different number of triangles.

  The old ``Wedge`` is not exactly right-angled, but the new ``WedgeGS`` is.

  ``[Emissive]PlaneWithCollision`` can be passed through in one direction, but
  has collision in the other. The replacement ``PlaneGS`` has collision in both
  directions.

  ``CapsuleGS`` has different proportions and different number of triangles.

  ``FlatDrop`` is replaced with ``CheeseGS``, which is not even close to the
  correct shape, but it's the best fit available.

  ``CylinderTapered`` is replaced with ``CircleFrustumGS``, which has a
  different angle and number of triangles.

* ``bugs``; just fix collisions with ``Cube`` objects.

  This is a work-around for the glitch with collisions with  old ``Cube``
  simples. This category just replaces all ``[Emissive]CubeWithCollision``
  with ``CubeGS``.

The category is specified as argument to the filter. For example, to use all
replacements::

  $ dst-filterlevel my_level.bytes result.bytes -o goldify:unsafe


filter: ``unkill``
''''''''''''''''''

Replace kill grids with harmless (kind-of similar looking) simples. Useful for
exploration, practice, and finding hidden routes.

Note: only finite kill grids are replaced for now, because they are most
significant for routing, and infinite ones are more difficult to replace.

Example::

  $ dst-filterlevel my_level.bytes result.bytes -o unkill

Collisions are enabled by default. To disable collisions specify
``unkill:nocollision``.

Color of the grid is copied to the simple by default. To use the default grid
color specify ``unkill:nocolor``.


filter: ``vis``
'''''''''''''''

Visualize various things by adding simples in their position.

Example::

  $ dst-filterlevel my_level.bytes result.bytes -o vis

Colliders of different objects are color-coded to indicate their effect.

Teleporter colliders have additional indicators for their connection status:

* Green: Bidirectional (destination teleporter leads back to this one)

* Blue: Unidirectional, but at least one different teleporter leads to this
  teleporter.

* Yellow: Unidirectional (can enter, but nothing leads to this teleporter)

* Pink: This teleporter leads nowhere, but at least one teleporter leads here.

* Red: not connected, or leads to itself


filter: ``settings``
''''''''''''''''''''

Modify level settings.

For example, to enable all modes and append "(filtered)" to the name::

  $ dst-filterlevel my_level.bytes result.bytes -o settings:modes=all:namefmt='{} (filtered)'


