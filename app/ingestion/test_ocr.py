from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Users\Rajvinder.kaur\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
)

img = Image.open("cropped.png")
print("Mode:", img.mode)
print("Size:", img.size)

img = img.convert("L")

img = img.point(
    lambda x: 0 if x < 180 else 255,
    mode="1"
)

img.save("threshold.png")

text = pytesseract.image_to_string(
    img,
    lang="eng",
    config="--psm 6"
)

print(repr(text))