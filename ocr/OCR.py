from paddleocr import PaddleOCRVL
from datetime import date

day = date.today()

pipeline = PaddleOCRVL()
results = pipeline.predict(
    "hydratation.pdf",
    use_layout_detection=True,
    use_chart_recognition=True,
    format_block_content=True,
    use_doc_preprocessor=False,
    use_ocr_for_image_block=False,
)


for res in results:
    res.save_to_json(f"ocr/runs/{day}_vl16/raw/")