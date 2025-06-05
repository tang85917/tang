from weasyprint import HTML, CSS

# HTMLファイルとCSSを読み込んでPDFに変換
html = HTML('resume.html')
css = CSS('style.css')

# PDF出力（ファイル名を変更可）
output_filename = '履歴書_湯涛.pdf'
html.write_pdf(output_filename, stylesheets=[css])

print(f'✅ PDF出力完了：{output_filename}')
