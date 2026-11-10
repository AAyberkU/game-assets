# Contributing packs

This fork of [eturner58/game-assets](https://github.com/eturner58/game-assets)
is the asset corpus behind [kenney-agent](https://github.com/AAyberkU/kenney-agent),
which indexes it so coding agents can search Kenney's assets. PRs that add
missing or newer Kenney packs are welcome.

## Packs we are missing

- [Tiny City](https://kenney.nl/assets/tiny-city)
- [Mini Shop](https://kenney.nl/assets/mini-shop) (replaces Mini Market)
- [Tiny Factory](https://kenney.nl/assets/tiny-factory)
- [Scribble Platformer Expansion](https://kenney.nl/assets/scribble-platformer-expansion)
- [Skyboxes Space](https://kenney.nl/assets/skyboxes-space)
- [Tower Defense (Top-Down)](https://kenney.nl/assets/tower-defense-top-down)
- [UI Pack: RPG Expansion](https://kenney.nl/assets/ui-pack-rpg-expansion)
- Updated versions of Mini Skate, City Kit Industrial and City Kit Roads

## How to add a pack

1. Download the pack from its kenney.nl page.
2. Unzip it into `kenney/<section>/<Pack Name>/`:
   - `<section>` is one of the existing folders: `2D assets`, `3D assets`,
     `Audio`, `Icons`, `UI assets`, `Goodies`, `Other`.
   - `<Pack Name>` is the name shown on kenney.nl (`Tiny City`), so
     kenney-agent can match it to the pack's page.
   - Keep the zip's own layout inside the folder, including `License.txt`.
3. For 3D packs, keep the GLB/glTF files and drop the other model formats
   (FBX, OBJ, DAE), as the rest of the corpus does. Keep FBX only when the pack
   ships no GLB or glTF.
4. Updating a pack that is already here: replace its folder's contents.
5. Open a PR with the kenney.nl link and the pack version.

## Rules

- Kenney packs only, and only CC0 ones. Nothing paid or under another licence.
- Do not edit `catalog/`: it is eturner58's catalogue. kenney-agent finds new
  pack folders by itself; nothing else needs to change.
- No single file over 100 MB (GitHub's limit).

After a merge, kenney-agent users get the pack with `git pull` and
`node bin/assets setup --update`.
