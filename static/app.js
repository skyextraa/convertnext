async function downloadResponse(res, fallbackName) {
  const type = res.headers.get("content-type") || "";

  if (!res.ok) {
    let message = "Download failed.";
    try {
      if (type.includes("json")) {
        const data = await res.json();
        message = data?.error || message;
      }
    } catch (_) {}
    throw new Error(message);
  }

  const blob = await res.blob();
  const cd = res.headers.get("content-disposition") || "";
  const match = cd.match(/filename\*?=(?:UTF-8''|")?([^;"]+)/i);
  let name = fallbackName;

  if (match) {
    try {
      name = decodeURIComponent(match[1].replace(/"/g, "").trim());
    } catch (_) {
      name = match[1].replace(/"/g, "").trim();
    }
  }

  const href = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = href;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(href), 1500);
}

function showDownloadAd() {
  const box = document.getElementById("downloadAd");
  if (!box || box.dataset.loaded === "1") return;

  box.hidden = false;
  box.dataset.loaded = "1";

  try {
    (window.adsbygoogle = window.adsbygoogle || []).push({});
  } catch (err) {
    console.warn("AdSense:", err);
  }
}

async function submitForm(form, endpoint, statusId) {
  const status = document.getElementById(statusId);
  const button = form.querySelector("button");

  if (!status || !button) return;

  status.textContent = "Working…";
  button.disabled = true;

  try {
    const res = await fetch(endpoint, {
      method: "POST",
      body: new FormData(form)
    });

    await downloadResponse(res, "download");
    status.textContent = "Done — your download has started.";
    showDownloadAd();
  } catch (e) {
    status.textContent = e.message || "Download failed.";
  } finally {
    button.disabled = false;
  }
}

function bindDrop(id, nameId) {
  const zone = document.getElementById(id);
  if (!zone) return;

  const input = zone.querySelector("input");
  const name = document.getElementById(nameId);
  if (!input || !name) return;

  const showNames = files => {
    name.textContent = [...files].map(x => x.name).join(", ");
  };

  input.addEventListener("change", () => showNames(input.files));

  zone.addEventListener("dragover", e => {
    e.preventDefault();
    zone.classList.add("drag");
  });

  zone.addEventListener("dragleave", e => {
    e.preventDefault();
    zone.classList.remove("drag");
  });

  zone.addEventListener("drop", e => {
    e.preventDefault();
    zone.classList.remove("drag");
    try {
      input.files = e.dataTransfer.files;
      showNames(input.files);
    } catch (_) {}
  });
}

bindDrop("pdfDrop", "pdfName");
bindDrop("jpgDrop", "jpgName");

const pdfForm = document.getElementById("pdfForm");
if (pdfForm) {
  pdfForm.addEventListener("submit", e => {
    e.preventDefault();
    submitForm(e.target, "/api/pdf-to-jpg", "pdfStatus");
  });
}

const jpgForm = document.getElementById("jpgForm");
if (jpgForm) {
  jpgForm.addEventListener("submit", e => {
    e.preventDefault();
    submitForm(e.target, "/api/jpg-to-pdf", "jpgStatus");
  });
}

const ytForm = document.getElementById("ytForm");

if (ytForm) {
  ytForm.addEventListener("submit", async e => {
    e.preventDefault();

    const form = e.target;
    const status = document.getElementById("ytStatus");
    const meta = document.getElementById("ytMeta");
    const button = form.querySelector("button[type=submit]");
    const mode =
      form.querySelector("select[name=mode]")?.value ||
      form.querySelector("input[name=mode]")?.value ||
      "video";

    if (!status || !button) return;

    status.textContent =
      mode === "mp3"
        ? "Preparing MP3… keep this tab open."
        : "Preparing MP4… keep this tab open.";

    if (meta) meta.textContent = "";
    button.disabled = true;

    const turnstileToken = form.querySelector('input[name="cf-turnstile-response"]')?.value || "";
    if (!turnstileToken) {
      status.textContent = "Please complete the human verification first.";
      button.disabled = false;
      return;
    }

    try {
      // Download directly instead of making a separate /info request first.
      // This avoids an unnecessary second YouTube extraction request.
      const endpoint = mode === "mp3" ? "/api/youtube/mp3" : "/api/youtube";
      const res = await fetch(endpoint, {
        method: "POST",
        body: new FormData(form)
      });

      await downloadResponse(
        res,
        mode === "mp3" ? "youtube-audio.mp3" : "youtube-video.mp4"
      );

      status.textContent = "Done — your download has started.";
      showDownloadAd();
    } catch (err) {
      status.textContent = err.message || "Download failed.";
      if (window.turnstile) {
        const widget = form.querySelector('.cf-turnstile');
        if (widget && widget.dataset.widgetId) {
          try { window.turnstile.reset(widget.dataset.widgetId); } catch (_) {}
        }
      }
    } finally {
      button.disabled = false;
    }
  });
}

function updateYTMode() {
  const mode = document.getElementById("ytMode");
  const label = document.getElementById("ytButtonLabel");
  const quality = document.getElementById("qualityWrap");
  const submit = document.querySelector("#ytForm button[type=submit]");

  if (!mode) return;

  const mp3 = mode.value === "mp3";

  if (label) label.textContent = mp3 ? "MP3" : "MP4";
  if (quality) quality.style.display = mp3 ? "none" : "flex";
  if (submit) submit.innerHTML = `Download <span id="ytButtonLabel">${mp3 ? "MP3" : "MP4"}</span> →`;
}

document.addEventListener("DOMContentLoaded", () => {
  const mode = document.getElementById("ytMode");

  if (mode) {
    mode.addEventListener("change", updateYTMode);
    updateYTMode();
  }

  const card = document.querySelector(".youtube-hero-card");

  if (card && window.matchMedia("(pointer:fine)").matches) {
    card.addEventListener("pointermove", e => {
      const r = card.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5;
      const y = (e.clientY - r.top) / r.height - 0.5;
      card.style.transform =
        `perspective(900px) rotateY(${x * 2.2}deg) ` +
        `rotateX(${-y * 1.8}deg) translateY(-5px)`;
    });

    card.addEventListener("pointerleave", () => {
      card.style.transform = "";
    });
  }
});
