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
    showAlert("✅ تم اختيار الصورة بنجاح.", "success");
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
    showAlert("❌ تم رفض الوصول للكاميرا أو أنها غير متاحة.", "danger");
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
    showAlert("✅ تم التقاط الصورة بنجاح.", "success");
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
  showAlert("✔️ تم إيقاف الكاميرا.", "secondary");
});

// 📤 Send to /users/verify_login
sendButton.addEventListener("click", async () => {
  if (!selectedFile) {
    showAlert("❌ يرجى تحديد أو التقاط صورة أولاً.", "danger");
    return;
  }

  const formData = new FormData();
  formData.append("image", selectedFile);

  showAlert("⏳ جاري التحقق، يرجى الانتظار...", "info");

  try {
    const response = await fetch("/users/verify_login", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();

    if (response.ok) {
      showAlert(
        `✅ تم تسجيل الدخول بنجاح. أهلاً بك، <strong>${data.user.name}</strong>`,
        "success"
      );
    } else {
      showAlert(
        `❌ ${data.error || "تم رفض الوصول. يرجى المحاولة مرة أخرى."}`,
        "danger"
      );
    }
  } catch (error) {
    showAlert("❌ خطأ في الشبكة. يرجى المحاولة مرة أخرى.", "danger");
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

// Custom File Upload Label Logic
document.addEventListener('DOMContentLoaded', () => {
  const imageUploadInput = document.getElementById("imageUpload");
  const userFileLabel = document.getElementById("userFileLabel");
  
  if (imageUploadInput && userFileLabel) {
    imageUploadInput.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        userFileLabel.innerText = '📁 ' + e.target.files[0].name;
      } else {
        userFileLabel.innerText = "📁 اختر صورة من الجهاز...";
      }
    });
  }
});
