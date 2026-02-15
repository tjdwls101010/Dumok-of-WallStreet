#!/usr/bin/env python3
"""
PDF to Markdown Converter

PDF를 마크다운으로 변환합니다.
이미지 설명 생성은 Describe_Images 스킬을 사용하세요.

Usage:
    python pdf_to_md.py -p "path/to/file.pdf"

Example:
    python pdf_to_md.py -p "chapter1.pdf"
"""

import argparse
import re
from pathlib import Path
from typing import Tuple

import pymupdf4llm

# ==================== 설정값 ====================
DPI = 150  # 이미지 해상도
IMAGE_FORMAT = "png"  # 이미지 포맷 (png, jpg)
FILE_ENCODING = "utf-8"


def parse_args():
    """CLI 인자 파싱"""
    parser = argparse.ArgumentParser(
        description="PDF를 마크다운으로 변환합니다."
    )
    parser.add_argument(
        "-p", "--pdf",
        required=True,
        help="변환할 PDF 파일 경로"
    )
    return parser.parse_args()


def convert_pdf_to_markdown(
    pdf_path: str,
    dpi: int = 150,
    image_format: str = "png"
) -> Tuple[str, str]:
    """
    PDF를 마크다운으로 변환

    PDF 경로가 ./folder1/folder2/file.pdf이면:
    - 출력 폴더: ./folder1/folder2/ (PDF와 같은 폴더)
    - 마크다운: ./folder1/folder2/file.md
    - 이미지: ./folder1/folder2/images/ (공통 폴더)

    Returns:
        (output_folder, markdown_file_path)
    """
    # 파일 존재 확인
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")

    # 출력 폴더는 PDF와 같은 폴더
    pdf_stem = pdf_file.stem
    output_folder = pdf_file.parent

    # 마크다운 파일 경로
    markdown_file = output_folder / f"{pdf_stem}.md"

    # 이미지 디렉토리 (공통 images 폴더)
    image_dir_abs = output_folder / "images"
    image_dir_abs.mkdir(parents=True, exist_ok=True)

    image_dir_relative = str(image_dir_abs)

    print(f"PDF 변환 시작...")
    print(f"입력: {pdf_path}")
    print(f"출력 폴더: {output_folder}")
    print(f"마크다운: {markdown_file}")
    print(f"이미지 저장: {image_dir_abs}")

    # PDF 변환
    markdown_text = pymupdf4llm.to_markdown(
        str(pdf_file),
        page_chunks=False,
        write_images=True,
        image_path=image_dir_relative,
        image_format=image_format,
        dpi=dpi
    )

    # 이미지 경로를 상대 경로로 수정
    print(f"\n이미지 경로를 상대 경로로 수정 중...")

    folder_prefix = str(output_folder.resolve())

    markdown_text = re.sub(
        rf'!\[([^\]]*)\]\({re.escape(folder_prefix)}/images/',
        r'![\1](images/',
        markdown_text
    )

    markdown_text = re.sub(
        rf'!\[([^\]]*)\]\({re.escape(str(output_folder))}/images/',
        r'![\1](images/',
        markdown_text
    )

    markdown_text = re.sub(
        r'!\[([^\]]*)\]\(.*/images/images/',
        r'![\1](images/',
        markdown_text
    )

    print(f"이미지 경로 수정 완료")

    # 마크다운 파일 저장
    markdown_file.write_text(markdown_text, encoding="utf-8")

    file_size_kb = len(markdown_text.encode("utf-8")) / 1024
    print(f"\n변환 완료!")
    print(f"마크다운: {markdown_file}")
    print(f"파일 크기: {file_size_kb:.2f} KB")
    print(f"텍스트 길이: {len(markdown_text):,} 문자")

    return str(output_folder), str(markdown_file)


def main():
    """메인 함수"""
    args = parse_args()

    print("\n" + "="*60)
    print("PDF to Markdown Converter")
    print("="*60)
    print(f"PDF: {args.pdf}")
    print("="*60 + "\n")

    # PDF -> 마크다운 변환
    output_folder, markdown_file = convert_pdf_to_markdown(
        pdf_path=args.pdf,
        dpi=DPI,
        image_format=IMAGE_FORMAT
    )

    print("\n" + "="*60)
    print("변환 완료!")
    print(f"결과 파일: {markdown_file}")
    print("\n[참고] 이미지 설명 생성은 Describe_Images 스킬을 사용하세요:")
    print(f"  python Describe_Images.py \"{markdown_file}\"")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
