import os
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path

from flask import Flask, render_template, request, send_file, jsonify, Response, redirect
from werkzeug.utils import secure_filename
from PIL import Image
import fitz

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
BASE = Path(tempfile.gettempdir()) / 'convertnest'
BASE.mkdir(exist_ok=True)
ALLOWED_IMAGES = {'jpg', 'jpeg', 'png', 'webp'}
SITE_NAME = 'ConvertNest'

SEO_PAGES = {
    'image-converter': {
        'path': '/image-converter',
        'title': 'JPG to PNG & PNG to JPG Converter Online — Free | ConvertNest',
        'description': 'Convert JPG, JPEG, PNG and WEBP images to PNG or JPEG online for free. Change the output format and quality in one tool.',
        'h1': 'JPG ↔ PNG Image Converter',
        'intro': 'Switch between PNG and JPEG in one clean converter. Upload one or many JPG, PNG or WEBP images and choose your output format.',
        'section_title': 'Change image format online',
        'paragraphs': [
            'ConvertNest lets you change common image formats without installing desktop software. Choose PNG or JPEG as the output format and convert one or multiple images in the same tool.',
            'Multiple images are packaged into a ZIP download. The upload limit is 50 MB per request and up to 30 images can be converted at once.'
        ],
        'steps': ['Choose your images.', 'Switch the output between PNG and JPEG.', 'Convert and download the result or ZIP.'],
        'faq': [
            {'q': 'Can I convert JPG to PNG?', 'a': 'Yes. Choose PNG as the output format.'},
            {'q': 'Can I convert PNG to JPG?', 'a': 'Yes. Choose JPEG as the output format. Transparent areas are flattened onto white because JPEG does not support transparency.'},
            {'q': 'Can I convert multiple images?', 'a': 'Yes. Up to 30 supported images can be converted in one job.'},
        ],
    },
    'pdf-converter': {
        'path': '/pdf-converter',
        'title': 'PDF ↔ JPG Converter Online — Free | ConvertNest',
        'description': 'Convert PDF to JPG or JPG, PNG and WEBP images to PDF in one free online converter.',
        'h1': 'PDF ↔ JPG Converter',
        'intro': 'One PDF tool, two directions. Switch between PDF to JPG and images to PDF without opening a different converter.',
        'section_title': 'Convert PDF and images in either direction',
        'paragraphs': [
            'Convert a PDF into JPG page images, or combine JPG, PNG and WEBP images into a single PDF. The direction is controlled by one simple switch.',
            'PDF to JPG returns all pages together as a ZIP. Images to PDF creates one PDF in the order you selected.'
        ],
        'steps': ['Choose PDF → JPG or Images → PDF.', 'Upload the matching files.', 'Convert and download your result.'],
        'faq': [
            {'q': 'Can I convert a PDF to JPG?', 'a': 'Yes. Select PDF → JPG and upload a PDF. Pages are returned in a ZIP file.'},
            {'q': 'Can I convert JPG to PDF?', 'a': 'Yes. Select Images → PDF and upload one or more JPG, PNG or WEBP images.'},
            {'q': 'Can I use both directions on the same page?', 'a': 'Yes. The converter has a single switch for both directions.'},
        ],
    },
}

def current_site_url():
    return os.environ.get('SITE_URL', '').strip().rstrip('/') or request.host_url.rstrip('/')

@app.context_processor
def site_context():
    return {'site_url': current_site_url(), 'site_name': SITE_NAME}

def cleanup(path):
    try:
        p = Path(path)
        if p.is_dir(): shutil.rmtree(p, ignore_errors=True)
        elif p.exists(): p.unlink(missing_ok=True)
    except Exception:
        pass

def schema_for(seo):
    return {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebSite', 'url': current_site_url() + '/', 'name': SITE_NAME, 'description': 'Free online image and PDF conversion tools.'},
        {'@type': 'SoftwareApplication', 'name': seo['h1'], 'url': current_site_url() + seo['path'], 'applicationCategory': 'UtilitiesApplication', 'operatingSystem': 'Web', 'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'}, 'description': seo['description']}
    ]}

@app.get('/')
def index():
    schema = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebSite', 'url': current_site_url() + '/', 'name': SITE_NAME, 'description': 'Free online image and PDF conversion tools.'},
        {'@type': 'Organization', 'name': SITE_NAME, 'url': current_site_url() + '/'}
    ]}
    return render_template('index.html', home_schema=schema)

def render_tool_page(kind):
    seo = SEO_PAGES[kind]
    return render_template('tool_page.html', kind=kind, seo=seo, schema=schema_for(seo))

@app.get('/image-converter')
def image_converter_page(): return render_tool_page('image-converter')

@app.get('/pdf-converter')
def pdf_converter_page(): return render_tool_page('pdf-converter')

# Legacy URLs kept as aliases so old bookmarks and indexed links do not break.
@app.get('/pdf-to-jpg')
def pdf_to_jpg_page(): return redirect('/pdf-converter', 301)

@app.get('/jpg-to-pdf')
def jpg_to_pdf_page(): return redirect('/pdf-converter', 301)

@app.get('/pdf-maker')
def pdf_maker_page(): return redirect('/pdf-converter', 301)

@app.get('/robots.txt')
def robots_txt():
    return Response('User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /health\n\nSitemap: ' + current_site_url() + '/sitemap.xml\n', mimetype='text/plain')

