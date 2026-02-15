#!/usr/bin/env python3
"""
Convert Wiki-style image links to Markdown-style image links.

Wiki style:  ![[image.png]]
Markdown style:  ![](path/image.png)

This script ONLY converts link format, WITHOUT generating AI descriptions.
For AI descriptions, use Describe_Images.py after this script.

Usage:
    python Convert_Image-Link.py <markdown_file>
    python Convert_Image-Link.py <markdown_file> -n  # dry-run

Example:
    python Convert_Image-Link.py "document.md"
"""

import argparse
import re
import sys
from pathlib import Path

# ==================== 설정값 ====================
# Vault 루트 경로 (고정)
VAULT_ROOT = Path("/Users/seongjin/Documents/⭐성진이의 옵시디언")

FILE_ENCODING = "utf-8"

# 패턴
WIKI_PATTERN = r'!\[\[([^\]]+\.(?:png|jpg|jpeg|gif|webp|svg|bmp|tiff|ico))\]\]'


def build_image_index(vault_root: Path) -> dict[str, Path]:
    """vault 전체에서 이미지 파일을 검색하여 {파일명: 절대경로} 인덱스 생성."""
    extensions = ('png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp', 'tiff', 'ico')
    index = {}
    for ext in extensions:
        for img_path in vault_root.rglob(f'*.{ext}'):
            index[img_path.name] = img_path
        for img_path in vault_root.rglob(f'*.{ext.upper()}'):
            index[img_path.name] = img_path
    return index


def get_vault_relative_path(image_path: Path) -> str:
    """vault 루트 기준 상대경로 반환."""
    return str(image_path.relative_to(VAULT_ROOT))


def convert_wiki_links_to_markdown(file_path: Path, image_index: dict[str, Path], dry_run: bool = False) -> int:
    """
    Wiki link를 Markdown 형식으로 변환

    Args:
        file_path: 마크다운 파일 경로
        image_index: 이미지 인덱스 (파일명 -> 절대경로)
        dry_run: True면 파일 수정 없이 미리보기만

    Returns:
        변환된 링크 수
    """
    content = file_path.read_text(encoding=FILE_ENCODING)

    matches = list(re.finditer(WIKI_PATTERN, content, re.IGNORECASE))
    if not matches:
        print("변환할 Wiki 링크가 없습니다.")
        return 0

    converted_count = 0
    warnings = []
    conversions = []

    # 역순으로 처리 (위치 밀림 방지)
    for match in reversed(matches):
        filename = match.group(1)

        # 경로 결정
        if '/' in filename or '\\' in filename:
            vault_path = filename
        elif filename in image_index:
            vault_path = get_vault_relative_path(image_index[filename])
        else:
            warnings.append(f"  파일 없음: {filename}")
            continue

        # 변환: ![[file]] → ![](path)
        new_text = f"![]({vault_path})"
        conversions.append((match.group(0), new_text))

        if not dry_run:
            content = content[:match.start()] + new_text + content[match.end():]
        converted_count += 1

    # 파일 저장 (dry-run이 아닐 때만)
    if not dry_run and converted_count > 0:
        file_path.write_text(content, encoding=FILE_ENCODING)

    # 결과 출력
    print(f"\n{'='*60}")
    print(f"Wiki 링크 변환 {'미리보기' if dry_run else '완료'}")
    print(f"{'='*60}")
    print(f"파일: {file_path}")
    print(f"변환: {converted_count}개")

    if conversions:
        print(f"\n변환 내역:")
        for old, new in conversions[:10]:
            print(f"  {old}")
            print(f"    → {new}")
        if len(conversions) > 10:
            print(f"  ... 외 {len(conversions) - 10}개")

    if warnings:
        print(f"\n경고:")
        for warning in warnings:
            print(warning)

    print(f"{'='*60}\n")

    return converted_count


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='Convert Wiki-style image links (![[image.png]]) to Markdown-style (![](path))'
    )
    parser.add_argument(
        'file',
        type=str,
        help='Path to the markdown file to convert'
    )
    parser.add_argument(
        '-n', '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying the file'
    )

    args = parser.parse_args()

    # Resolve file path
    file_path = Path(args.file)

    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    if not file_path.is_file():
        print(f"Error: Not a file: {file_path}", file=sys.stderr)
        sys.exit(1)

    # Build image index
    print("Building image index...")
    image_index = build_image_index(VAULT_ROOT)
    print(f"Found {len(image_index)} image files")

    # Convert
    converted = convert_wiki_links_to_markdown(file_path, image_index, dry_run=args.dry_run)

    if args.dry_run:
        print("(Dry-run 모드: 파일이 수정되지 않았습니다)")
    else:
        print(f"완료: {file_path}")


if __name__ == '__main__':
    main()
