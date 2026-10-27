"""PPTX 슬라이드를 PNG로 렌더링하는 미리보기 도구.

PowerPoint COM 자동화 대신 LibreOffice(headless)로 PDF를 만든 뒤 PyMuPDF로 PNG를 뽑음.
PowerPoint는 컴퓨터 전체에서 한 프로세스만 떠서, COM으로 붙으면 사용자가 열어 둔 창과 섞이고
`Quit()` 한 번에 사용자 작업까지 닫히는 문제가 있었음 (2026-10 크래시 원인).

사용법:
    python scripts/render-pptx.py deck.pptx [--out 출력폴더] [--width 1600]

의존성: LibreOffice(`soffice`), `pip install pymupdf`
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import fitz  # PyMuPDF

SOFFICE_CANDIDATES = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    "/usr/bin/soffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
]
CONVERT_TIMEOUT_SEC = 180


def find_soffice() -> str:
    """soffice 실행 파일 경로 반환. 없으면 설치 안내와 함께 종료."""
    found = shutil.which("soffice")
    if found:
        return found
    for candidate in SOFFICE_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    sys.exit("soffice를 찾지 못함. LibreOffice 설치 필요: winget install TheDocumentFoundation.LibreOffice")


def convert_to_pdf(soffice: str, deck: Path, out_dir: Path) -> Path:
    """PPTX를 PDF로 변환하고 PDF 경로 반환."""
    # 전용 임시 프로필을 써야 사용자가 열어 둔 LibreOffice 창에 붙지 않음 (COM 문제와 같은 함정 회피)
    with tempfile.TemporaryDirectory(prefix="lo-profile-") as profile:
        cmd = [
            soffice,
            f"-env:UserInstallation={Path(profile).as_uri()}",
            "--headless", "--norestore", "--nolockcheck",
            "--convert-to", "pdf", "--outdir", str(out_dir), str(deck),
        ]
        # 손상된 파일에서 변환이 멈춰도 무한 대기하지 않도록 상한을 둠
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=CONVERT_TIMEOUT_SEC)
    pdf = out_dir / f"{deck.stem}.pdf"
    if result.returncode != 0 or not pdf.exists():
        sys.exit(f"PDF 변환 실패 (exit={result.returncode})\n{result.stdout}\n{result.stderr}")
    return pdf


def render_pages(pdf: Path, out_dir: Path, width: int) -> list[Path]:
    """PDF 각 페이지를 지정 너비의 PNG로 저장하고 경로 목록 반환."""
    images: list[Path] = []
    # LibreOffice PDF의 접근성 태그 구조 경고("No common ancestor...")는 렌더링 결과와 무관해 숨김
    fitz.TOOLS.mupdf_display_errors(False)
    with fitz.open(pdf) as doc:
        for index, page in enumerate(doc, start=1):
            zoom = width / page.rect.width
            image = out_dir / f"slide-{index}.png"
            page.get_pixmap(matrix=fitz.Matrix(zoom, zoom)).save(image)
            images.append(image)
    return images


def main() -> None:
    parser = argparse.ArgumentParser(description="PPTX 슬라이드를 PNG로 렌더링 (LibreOffice 사용)")
    parser.add_argument("deck", type=Path, help="렌더링할 .pptx 경로")
    parser.add_argument("--out", type=Path, help="출력 폴더 (기본값: {파일명}-preview)")
    parser.add_argument("--width", type=int, default=1600, help="PNG 가로 픽셀 (기본값: 1600)")
    args = parser.parse_args()

    deck = args.deck.resolve()
    if not deck.exists():
        sys.exit(f"파일 없음: {deck}")
    out_dir = (args.out or deck.with_name(f"{deck.stem}-preview")).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    pdf = convert_to_pdf(find_soffice(), deck, out_dir)
    images = render_pages(pdf, out_dir, args.width)
    print(f"PDF: {pdf}")
    print(f"PNG {len(images)}장: {out_dir}")


if __name__ == "__main__":
    main()
