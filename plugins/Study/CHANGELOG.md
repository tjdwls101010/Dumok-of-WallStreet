# Changelog

## [1.1.0] - 2026-02-16

### Changed
- Replaced all hardcoded absolute paths with portable relative paths across 9 files
- SKILL.md files: `{skill_scripts_dir}/`, `.claude/skills/X/...` → skill-root-relative `scripts/` or `Scripts/`
- Command .md files: Absolute paths → skill-relative `<Skill_name>/scripts/` references
- `commands/Book.md`: `VAULT_PATH` from hardcoded to `$(pwd)` auto-detection at command start
- `Describe_Images.py`, `Convert_Image-Link.py`: `VAULT_ROOT` from hardcoded path to `.obsidian/` directory auto-detection
- Cross-skill references in `Prepare_Book/SKILL.md` now use `<Describe_Images_skill>/Scripts` pattern

## [1.0.0] - 2026-01-26

### Added
- Initial release with PDF processing, image description, presentation generation, NotebookLM integration, and content restructuring
