import os
import logging
import threading
from abc import ABC, abstractmethod
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


def pdf_to_images(pdf_path: str, dpi: int | None = None) -> list[str]:
    """Convert PDF pages to PNG images using PyMuPDF. Returns list of image paths."""
    import fitz  # PyMuPDF

    if dpi is None:
        dpi = settings.OCR_DPI

    doc = fitz.open(pdf_path)
    image_paths = []
    base = Path(pdf_path).stem

    out_dir = os.path.join(os.path.dirname(pdf_path), f"{base}_pages")
    os.makedirs(out_dir, exist_ok=True)

    for page_num in range(len(doc)):
        page = doc[page_num]
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img_path = os.path.join(out_dir, f"page_{page_num + 1}.png")
        pix.save(img_path)
        image_paths.append(img_path)

    doc.close()
    return image_paths


class OCRService(ABC):
    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """Extract text from a PDF or image file."""
        ...


class PaddleOCRService(OCRService):
    def __init__(self):
        import paddle
        paddle.set_flags({"FLAGS_use_mkldnn": False})

        from paddleocr import PaddleOCR

        self._ocr = PaddleOCR(use_angle_cls=True, lang="ar", enable_mkldnn=False)
        self._lock = threading.Lock()

    def extract_text(self, file_path: str) -> str:
        if file_path.lower().endswith(".pdf"):
            image_paths = pdf_to_images(file_path)
        else:
            image_paths = [file_path]

        all_text = []
        for img_path in image_paths:
            with self._lock:
                # Use predict() API (PaddleOCR v3+). The old .ocr() method
                # returns empty results in newer versions.
                for result in self._ocr.predict(img_path):
                    res = result.json.get("res", result.json) if isinstance(result.json, dict) else {}
                    if isinstance(res, dict) and "rec_texts" in res:
                        all_text.extend(res["rec_texts"])

        return "\n".join(all_text)


class MockOCRService(OCRService):
    """Returns fixture text files instead of running real OCR."""

    FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")

    def extract_text(self, file_path: str) -> str:
        # Try to match fixture by filename pattern
        basename = Path(file_path).stem.lower()

        fixture_map = {
            "cid": "civil_id.txt",
            "civil": "civil_id.txt",
            "civid": "civil_id.txt",
            "sloom": "civil_id.txt",
            "statement": "bank_statement.txt",
            "kib": "bank_statement.txt",
            "original": "bank_statement.txt",
            "salary": "salary_transfer.txt",
        }

        fixture_file = None
        for keyword, fname in fixture_map.items():
            if keyword in basename:
                fixture_file = fname
                break

        if fixture_file is None:
            fixture_file = "civil_id.txt"
            logger.warning(f"No fixture match for '{basename}', defaulting to civil_id.txt")

        fixture_path = os.path.join(self.FIXTURE_DIR, fixture_file)
        if os.path.exists(fixture_path):
            with open(fixture_path, "r", encoding="utf-8") as f:
                return f.read()

        logger.warning(f"Fixture file not found: {fixture_path}")
        return f"[Mock OCR output for {basename}]"


_ocr_service_instance: OCRService | None = None
_ocr_service_lock = threading.Lock()


def get_ocr_service() -> OCRService:
    """Return a singleton OCR service instance. Models load once and are reused."""
    global _ocr_service_instance
    if _ocr_service_instance is None:
        with _ocr_service_lock:
            if _ocr_service_instance is None:
                if settings.OCR_PROVIDER == "paddleocr":
                    _ocr_service_instance = PaddleOCRService()
                else:
                    _ocr_service_instance = MockOCRService()
    return _ocr_service_instance
