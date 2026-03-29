# Development Guide

## Plugin Modification Checklist

When any modification is made to a plugin (skills, commands, scripts, or configuration), you MUST update ALL of the following files:

1. **`plugin.json`** (`.claude/.claude-plugin/plugin.json`)
   - Bump `version` if the change is user-facing
   - Update `description`, `skills`, or `commands` arrays if added or removed

2. **`marketplace.json`** (`.claude-plugin/marketplace.json` at repository root)
   - Sync plugin `version` with plugin.json
   - Update `description`, `skills`, or `commands` arrays to match
   - Bump top-level `metadata.version` to reflect the overall marketplace update

3. **`README.md`** (repository root)
   - Sync plugin `version` in the summary section
   - Update component tables (Type, Description) if skills, commands, or agents were added, removed, or renamed
   - Update the Structure tree if directory layout changed

## Git Commit Convention

Git commit이 변경 이력의 단일 소스(Single Source of Truth). 의미 있는 작업 단위마다 커밋한다.

### Commit Message Format

```
<category>(<component>): <description>

<optional body — why this change was made>
```

- **category**: `feat`, `fix`, `refactor`, `docs`, `chore`
- **component**: 변경 대상 (e.g., `serenity`, `minervini`, `plugin`, `principles`)
- **description**: 변경 내용 1줄 요약 (영어, 소문자 시작, 마침표 없음)

### Examples

```
feat(serenity): add iv_tier classification to iv_context module
fix(minervini): fix sys.path for trend_template import in modules/
refactor(serenity): flatten directory structure to pipeline/ + modules/
docs(principles): add Structural Clarity principle (§2.8)
chore(plugin): bump version to 9.0.0
```

### When to Commit

- **[HARD] 커밋 전 반드시 사용자 승인 필요** — 사용자가 명시적으로 커밋을 요청한 경우에만 수행
- 사용자가 커밋을 요청하면, 적절한 논리적 단위별로 분리하여 각각 적절한 메시지와 함께 커밋
- 하나의 논리적 변경 = 하나의 커밋
- 여러 파일이 함께 변경되더라도 같은 목적이면 하나의 커밋
- 검증(validation) 통과 후 커밋 — 깨진 상태로 커밋하지 않음
- 버전 범프(plugin.json, marketplace.json, README.md)는 실제 변경과 같은 커밋에 포함

### When to Push

- 사용자가 명시적으로 요청할 때만 push
- 작업 중간에 push하지 않음 — 검증 완료 후에만
