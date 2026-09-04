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
        'title': 'JPG to PNG Converter & PNG to JPG Online — Free | ConvertNest',
        'description': 'Convert JPG to PNG or PNG to JPG online for free. Convert JPEG and WEBP images too, with quality controls and batch conversion.',
        'h1': 'JPG to PNG & PNG to JPG Converter',
        'intro': 'Convert JPG to PNG or PNG to JPG online for free. Upload one or multiple JPG, JPEG, PNG or WEBP images and choose your output format.',
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
        'title': 'PDF to JPG Converter & JPG to PDF Online — Free | ConvertNest',
        'description': 'Convert PDF to JPG online for free, or turn JPG, PNG and WEBP images into a PDF. Simple browser-based PDF conversion.',
        'h1': 'PDF to JPG & JPG to PDF Converter',
        'intro': 'Convert PDF pages to JPG, or combine JPG, PNG and WEBP images into a PDF. Use both conversion directions in one simple tool.',
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
    base = current_site_url()
    faq_entities = [
        {'@type': 'Question', 'name': item['q'], 'acceptedAnswer': {'@type': 'Answer', 'text': item['a']}}
        for item in seo.get('faq', [])
    ]
    return {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebSite', 'url': base + '/', 'name': SITE_NAME, 'description': 'Free online JPG, PNG, WEBP and PDF conversion tools.'},
        {'@type': 'WebPage', 'url': base + seo['path'], 'name': seo['title'], 'description': seo['description']},
        {'@type': 'SoftwareApplication', 'name': seo['h1'], 'url': base + seo['path'], 'applicationCategory': 'UtilitiesApplication', 'operatingSystem': 'Web', 'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'}, 'description': seo['description']},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'ConvertNest', 'item': base + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': seo['h1'], 'item': base + seo['path']}
        ]},
        {'@type': 'FAQPage', 'mainEntity': faq_entities}
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
    pages = ['/', '/image-converter', '/pdf-converter', '/faq', '/about', '/contact', '/privacy', '/terms']
    body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path in pages:
        body.append(f'<url><loc>{current_site_url()}{path}</loc></url>')
    body.append('</urlset>')
    return Response('\n'.join(body), mimetype='application/xml')


@app.get('/about')
def about_page():
    return render_template('info_page.html', page_title='About ConvertNest', meta_description='Learn about ConvertNest, a simple collection of free online image and PDF conversion tools.', heading='About ConvertNest', sections=[
        ('Simple online file conversion', 'ConvertNest provides straightforward browser-based tools for common image and PDF conversions. The goal is to make routine file conversion quick and easy without requiring desktop software.'),
        ('Supported conversions', 'Convert JPG to PNG, PNG to JPG, JPG and other supported images to PDF, and PDF pages to JPG. Batch image conversion is supported within the published limits.'),
        ('Privacy-minded design', 'Files are processed for the conversion request and temporary conversion data is cleaned up after the response where applicable. Do not upload confidential files unless you are comfortable using an online conversion service.')
    ])

@app.get('/faq')
def faq_page():
    return render_template('info_page.html', page_title='ConvertNest FAQ', meta_description='Answers to common questions about JPG, PNG, PDF and image conversion on ConvertNest.', heading='Frequently Asked Questions', sections=[
        ('Is ConvertNest free?', 'Yes. The conversion tools currently available on ConvertNest are free to use and do not require an account.'),
        ('Can I convert JPG to PNG?', 'Yes. Open the Image Converter and choose PNG as the output format.'),
        ('Can I convert PNG to JPG?', 'Yes. Choose JPEG as the output format. Transparent areas are placed on a white background because JPEG does not support transparency.'),
        ('Can I convert PDF to JPG?', 'Yes. Open the PDF Converter, choose PDF to JPG, and upload your PDF.'),
        ('Can I convert JPG to PDF?', 'Yes. Choose Images to PDF and upload one or more JPG, PNG or WEBP images.'),
        ('Is there a file limit?', 'The application enforces upload, image-count and PDF-page limits to keep the service reliable.')
    ])

@app.get('/contact')
def contact_page():
    return render_template('info_page.html', page_title='Contact ConvertNest', meta_description='Contact ConvertNest for questions, feedback, bug reports and website issues.', heading='Contact ConvertNest', sections=[
        ('Questions and feedback', 'If a converter is not working as expected, report the conversion type, file type, browser and a short description of the problem.'),
        ('Important', 'Do not send passwords, payment-card information, private keys or other sensitive information in a support message.')
    ])

@app.get('/privacy')
def privacy_page():
    return render_template('info_page.html', page_title='Privacy Policy — ConvertNest', meta_description='Read the ConvertNest privacy information for online image and PDF conversion tools.', heading='Privacy Policy', sections=[
        ('File processing', 'Files uploaded for conversion are handled temporarily for the requested conversion. Temporary conversion data is cleaned up after the response where applicable.'),
        ('Cookies and advertising', 'ConvertNest may use third-party advertising technology. Advertising providers may use cookies or similar technologies subject to their own policies and applicable consent requirements.'),
        ('Your responsibility', 'Do not upload confidential or sensitive files unless you understand and accept the risks of using an online conversion service.')
    ])

@app.get('/terms')
def terms_page():
    return render_template('info_page.html', page_title='Terms of Use — ConvertNest', meta_description='Read the ConvertNest terms of use for the online conversion tools.', heading='Terms of Use', sections=[
        ('Use of the service', 'Use ConvertNest only for lawful files and purposes. You are responsible for having the rights and permissions needed to upload and convert files.'),
        ('No guarantee', 'Conversion results can vary by file, format and browser. The service is provided without a guarantee that every file will convert successfully.'),
        ('Limits', 'The application may enforce file, page and batch limits to protect service reliability.')
    ])

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
