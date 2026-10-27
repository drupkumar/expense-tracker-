const fileInput = document.getElementById("fileInput");
const pickBtn = document.getElementById("pickBtn");
const camBtn = document.getElementById("camBtn");
const snapBtn = document.getElementById("snapBtn");
const preview = document.getElementById("preview");
const camera = document.getElementById("camera");
const emptyState = document.getElementById("emptyState");
const ocrStatus = document.getElementById("ocrStatus");
const ocrProgress = document.getElementById("ocrProgress");
const ocrBar = document.getElementById("ocrBar");
const saveBtn = document.getElementById("saveBtn");
const dropzone = document.getElementById("dropzone");

let stream = null;

pickBtn?.addEventListener("click", () => fileInput.click());
fileInput?.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (file) handleFile(file);
});

["dragenter", "dragover"].forEach((evt) => {
  dropzone?.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.style.borderColor = "#3ee0b0";
  });
});
dropzone?.addEventListener("drop", (e) => {
  e.preventDefault();
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});

camBtn?.addEventListener("click", async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
    camera.srcObject = stream;
    camera.classList.add("show");
    preview.classList.remove("show");
    emptyState.style.display = "none";
    snapBtn.hidden = false;
    ocrStatus.textContent = "Camera ready — hold the bill steady and capture.";
  } catch {
    ocrStatus.textContent = "Camera permission was denied. Upload a photo instead.";
  }
});

snapBtn?.addEventListener("click", () => {
  const canvas = document.createElement("canvas");
  canvas.width = camera.videoWidth || 1080;
  canvas.height = camera.videoHeight || 1440;
  canvas.getContext("2d").drawImage(camera, 0, 0);
  canvas.toBlob((blob) => {
    const file = new File([blob], "capture.jpg", { type: "image/jpeg" });
    handleFile(file);
  }, "image/jpeg", 0.92);
  stream?.getTracks().forEach((t) => t.stop());
  camera.classList.remove("show");
});

async function handleFile(file) {
  emptyState.style.display = "none";
  preview.src = URL.createObjectURL(file);
  preview.classList.add("show");
  camera.classList.remove("show");
  saveBtn.disabled = true;
  ocrProgress.hidden = false;
  ocrStatus.textContent = "Reading the bill…";
  await uploadReceipt(file);
  try {
    const result = await Tesseract.recognize(file, "eng", {
      logger: (m) => {
        if (m.status === "recognizing text" && m.progress) {
          ocrBar.style.width = `${Math.round(m.progress * 100)}%`;
          ocrStatus.textContent = `Reading text… ${Math.round(m.progress * 100)}%`;
        }
      },
    });
    const text = result.data.text || "";
    document.getElementById("rawText").textContent = text || "No text found. Try a clearer photo.";
    await fillFromServer(text);
  } catch (err) {
    ocrStatus.textContent = "Could not read this image. Enter the details manually.";
    saveBtn.disabled = false;
  }
}

async function uploadReceipt(file) {
  const body = new FormData();
  body.append("receipt", file);
  try {
    const res = await fetch("/scan/upload", { method: "POST", body });
    const data = await res.json();
    if (data.path) document.getElementById("receiptPath").value = data.path;
  } catch {
    /* preview still works even if upload fails */
  }
}

async function fillFromServer(text) {
  const res = await fetch("/scan/parse", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  const data = await res.json();
  document.getElementById("fAmount").value = data.amount || "";
  document.getElementById("fMerchant").value = data.merchant || "";
  document.getElementById("fDate").value = data.date || "";
  document.getElementById("fNote").value = data.note || "";
  document.getElementById("fPay").value = data.payment_method || "UPI";
  if (data.category_id) document.getElementById("fCategory").value = data.category_id;
  document.getElementById("confidenceChip").textContent = data.amount ? "Fields filled" : "Check manually";
  ocrStatus.textContent = data.amount
    ? `Found ₹${data.amount} at ${data.merchant}. Confirm and save.`
    : "Text captured, but amount was unclear. Fill the amount and save.";
  saveBtn.disabled = false;
}
