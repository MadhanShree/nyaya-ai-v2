let documentId = null;

const $ = (id) => document.getElementById(id);

function setStatus(message, error = false) {
  const status = $("uploadStatus");
  status.textContent = message;
  status.classList.toggle("error", error);
}

function setBusy(button, busy, label) {
  button.disabled = busy;
  button.setAttribute("aria-busy", String(busy));
  button.textContent = busy ? label : button.dataset.defaultLabel;
}

async function readJson(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "The request failed. Please try again.");
  }
  return data;
}

function showAnalysis() {
  $("analysis").classList.remove("hidden");
  $("questions").classList.remove("hidden");
}

async function upload() {
  const file = $("file").files[0];
  if (!file) {
    setStatus("Please choose a document first.", true);
    return;
  }

  const allowedTypes = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "",
  ];
  const allowedExtension = /\.(pdf|docx|txt)$/i.test(file.name);
  if (!allowedTypes.includes(file.type) && !allowedExtension) {
    setStatus("Please choose a PDF, DOCX, or TXT file.", true);
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    setStatus("The file is larger than the 5 MB limit.", true);
    return;
  }

  const form = new FormData();
  form.append("file", file);
  form.append("language", $("language").value);

  setStatus("Uploading and extracting text...");
  const button = $("uploadBtn");
  setBusy(button, true, "Uploading...");

  try {
    const data = await readJson(await fetch("/api/upload", {
      method: "POST",
      body: form,
    }));
    documentId = data.document_id;
    setStatus(`Uploaded ${data.filename} — ${data.clause_count} clauses found.`);
    showAnalysis();
    $("summary").textContent = "Analyzing document...";
    $("risks").replaceChildren(Object.assign(document.createElement("p"), {
      className: "muted",
      textContent: "Analyzing...",
    }));
    await analyze();
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    setBusy(button, false, "Uploading...");
  }
}

async function analyze() {
  try {
    const data = await readJson(await fetch(
      `/api/analyze/${encodeURIComponent(documentId)}`,
      { method: "POST" },
    ));
    $("summary").textContent = data.summary || "No summary was returned.";
    const risks = Array.isArray(data.risks) ? data.risks : [];
    $("risks").replaceChildren();

    if (!risks.length) {
      $("risks").appendChild(Object.assign(document.createElement("p"), {
        className: "muted",
        textContent: "No specific risk items were returned. Read the document carefully.",
      }));
      return;
    }

    for (const risk of risks) {
      const box = document.createElement("div");
      box.className = "risk";
      const title = document.createElement("strong");
      title.textContent = risk.text || "Review this clause";
      const citation = document.createElement("div");
      citation.className = "citation";
      citation.textContent = risk.citation || "";
      box.append(title, citation);
      $("risks").appendChild(box);
    }
  } catch (error) {
    $("summary").textContent = error.message;
    $("risks").replaceChildren();
  }
}

$("file").addEventListener("change", () => {
  const file = $("file").files[0];
  $("selected-file").textContent = file
    ? `${file.name} — ${(file.size / 1024 / 1024).toFixed(2)} MB`
    : "No file selected.";
});

$("uploadBtn").dataset.defaultLabel = "Upload document";
$("uploadBtn").addEventListener("click", upload);

$("question").addEventListener("input", () => {
  $("question-count").textContent = `${$("question").value.length} / 2000`;
});

$("askBtn").dataset.defaultLabel = "Ask NyayaAI";
$("askForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = $("question").value.trim();
  if (!documentId || !question) return;

  const button = $("askBtn");
  setBusy(button, true, "Thinking...");
  $("answer").textContent = "Thinking...";

  try {
    const data = await readJson(await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        document_id: documentId,
        question,
        language: $("language").value,
      }),
    }));

    $("answer").replaceChildren();
    const answer = document.createElement("div");
    answer.textContent = data.answer || "No answer returned.";
    $("answer").appendChild(answer);

    for (const citation of (data.citations || [])) {
      const item = document.createElement("div");
      item.className = "citation";
      item.textContent = citation;
      $("answer").appendChild(item);
    }
  } catch (error) {
    $("answer").textContent = error.message;
  } finally {
    setBusy(button, false, "Thinking...");
  }
});
