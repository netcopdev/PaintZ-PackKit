# PaintZ PackKit

PaintZ PackKit is the authoring and build toolkit for creating content packs for [PaintZ](https://github.com/netcopdev/PaintZ), the generic DayZ runtime painting framework.

PackKit is **not** a DayZ runtime framework and should not duplicate PaintZ gameplay logic. Its job is to turn finish definitions, source artwork and limited pack branding into consistent, validated, PaintZ-compatible pack content.

## Project status

This repository is at the initial architecture/bootstrap stage. The existing PaintZ generator currently lives in the PaintZ repository under `tools/paintzgen`; PackKit is intended to become the dedicated home for that authoring pipeline as it grows into a complete paint-pack builder.

The exact manifest/schema and generated directory layout are intentionally not frozen yet. They should be defined by implementation and tests rather than guessed in advance.

## Separation of responsibilities

### PaintZ core

PaintZ owns runtime behaviour and the common physical spray-can implementation:

- painting and stripping actions;
- eligibility/policy logic;
- persistence and synchronization;
- finish application and restoration;
- quantity, condition, animation and sound behaviour;
- the canonical spray-can model and UV layout;
- the non-spawnable `PaintZ_SprayCan_Base` class;
- the standard PaintZ can-label design contract;
- the runtime API/contract used by paint packs.

### PaintZ PackKit

PackKit is an **offline authoring/build tool**. Its intended responsibilities include:

- reading paint-pack and finish metadata;
- validating canonical finish identities and visible paint IDs;
- generating standardized spray-can artwork;
- generating or preparing finish surface textures and required variants;
- generating the thin DayZ classes needed for spawnable finish-specific spray cans;
- generating finish-registration/config fragments required by PaintZ;
- validating assets, paths, naming and pack consistency;
- producing a deterministic PBO-ready source tree;
- eventually providing packaging/build helpers where useful.

### Paint packs

A paint pack owns content, not painting mechanics. A normal pack may contain:

- finish definitions;
- solid/pattern/other surface textures;
- generated can textures;
- thin spawnable spray-can subclasses;
- optional restrained publisher/collection branding;
- metadata required to register its finishes with PaintZ.

A generated paint pack depends on PaintZ at runtime. PaintZ must never depend on a specific paint pack.

## Spray-can class model

PaintZ core provides one common base class, conceptually:

```cpp
class PaintZ_SprayCan_Base;
```

That base is infrastructure and is not itself a normal loot/spawn item.

Each paint pack provides the actual spawnable can classes for the finishes it ships. PackKit should generate these classes rather than requiring authors to maintain repetitive config manually. Conceptually:

```cpp
class MyPack_SprayCan_FDE : PaintZ_SprayCan_Base
{
    scope = 2;
    displayName = "PaintZ - Flat Dark Earth";
    paintzFinish = "netcop.military.fde";
    hiddenSelectionsTextures[] = {"\\MyPack\\data\\cans\\fde_co.paa"};
};
```

The subclass should contain only the data needed to identify and present that finish. Runtime painting behaviour remains inherited from PaintZ.

Having one lightweight can class per finish is intentional. It integrates naturally with DayZ loot configuration, admin tools and other classname-based systems without creating painted subclasses for every target weapon/item.

## Finish identity

PackKit should distinguish between:

1. a **canonical machine identity** that is globally collision-resistant across independent packs, for example `netcop.military.fde`; and
2. a **human-facing paint code**, such as `PZ-S-FDE`.

The canonical identity is the persistence/registration identity. The visible code is presentation metadata.

The exact manifest field names and validation rules will be finalized with the pack schema. Do not make the short visible code the only global identity once third-party packs are supported.

## Can design and custom branding

PaintZ should remain visually recognizable even when the finish comes from a third-party pack.

The standard PackKit-generated can should retain PaintZ-controlled elements such as:

- the PaintZ logo/identity;
- label geometry and proportions;
- typography rules;
- category/badge placement;
- standard margins and footer treatment;
- the physical can model and UV mapping.

A pack may supply content for defined fields such as:

- finish name;
- visible paint ID;
- finish category/type;
- publisher name;
- a small publisher mark/logo;
- collection/series name or similarly restrained secondary text.

Publisher branding should remain subordinate to PaintZ branding. Normal paint packs should not receive arbitrary control over label coordinates, fonts, layout geometry or the physical can model.

PackKit should enforce this through templates and validation rather than relying on authors to reproduce the design manually.

## What a normal paint pack should not control

A normal pack should be primarily **data + assets**. It should not redefine PaintZ mechanics such as:

- action duration or consumption rules;
- painting/stripping actions;
- persistence implementation;
- synchronization;
- target eligibility logic;
- animation/sound behaviour;
- core can condition/damage mechanics;
- core PaintZ UI behaviour.

Something that genuinely needs new runtime behaviour is a PaintZ extension/mod, not merely a paint pack.

## Design goals

PackKit should be:

- **deterministic** — the same inputs produce the same generated outputs;
- **validation-first** — bad IDs, paths, missing assets and incompatible metadata fail clearly;
- **repeatable** — generated files are rebuilt, not hand-maintained;
- **third-party friendly** — no assumptions that all packs are owned by netcopdev;
- **PaintZ-independent at authoring time where practical** — PackKit should use a documented contract/templates rather than copy runtime implementation logic;
- **Windows-friendly** — the primary DayZ authoring/build environment is Windows and DayZ Tools;
- **extensible** — adding future finish kinds or generated assets should not require redesigning existing packs unnecessarily.

## Non-goals

PackKit must not become:

- a second implementation of the PaintZ runtime;
- a registry of specific compatible weapons/items;
- a system that generates painted subclasses for target items;
- a requirement for server-side runtime generation of textures;
- an unrestricted skinning framework that abandons the standard PaintZ can design.

## Near-term direction

The first implementation work should establish the pack contract around the capabilities already proven by the existing PaintZ generator, then migrate/refactor those capabilities here without breaking generated PaintZ assets unexpectedly.

Expected early milestones are:

1. define a versioned pack/finish manifest;
2. extract reusable can/surface generation from `PaintZ/tools/paintzgen`;
3. generate standardized finish-specific can classes;
4. generate PaintZ finish-registration data;
5. validate IDs, paths, source artwork and branding constraints;
6. create a small reference pack and deterministic regression tests;
7. document the handoff from PackKit output to a DayZ PBO/release build.

## License

License is not yet declared in this repository.
