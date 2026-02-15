#!/bin/bash
# batch.sh - 폴더 내 마크다운 파일들을 10초 간격으로 백그라운드 실행
# 사용법: ./batch.sh <폴더경로> [추가프롬프트]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESTRUCTURE_SCRIPT="$SCRIPT_DIR/restructure.sh"
INTERVAL_SECONDS=10

FOLDER="$1"
ADDITIONAL_PROMPT="$2"

# 폴더 검증
if [ ! -d "$FOLDER" ]; then
    echo "[ERROR] 폴더를 찾을 수 없습니다: $FOLDER"
    exit 1
fi

# 파일 목록 (오름차순 정렬, Restructured_/backup 제외)
FILES=$(find "$FOLDER" -maxdepth 1 -name "*.md" -type f \
    | grep -v ".backup" \
    | grep -v "Restructured_" \
    | sort -V)

if [ -z "$FILES" ]; then
    echo "[INFO] 처리할 파일이 없습니다."
    exit 0
fi

FILE_COUNT=$(echo "$FILES" | wc -l | tr -d ' ')
echo "[INFO] 처리할 파일 수: $FILE_COUNT"
echo "[INFO] ${INTERVAL_SECONDS}초 간격으로 백그라운드 실행 시작"
echo ""

CURRENT=0
while IFS= read -r file; do
    CURRENT=$((CURRENT + 1))
    echo "[$CURRENT/$FILE_COUNT] 🩷시작: $(basename "$file")"

    # 백그라운드 실행 (완료 대기 없음)
    if [ -n "$ADDITIONAL_PROMPT" ]; then
        "$RESTRUCTURE_SCRIPT" "$file" "$ADDITIONAL_PROMPT" < /dev/null &
    else
        "$RESTRUCTURE_SCRIPT" "$file" < /dev/null &
    fi

    # 마지막 파일이 아니면 10초 대기
    if [ $CURRENT -lt $FILE_COUNT ]; then
#        echo "[INFO] 10초 대기 후 다음 파일 시작..."
        sleep $INTERVAL_SECONDS
    fi
done <<< "$FILES"

echo ""
echo "[INFO] 🧡모든 파일 실행 시작 완료. 백그라운드 작업 완료 대기 중..."
wait
echo "[INFO] 💛모든 작업 완료!"
