const imageInput = document.getElementById("imageUpload");
const preview = document.getElementById("preview");
const resultDiv = document.getElementById("result");
const sendButton = document.getElementById("sendButton");

const openCameraButton = document.getElementById("openCamera");
const cameraStream = document.getElementById("cameraStream");
const captureButton = document.getElementById("captureButton");
const stopCameraButton = document.getElementById("stopCameraButton");

let selectedFile = null;
let stream = null;

// 📁 Upload from file
imageInput.addEventListener("change", (e) => {
  selectedFile = e.target.files[0];
  if (selectedFile) {
    preview.src = URL.createObjectURL(selectedFile);
    preview.style.display = "block";
    showAlert("✅ Image selected successfully.", "success");
  }
});

// 📷 Open Camera
openCameraButton.addEventListener("click", async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true });
    cameraStream.srcObject = stream;
    cameraStream.style.display = "block";
    captureButton.style.display = "inline-block";
    stopCameraButton.style.display = "inline-block";
    clearAlert();
  } catch (err) {
    showAlert("❌ Camera access denied or unavailable.", "danger");
  }
});

// 📸 Capture Frame
captureButton.addEventListener("click", () => {
  const canvas = document.createElement("canvas");
  canvas.width = cameraStream.videoWidth;
  canvas.height = cameraStream.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(cameraStream, 0, 0);
  canvas.toBlob((blob) => {
    selectedFile = new File([blob], "captured.png", { type: "image/png" });
    preview.src = URL.createObjectURL(selectedFile);
    preview.style.display = "block";
    showAlert("✅ Image captured successfully.", "success");
  });
});

// ✖️ Stop Camera
stopCameraButton.addEventListener("click", () => {
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
  }
  cameraStream.style.display = "none";
  captureButton.style.display = "none";
  stopCameraButton.style.display = "none";
  showAlert("✔️ Camera stopped.", "secondary");
});

// 📤 Send to /users/verify_login
sendButton.addEventListener("click", async () => {
  if (!selectedFile) {
    showAlert("❌ Please select or capture an image first.", "danger");
    return;
  }

  const formData = new FormData();
  formData.append("image", selectedFile);

  showAlert("⏳ Verifying, please wait...", "info");

  try {
    const response = await fetch("/users/verify_login", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();

    if (response.ok) {
      showAlert(
        `✅ Login successful. Welcome,  <strong>${data.user.name}</strong>`,
        "success"
      );
    } else {
      showAlert(
        `❌ ${data.error || "Access Denied. Please try again."}`,
        "danger"
      );
    }
  } catch (error) {
    showAlert("❌ Network error. Please try again.", "danger");
  }
});

// Alert Utility
function showAlert(message, type) {
  resultDiv.innerHTML = `
    <div class="alert alert-${type}" role="alert">
      ${message}
    </div>`;
}
function clearAlert() {
  resultDiv.innerHTML = "";
}
