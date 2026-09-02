async function downloadResponse(res, fallbackName){
  const type=res.headers.get("content-type")||"";
  if(!res.ok){
    let message="Download failed.";
    try{const data=type.includes("json")?await res.json():null;message=data?.error||message;}catch(_e){}
    throw new Error(message);
  }
  const blob=await res.blob();
  const cd=res.headers.get("content-disposition")||"";
  const match=cd.match(/filename\*?=(?:UTF-8''|\")?([^;\"]+)/i);
  const name=match?decodeURIComponent(match[1].replace(/\"/g,"").trim()):fallbackName;
  const href=URL.createObjectURL(blob);
  const a=document.createElement("a");
  a.href=href;a.download=name;document.body.appendChild(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(href),1500);
}

function showDownloadAd(){
  const box=document.getElementById("downloadAd");
  if(!box || box.dataset.loaded === "1") return;
  box.hidden=false;
  box.dataset.loaded="1";
  try{
    (window.adsbygoogle=window.adsbygoogle||[]).push({});
  }catch(err){
    console.warn("AdSense:",err);
  }
}

async function submitForm(form, endpoint, statusId){
  const status=document.getElementById(statusId);
  const button=form.querySelector("button");
  status.textContent="Working…";
  button.disabled=true;
  try{
    const res=await fetch(endpoint,{method:"POST",body:new FormData(form)});
    await downloadResponse(res,"download");
    status.textContent="Done — your download has started.";
    showDownloadAd();
  }catch(e){status.textContent=e.message}
  finally{button.disabled=false}
}

function bindDrop(id,nameId){
 const zone=document.getElementById(id); if(!zone) return;
 const input=zone.querySelector("input"), name=document.getElementById(nameId);
 input.addEventListener("change",()=>{name.textContent=[...input.files].map(x=>x.name).join(", ")});
 zone.addEventListener("dragover",e=>{e.preventDefault();zone.classList.add("drag")});
 zone.addEventListener("dragleave",e=>{e.preventDefault();zone.classList.remove("drag")});
 zone.addEventListener("drop",e=>{e.preventDefault();zone.classList.remove("drag");input.files=e.dataTransfer.files;name.textContent=[...input.files].map(x=>x.name).join(", ")});
}

bindDrop("pdfDrop","pdfName");
bindDrop("jpgDrop","jpgName");

const pdfForm=document.getElementById("pdfForm");
if(pdfForm) pdfForm.addEventListener("submit",e=>{e.preventDefault();submitForm(e.target,"/api/pdf-to-jpg","pdfStatus")});
const jpgForm=document.getElementById("jpgForm");
if(jpgForm) jpgForm.addEventListener("submit",e=>{e.preventDefault();submitForm(e.target,"/api/jpg-to-pdf","jpgStatus")});

const ytForm=document.getElementById("ytForm");
if(ytForm){
  ytForm.addEventListener("submit", async e=>{
    e.preventDefault();
    const form=e.target;
    const status=document.getElementById("ytStatus");
    const meta=document.getElementById("ytMeta");
    const button=form.querySelector("button[type=submit]");
    const mode=form.querySelector("select[name=mode]")?.value || form.querySelector("input[name=mode]")?.value || "video";
    status.textContent="Checking video…";
    meta.textContent="";
    button.disabled=true;
    try{
      const infoRes=await fetch("/api/youtube/info",{method:"POST",body:new FormData(form)});
      const info=await infoRes.json();
      if(!infoRes.ok) throw new Error(info.error||"Could not inspect this video.");
      meta.textContent=info.title+(info.duration?` • ${Math.floor(info.duration/60)} min`:"");
      const endpoint=mode==="mp3"?"/api/youtube/mp3":"/api/youtube";
      status.textContent=mode==="mp3"?"Extracting MP3… keep this tab open.":"Preparing MP4… keep this tab open.";
      const res=await fetch(endpoint,{method:"POST",body:new FormData(form)});
      await downloadResponse(res,mode==="mp3"?"youtube-audio.mp3":"youtube-video.mp4");
      status.textContent="Done — your download has started.";
      showDownloadAd();
    }catch(err){status.textContent=err.message}
    finally{button.disabled=false}
  });
}

// ConvertNest Sky interactions
document.addEventListener("DOMContentLoaded", () => {
  const mode = document.getElementById("ytMode");
  const label = document.getElementById("ytButtonLabel");
  const quality = document.getElementById("qualityWrap");
  if (mode) {
    const sync = () => {
      const mp3 = mode.value === "mp3";
      if (label) label.textContent = mp3 ? "MP3" : "MP4";
      if (quality) quality.style.display = mp3 ? "none" : "flex";
    };
    mode.addEventListener("change", sync); sync();
  }
  const card = document.querySelector(".youtube-hero-card");
  if (card && window.matchMedia("(pointer:fine)").matches) {
    card.addEventListener("pointermove", e => {
      const r=card.getBoundingClientRect(), x=(e.clientX-r.left)/r.width-.5, y=(e.clientY-r.top)/r.height-.5;
      card.style.transform=`perspective(900px) rotateY(${x*2.2}deg) rotateX(${-y*1.8}deg) translateY(-5px)`;
    });
    card.addEventListener("pointerleave",()=>card.style.transform="");
  }
});
