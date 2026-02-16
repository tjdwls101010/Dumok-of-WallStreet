# Changelog

## 2026-02-16

### Added
- **[HARD] Truncation Recovery Rule** in `SKILL.md` — Prevents cascading failures when `extract_docstring.py` output exceeds 30KB and gets truncated by the system. Forces Claude to read the saved full-output file before executing any script, eliminating subcommand guessing from partial previews.

### Changed
- **Batch Discovery Rule** — `extract_docstring.py` 호출 시 최대 5개 스크립트 배치 제한 추가. 카테고리 내 스크립트가 10개 이상인 경우에도 토큰 소비를 적절히 관리.
