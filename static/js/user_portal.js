const API_BASE = "";

const preview = document.getElementById("preview");
const captureButton = document.getElementById("captureButton");
const btnOpenCamera = document.getElementById("btnOpenCamera");
const stopCameraButton = document.getElementById("stopCameraButton");
const sendButton = document.getElementById("sendButton");
const retakeButton = document.getElementById("retakeButton");
const btnCancelCamera = document.getElementById("btnCancelCamera");
const cameraStream = document.getElementById("cameraStream");
const openCameraWrapper = document.getElementById("openCameraWrapper");
const securityDisclaimer = document.getElementById("securityDisclaimer");

let stream = null;

/**
 * State 1: Start Camera
 */
btnOpenCamera.addEventListener("click", async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true });
    cameraStream.srcObject = stream;
    
    // UI Transitions
    cameraStream.style.display = "block";
    preview.style.display = "none";
    openCameraWrapper.classList.add("d-none");
    securityDisclaimer.classList.add("d-none");
    
    captureButton.style.display = "inline-block";
    stopCameraButton.style.display = "inline-block";
    
    sendButton.style.display = "none";
    retakeButton.style.display = "none";
    btnCancelCamera.style.display = "none";
  } catch (error) {
    showAlert("❌ فشل في الوصول إلى الكاميرا. يرجى التأكد من منح الأذونات.", "danger");
  }
});

/**
 * State 2: Capture Photo
 */
captureButton.addEventListener("click", () => {
  const canvas = document.createElement("canvas");
  canvas.width = cameraStream.videoWidth;
  canvas.height = cameraStream.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(cameraStream, 0, 0);

  preview.src = canvas.toDataURL("image/jpeg");
  
  // UI Transitions
  preview.style.display = "block";
  cameraStream.style.display = "none";
  captureButton.style.display = "none";
  stopCameraButton.style.display = "none";
  
  sendButton.style.display = "inline-block";
  retakeButton.style.display = "inline-block";
  btnCancelCamera.style.display = "inline-block";

  // Stop camera stream to save resources
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
  }
});

/**
 * State 3: Retake Photo
 */
retakeButton.addEventListener("click", () => {
  // Reset UI and re-trigger camera
  preview.style.display = "none";
  sendButton.style.display = "none";
  retakeButton.style.display = "none";
  btnCancelCamera.style.display = "none";
  
  btnOpenCamera.click(); 
});

/**
 * State 4: Cancel Camera/Preview
 */
btnCancelCamera.addEventListener("click", () => {
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
  }
  cameraStream.style.display = "none";
  preview.style.display = "none";
  
  sendButton.style.display = "none";
  retakeButton.style.display = "none";
  btnCancelCamera.style.display = "none";
  
  openCameraWrapper.classList.remove("d-none");
  securityDisclaimer.classList.remove("d-none");
  preview.src = "#";
});

/**
 * Helper: Stop Camera manually
 */
stopCameraButton.addEventListener("click", () => {
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
    cameraStream.style.display = "none";
    captureButton.style.display = "none";
    stopCameraButton.style.display = "none";
    openCameraWrapper.classList.remove("d-none");
    securityDisclaimer.classList.remove("d-none");
  }
});

/**
 * Verification Logic (Backend Submission)
 */
sendButton.addEventListener("click", async () => {
  const imageData = preview.src;
  if (!imageData || imageData === "#") {
    showAlert("❌ يرجى التقاط صورة أولاً.", "danger");
    return;
  }

  // 1. Immediate Disable & Loading UI
  sendButton.disabled = true;
  retakeButton.disabled = true;
  const originalBtnContent = sendButton.innerHTML;
  sendButton.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> جاري التحقق...`;

  try {
    const blob = dataURLtoBlob(imageData);

    if (blob.size === 0) {
        throw new Error("❌ فشل في إنشاء بيانات الصورة.");
    }

    const formData = new FormData();
    formData.append("image", blob, "capture.jpg");

    const response = await fetch(`${API_BASE}/users/verify_login`, {
      method: "POST",
      body: formData,
    });
    const data = await response.json();

    if (response.ok) {
      showAlert(`✅ تم تسجيل الدخول بنجاح. أهلاً بك، <strong>${data.user.name}</strong>`, "success");
    } else {
      const errorMessage = data.error || "تم رفض الوصول. يرجى المحاولة مرة أخرى.";
      if (errorMessage.includes("حظر") || errorMessage.includes("تجاوز عدد المحاولات")) {
          // Special "Attractive & Modern" Alert for Bans
          Swal.fire({
            icon: 'warning',
            title: 'تنبيه أمني',
            html: `<div class="text-center p-2">${errorMessage}</div>`,
            confirmButtonText: 'حسناً',
            confirmButtonColor: '#ffc107',
            background: '#fff9e6',
            showClass: {
              popup: 'animate__animated animate__shakeX'
            }
          });
      } else {
          showAlert(`❌ ${errorMessage}`, "danger");
      }
    }
  } catch (error) {
    showAlert("❌ خطأ في الشبكة. يرجى المحاولة مرة أخرى.", "danger");
  } finally {
    // 2. Safe Restoration
    sendButton.disabled = false;
    retakeButton.disabled = false;
    sendButton.innerHTML = originalBtnContent;
  }
});

/**
 * Utility: Convert DataURL to Blob
 */
function dataURLtoBlob(dataurl) {
    const byteString = atob(dataurl.split(',')[1]);
    const mimeString = dataurl.split(',')[0].split(':')[1].split(';')[0];
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], {type: mimeString});
}

// SweetAlert2 Toast Mixin
const Toast = Swal.mixin({
  toast: true,
  position: 'bottom-end',
  showConfirmButton: false,
  timer: 3000,
  timerProgressBar: true,
  didOpen: (toast) => {
    toast.addEventListener('mouseenter', Swal.stopTimer)
    toast.addEventListener('mouseleave', Swal.resumeTimer)
  }
});

function showAlert(message, type) {
  let iconType = type === 'danger' ? 'error' : (type === 'success' ? 'success' : 'info');
  Toast.fire({
    icon: iconType,
    html: message
  });
}
