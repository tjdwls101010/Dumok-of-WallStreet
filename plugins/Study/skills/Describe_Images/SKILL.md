---
name: Describe_Images
description: Convert Wiki-style image links to Markdown format with AI-generated descriptions. Use when preprocessing markdown files for PPT generation, converting ![[image.png]] to ![description](path) format, or enabling text-based image understanding.
allowed-tools: Read, Bash, Glob
version: 2.1.0
updated: 2026-02-27
status: active
color: green
---

# Describe_Images

Wiki 이미지 링크(`![[img.png]]`)를 AI 설명이 포함된 Markdown 형식(`![description](path)`)으로 변환한다.

**2-step 워크플로우:**
```
![[image.png]]  ──Convert_Image-Link.py──▶  ![](path/image.png)  ──Describe_Images.py──▶  ![AI description](path/image.png)
```

> PPT 워크플로우에서는 `/ppt` 커맨드가, Book 워크플로우에서는 `/Book` 커맨드가 이 스킬을 자동으로 호출한다.

---

## Setup

스크립트 실행 전 가상환경이 준비되어 있는지 확인한다.

### 자동 환경 확인 (매 실행 전)

```bash
SKILL_DIR="<이 SKILL.md가 위치한 디렉토리의 절대경로>"
cd "$SKILL_DIR/Scripts"

# venv가 없으면 생성
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
else
  source .venv/bin/activate
fi
```

### API Key 설정

`Scripts/.env` 파일에 키를 설정한다. 없으면 `.env.example`을 복사:

```bash
cp .env.example .env  # 후 키 입력
```

`.env` 로딩 우선순위: CWD의 `.env` → `Scripts/.env` (폴백)

---

## Execution

모든 명령어는 venv 활성화 후 `Scripts/` 디렉토리에서 실행한다.

| 작업 | 명령어 |
|------|--------|
| Wiki→Markdown 변환 | `python3 Convert_Image-Link.py "{markdown_path}"` |
| Wiki→Markdown (미리보기) | `python3 Convert_Image-Link.py "{markdown_path}" -n` |
| AI 설명 생성 (GPT) | `python3 Describe_Images.py "{markdown_path}" -m gpt` |
| AI 설명 생성 (Gemini) | `python3 Describe_Images.py "{markdown_path}" -m gemini` |
| AI 설명 (미리보기) | `python3 Describe_Images.py "{markdown_path}" -n` |

---

## Input/Output

**Input** (Wiki-style):
```markdown
![[image.png]]
![[folder/diagram.jpg]]
```

**After Convert_Image-Link.py**:
```markdown
![](vault-relative/path/to/image.png)
![](folder/diagram.jpg)
```

**After Describe_Images.py**:
```markdown
![Detailed AI-generated description](vault-relative/path/to/image.png)
![System architecture diagram showing...](folder/diagram.jpg)
```

출력은 마크다운 파일을 in-place 수정한다.

---

## CLI Reference

### Convert_Image-Link.py

| 옵션 | 설명 |
|------|------|
| `-n, --dry-run` | 파일 수정 없이 변환 내역 미리보기 |

### Describe_Images.py

| 옵션 | 설명 |
|------|------|
| `-n, --dry-run` | 파일 수정 없이 AI 설명 결과를 JSON 출력 |
| `-m, --model` | AI 모델 선택: `gpt` (기본) 또는 `gemini` |

### 설정 상수 (Describe_Images.py)

```python
CONTEXT_CHARS = 500   # 이미지 앞뒤 컨텍스트 추출 길이
MAX_RETRIES = 3       # API 호출 재시도 횟수
CONCURRENT = 20       # 최대 병렬 이미지 분석 수
```

### 지원 이미지 형식

png, jpg, jpeg, gif, webp, svg, bmp, tiff, ico

---

## Path Resolution

### Vault Root 탐지

두 스크립트 모두 동일한 `find_vault_root()` 사용:
1. 마크다운 파일의 상위 디렉토리에서 `.obsidian/` 탐색
2. 없으면 `VAULT_ROOT` 환경변수 폴백

### Convert_Image-Link.py 이미지 경로 해석

vault 전체 이미지 인덱스(`{파일명: 절대경로}`)를 먼저 빌드한 후:
1. 경로에 `/` 포함 → vault-relative 경로로 직접 사용
2. 파일명이 인덱스에 존재 → 인덱스의 절대경로에서 vault-relative 경로 계산
3. 둘 다 아니면 → 건너뜀 (경고 출력)

### Describe_Images.py 이미지 경로 해석

`resolve_image_path()` 함수:
1. 절대경로 → 그대로 사용
2. 마크다운 파일 기준 상대경로 → 존재하면 사용
3. Vault 루트 기준 상대경로 → 존재하면 사용

---

## Troubleshooting

| 증상 | 해결 |
|------|------|
| API Key Not Found | `.env` 파일이 CWD 또는 `Scripts/`에 있는지 확인. `OPENAI_API_KEY` 또는 `GOOGLE_API_KEY` 설정 확인 |
| Image Not Found | 이미지 파일이 vault에 존재하는지, 확장자가 지원 형식인지 확인. `-n` 모드로 경로 확인 |
| Empty Descriptions | API 연결 및 키 할당량 확인. 콘솔 에러 메시지 참조 |
| Partial Processing | 스크립트 재실행 시 이미 설명이 있는 이미지는 건너뜀. 재실행으로 나머지 처리 |
| venv 문제 | `rm -rf .venv && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` |
