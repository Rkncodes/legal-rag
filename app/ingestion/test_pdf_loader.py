from pdf_loader import load_pdf

pages = load_pdf("data/pdfs/testfile6.pdf")

for page in pages:
    print(page)