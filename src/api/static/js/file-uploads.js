const dropZone = document.querySelector(".file-drop");
const fileInput = document.getElementById("files");
const fileList = document.getElementById("fileList");
const fileCount = document.getElementById("fileCount");
const totalSize = document.getElementById("totalSize");
const analysisNameInput = document.getElementById("analysisName");
const analysisNameDisplay = document.getElementById("analysisNameDisplay");

function updateFileUI(files) {

    let size = 0;
    fileList.innerHTML = "";

    Array.from(files).forEach(file => {
        size += file.size;

        const div = document.createElement("div");
        div.className = "file-item";
        div.textContent = file.name;

        fileList.appendChild(div);
    });

    fileCount.textContent = files.length;
    totalSize.textContent = (size / 1024).toFixed(1) + " KB";
}

function updateAnalysisUI(analysisName) {
    if (analysisName == ""){
        analysisNameDisplay.textContent = "Not Set"
    } else {
        analysisNameDisplay.textContent = analysisName
    }
}

// Handle file input selection
fileInput.addEventListener("change", () => {
    updateFileUI(fileInput.files);
});

// Handle analysis name input
analysisNameInput.addEventListener("change", () => {
    updateAnalysisUI(analysisNameInput.value)
});

// Handle file drag and drop events
dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");

    const files = e.dataTransfer.files;

    fileInput.files = files;
    updateFileUI(files);
});