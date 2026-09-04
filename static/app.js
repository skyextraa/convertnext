async function downloadResponse(res, fallbackName) {
  const type = res.headers.get('content-type') || '';
  if (!res.ok) {
    let message = 'Conversion failed.';
    try { if (type.includes('json')) message = (await res.json()).error || message; } catch (_) {}
    throw new Error(message);
  }
  const blob = await res.blob();
  const cd = res.headers.get('content-disposition') || '';
  const match = cd.match(/filename\*?=(?:UTF-8''|")?([^;"]+)/i);
  let name = fallbackName;
  if (match) { try { name = decodeURIComponent(match[1].replace(/"/g, '').trim()); } catch (_) { name = match[1].replace(/"/g, '').trim(); } }
  const href = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = href; a.download = name; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(href), 1500);
}

async function submitForm(form, endpoint, statusId, fallback) {
  const status = document.getElementById(statusId); const button = form.querySelector('button[type=submit]');
  if (!status || !button) return;
  status.textContent = 'Converting…'; button.disabled = true;
  try { await downloadResponse(await fetch(endpoint, {method:'POST', body:new FormData(form)}), fallback); status.textContent = 'Done — your download has started.'; }
  catch (e) { status.textContent = e.message || 'Conversion failed.'; }
  finally { button.disabled = false; }
}

function bindDrop(zoneId, inputId, nameId) {
  const zone = document.getElementById(zoneId), input = document.getElementById(inputId), name = document.getElementById(nameId);
  if (!zone || !input || !name) return;
  const show = files => { const n = [...files].length; name.textContent = n ? `${n} file${n === 1 ? '' : 's'} selected` : ''; };
  input.addEventListener('change', () => show(input.files));
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag'));
  zone.addEventListener('drop', e => { e.preventDefault(); zone.classList.remove('drag'); try { input.files = e.dataTransfer.files; show(input.files); } catch (_) {} });
}

bindDrop('imageDrop','imageInput','imageName');
bindDrop('pdfInputZone','pdfInput','pdfFileName');
bindDrop('imagesInputZone','imagesInput','pdfFileName');

const imageForm = document.getElementById('imageForm');
if (imageForm) {
  const output = document.getElementById('imageOutput'), qualityRow = document.getElementById('qualityRow'), quality = document.getElementById('quality'), qualityValue = document.getElementById('qualityValue'), submit = imageForm.querySelector('button[type=submit]');
  document.querySelectorAll('.format-option[data-output]').forEach(btn => btn.addEventListener('click', () => {
    document.querySelectorAll('.format-option[data-output]').forEach(x => x.classList.remove('active')); btn.classList.add('active'); output.value = btn.dataset.output;
    const jpeg = output.value === 'jpeg'; qualityRow.hidden = !jpeg; submit.textContent = `Convert to ${jpeg ? 'JPEG' : 'PNG'}`;
  }));
  quality.addEventListener('input', () => qualityValue.value = quality.value);
  imageForm.addEventListener('submit', e => { e.preventDefault(); submitForm(e.target,'/api/image-convert','imageStatus','converted.png'); });
}

const pdfForm = document.getElementById('pdfConvertForm');
if (pdfForm) {
  const mode = document.getElementById('pdfMode'), pdfZone = document.getElementById('pdfInputZone'), imgZone = document.getElementById('imagesInputZone'), pdfInput = document.getElementById('pdfInput'), imagesInput = document.getElementById('imagesInput'), submit = document.getElementById('pdfSubmit'), name = document.getElementById('pdfFileName');
  const sync = m => { mode.value = m; const imageMode = m === 'jpg-to-pdf'; pdfZone.hidden = imageMode; imgZone.hidden = !imageMode; pdfInput.disabled = imageMode; imagesInput.disabled = !imageMode; submit.textContent = imageMode ? 'Convert Images to PDF' : 'Convert PDF to JPG'; name.textContent = ''; };
  document.querySelectorAll('.direction-switch .format-option').forEach(btn => btn.addEventListener('click', () => { document.querySelectorAll('.direction-switch .format-option').forEach(x => x.classList.remove('active')); btn.classList.add('active'); sync(btn.dataset.mode); }));
  pdfForm.addEventListener('submit', e => { e.preventDefault(); submitForm(e.target,'/api/pdf-convert','pdfConvertStatus',mode.value === 'jpg-to-pdf' ? 'images.pdf' : 'pdf-to-jpg.zip'); });
}

// Gentle mouse interaction for desktop only.
document.querySelectorAll('.interactive-card').forEach(card => {
  if (!window.matchMedia('(pointer:fine)').matches) return;
  card.addEventListener('pointermove', e => { const r=card.getBoundingClientRect(), x=(e.clientX-r.left)/r.width-.5, y=(e.clientY-r.top)/r.height-.5; card.style.transform=`perspective(1000px) rotateY(${x*2}deg) rotateX(${-y*1.5}deg) translateY(-3px)`; });
  card.addEventListener('pointerleave', () => card.style.transform='');
});

function bindSimpleImageTool(prefix, endpoint, statusId, fallback) {
  const form = document.getElementById(prefix + 'Form');
  if (!form) return;
  const input = document.getElementById(prefix + 'Input');
  const name = document.getElementById(prefix + 'Name');
  const zone = document.getElementById(prefix + 'Drop');
  if (input && name && zone) bindDrop(prefix + 'Drop', prefix + 'Input', prefix + 'Name');
  form.addEventListener('submit', e => { e.preventDefault(); submitForm(e.target, endpoint, statusId, fallback); });
}

bindSimpleImageTool('resize', '/api/image-resize', 'resizeStatus', 'resized-image.jpg');
bindSimpleImageTool('enhance', '/api/image-enhance', 'enhanceStatus', 'enhanced-image.png');

const resizeQuality = document.getElementById('resizeQuality');
const resizeQualityValue = document.getElementById('resizeQualityValue');
if (resizeQuality && resizeQualityValue) resizeQuality.addEventListener('input', () => resizeQualityValue.value = resizeQuality.value);
const enhanceQuality = document.getElementById('enhanceQuality');
const enhanceQualityValue = document.getElementById('enhanceQualityValue');
if (enhanceQuality && enhanceQualityValue) enhanceQuality.addEventListener('input', () => enhanceQualityValue.value = enhanceQuality.value);
