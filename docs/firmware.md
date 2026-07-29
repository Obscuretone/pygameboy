# Boot firmware policy

PyGameBoy does not distribute Nintendo boot firmware. Users may supply a
256-byte DMG boot ROM they are legally entitled to use:

```bash
pygameboy --boot-rom /path/to/DMG_ROM.bin /path/to/game.gb
```

`DMG_ROM.bin` is ignored by Git. Tests and CI must continue to work without it.

## Maintainer history cleanup

Deleting firmware in a new commit does not remove it from older Git objects. If
a proprietary image was ever pushed, repository maintainers should coordinate a
history rewrite before publicizing the repository:

```bash
git filter-repo --path DMG_ROM.bin --invert-paths
git push --force --all
git push --force --tags
```

This rewrites commit IDs for every affected branch and tag. Coordinate with
collaborators first, revoke or replace existing clones where appropriate, and
follow the hosting provider's process for purging cached objects. Do not run
these commands as part of normal development or CI.