@app.get('/sitemap.xml')
def sitemap_xml():
    body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path in ['/','/image-converter','/pdf-converter']:
        body.append(f'<url><loc>{current_site_url()}{path}</loc></url>')
    body.append('</urlset>')
    return Response('\n'.join(body), mimetype='application/xml')

@app.post('/api/image-convert')
def image_convert():
    files = request.files.getlist('files')
    output = request.form.get('output', 'png').lower().strip()
    try: quality = max(1, min(100, int(request.form.get('quality', '90'))))
    except ValueError: quality = 90
    if output not in {'png', 'jpeg'}: return jsonify(error='Choose PNG or JPEG as the output format.'), 400
    valid = [f for f in files if f and f.filename and Path(f.filename).suffix.lower().lstrip('.') in ALLOWED_IMAGES]
    if not valid: return jsonify(error='Upload one or more JPG, JPEG, PNG or WEBP images.'), 400
    if len(valid) > 30: return jsonify(error='Maximum 30 images per conversion.'), 400
    job = BASE / uuid.uuid4().hex; job.mkdir(); outputs=[]
    try:
        for i, upload in enumerate(valid, 1):
            safe = secure_filename(upload.filename) or f'image-{i}'
            src = job / f'source-{i}{Path(safe).suffix.lower()}'; upload.save(src)
            with Image.open(src) as im:
                stem = Path(safe).stem or f'image-{i}'
                if output == 'jpeg':
                    if im.mode in ('RGBA','LA') or (im.mode == 'P' and 'transparency' in im.info):
                        rgba = im.convert('RGBA'); converted = Image.new('RGB', rgba.size, 'white'); converted.paste(rgba, mask=rgba.getchannel('A')); rgba.close()
                    else: converted = im.convert('RGB')
                    out = job / f'{stem}.jpg'; converted.save(out, 'JPEG', quality=quality, optimize=True); converted.close()
                else:
                    converted = im.convert('RGBA'); out = job / f'{stem}.png'; converted.save(out, 'PNG', optimize=True); converted.close()
                outputs.append(out)
        if len(outputs) == 1:
            response = send_file(outputs[0], as_attachment=True, download_name=outputs[0].name, mimetype='image/png' if output=='png' else 'image/jpeg')
        else:
            zip_path = job / f'converted-{output}.zip'
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
                for p in outputs: z.write(p, p.name)
            response = send_file(zip_path, as_attachment=True, download_name=zip_path.name, mimetype='application/zip')
        response.call_on_close(lambda: cleanup(job)); return response
    except Exception:
        cleanup(job); return jsonify(error='Could not convert the image(s). Please check that the files are valid.'), 500

@app.post('/api/pdf-convert')
def pdf_convert():
    mode = request.form.get('mode', 'pdf-to-jpg').strip().lower()
    job = BASE / uuid.uuid4().hex; job.mkdir()
    try:
        if mode == 'pdf-to-jpg':
            upload = request.files.get('file')
            if not upload or not upload.filename.lower().endswith('.pdf'):
                cleanup(job); return jsonify(error='Choose a PDF file.'), 400
            pdf_path = job / (secure_filename(upload.filename) or 'document.pdf'); upload.save(pdf_path)
            doc = fitz.open(pdf_path)
            if len(doc) > 100:
                doc.close(); cleanup(job); return jsonify(error='PDF limit is 100 pages.'), 400
            out_dir = job / 'pages'; out_dir.mkdir(); jpg_paths=[]
            for i, page in enumerate(doc):
                pix = page.get_pixmap(matrix=fitz.Matrix(1.7,1.7), alpha=False)
                out = out_dir / f'page-{i+1}.jpg'; pix.save(out, jpg_quality=90); jpg_paths.append(out)
            doc.close()
            zip_path = job / 'pdf-to-jpg.zip'
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
                for p in jpg_paths: z.write(p, p.name)
            response = send_file(zip_path, as_attachment=True, download_name=zip_path.name, mimetype='application/zip')
            response.call_on_close(lambda: cleanup(job)); return response

        if mode == 'jpg-to-pdf':
            files = request.files.getlist('files')
            valid = [f for f in files if f and f.filename and Path(f.filename).suffix.lower().lstrip('.') in ALLOWED_IMAGES]
            if not valid: cleanup(job); return jsonify(error='Upload one or more JPG, JPEG, PNG or WEBP images.'), 400
            if len(valid) > 30: cleanup(job); return jsonify(error='Maximum 30 images per PDF.'), 400
            images=[]
            for i, f in enumerate(valid,1):
                path=job / f'image-{i}{Path(f.filename).suffix.lower()}'; f.save(path)
                with Image.open(path) as im: images.append(im.convert('RGB').copy())
            pdf_path=job/'images.pdf'; images[0].save(pdf_path,'PDF',resolution=150.0,save_all=True,append_images=images[1:])
            for im in images: im.close()
            response=send_file(pdf_path,as_attachment=True,download_name='images.pdf',mimetype='application/pdf'); response.call_on_close(lambda: cleanup(job)); return response
        cleanup(job); return jsonify(error='Choose a valid conversion direction.'), 400
    except Exception:
        cleanup(job); return jsonify(error='The conversion could not be completed. Please check your files and try again.'), 500

@app.errorhandler(413)
def too_large(_): return jsonify(error='File is too large. Maximum upload size is 50 MB.'), 413

@app.get('/health')
def health(): return {'status':'ok'}

if __name__ == '__main__': app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)), debug=True)
