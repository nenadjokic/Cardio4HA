Auto-release: commit, bump patch version, push, and create GitHub release.

## Instructions

1. Run `git status` and `git diff` to see all changes.
2. Read the current version from `custom_components/cardio4ha/manifest.json` (the `"version"` field).
3. Increment the **patch** version only (e.g. 1.1.0 → 1.1.1, 1.1.1 → 1.1.2). Never bump minor or major unless the user explicitly says so.
4. Update the version in ALL of these files:
   - `custom_components/cardio4ha/manifest.json` → `"version": "X.Y.Z"`
   - `custom_components/cardio4ha/sensor.py` → `sw_version` string
   - `custom_components/cardio4ha/__init__.py` → version string in log messages (e.g. "Setting up Cardio4HA vX.Y.Z")
   - `custom_components/cardio4ha/panel/cardio4ha-panel.js` → `PANEL_VERSION` constant
   - `custom_components/cardio4ha/__init__.py` → cache bust query param `?v=XYZ` (no dots, e.g. v1.1.2 → ?v=112)
5. Stage all changed files (specific files, not `git add -A`).
6. Write a concise commit message summarizing the changes. End with `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`.
7. Create a git tag `vX.Y.Z`.
8. Push the commit and tag to origin.
9. Create a GitHub release using `gh release create vX.Y.Z --title "vX.Y.Z" --notes "..."` with a short changelog based on the commit diff.
10. Output the release URL when done.
