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
    stream = await navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 640 }, height: { ideal: 480 } } });
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
    showAlert("فشل في الوصول إلى الكاميرا. يرجى التأكد من منح الأذونات.", "danger");
  }
});

/**
 * State 2: Capture Photo
 */
captureButton.addEventListener("click", async () => {
  const canvas1 = document.createElement("canvas");
  canvas1.width = cameraStream.videoWidth;
  canvas1.height = cameraStream.videoHeight;
  const ctx1 = canvas1.getContext("2d");
  ctx1.drawImage(cameraStream, 0, 0);

  const challenges = [
    { code: "smile", text: "ابتسم بوضوح" },
    { code: "turn_right", text: "أدر رأسك يمينًا قليلاً" },
    { code: "raise_eyebrows", text: "ارفع حاجبيك" }
  ];
  const randomChallenge = challenges[Math.floor(Math.random() * challenges.length)];
  
  // Store the challenge code to send it later
  preview.dataset.challenge = randomChallenge.code;

  // Active Challenge UI Hint
  Swal.fire({
    title: randomChallenge.text,
    text: 'جاري التقاط الإطار الثاني للتأكد من الحيوية...',
    icon: 'info',
    timer: 1500,
    showConfirmButton: false,
    allowOutsideClick: false
  });
  
  // Wait ~1.5 seconds for the user to make a micro-movement
  await new Promise(r => setTimeout(r, 1500));
  
  const canvas2 = document.createElement("canvas");
  canvas2.width = cameraStream.videoWidth;
  canvas2.height = cameraStream.videoHeight;
  const ctx2 = canvas2.getContext("2d");
  ctx2.drawImage(cameraStream, 0, 0);

  preview.src = canvas1.toDataURL("image/jpeg", 0.85);
  preview.dataset.frame2 = canvas2.toDataURL("image/jpeg", 0.85);
  
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
    showAlert("يرجى التقاط صورة أولاً.", "danger");
    return;
  }

  // 1. Immediate Disable & Loading UI
  sendButton.disabled = true;
  retakeButton.disabled = true;
  const originalBtnContent = sendButton.innerHTML;
  sendButton.innerHTML = `<span class="fc-spinner" role="status" aria-hidden="true"></span> جاري التحقق...`;

  try {
    const blob = dataURLtoBlob(imageData);

    if (blob.size === 0) {
        throw new Error("❌ فشل في إنشاء بيانات الصورة.");
    }

    const formData = new FormData();
    formData.append("image", blob, "capture.jpg");
    
    // Add second frame if available for Liveness challenge
    if (preview.dataset.frame2) {
      const blob2 = dataURLtoBlob(preview.dataset.frame2);
      formData.append("image2", blob2, "capture2.jpg");
      if (preview.dataset.challenge) {
        formData.append("challenge", preview.dataset.challenge);
      }
    }

    const response = await fetch(`${API_BASE}/users/verify_login`, {
      method: "POST",
      body: formData,
    });
    const data = await response.json();

    if (response.ok) {
      Swal.fire({
        icon: 'success',
        title: 'نجاح',
        html: `تم تسجيل الدخول بنجاح. أهلاً بك، <strong>${escapeHTML(data.user.name)}</strong><br><br>` +
              `<button id="registerPasskeyBtn" class="btn-cta-primary" style="font-size: 0.9em; padding: 10px 20px; width: auto; display: inline-flex; justify-content: center; margin-top: 10px;">🔑 تسجيل مفتاح مرور لهذا الجهاز</button>`,
        showConfirmButton: true,
        confirmButtonText: 'إغلاق',
        customClass: { popup: 'swal-dark-popup' },
        didRender: () => {
          const btn = document.getElementById('registerPasskeyBtn');
          if (btn) {
            btn.addEventListener('click', async () => {
              btn.disabled = true;
              btn.innerHTML = `<span class="fc-spinner" role="status" aria-hidden="true" style="margin-left: 8px;"></span> جاري الإعداد...`;
              try {
                // 1. Begin registration
                const beginResp = await fetch(`${API_BASE}/users/webauthn/register/begin`, { method: 'POST' });
                if (!beginResp.ok) throw new Error("Failed to start WebAuthn");
                const options = await beginResp.json();
                
                // Convert base64url to Uint8Array
                options.challenge = base64urlToUint8Array(options.challenge);
                options.user.id = base64urlToUint8Array(options.user.id);
                if (options.excludeCredentials) {
                  for (let cred of options.excludeCredentials) {
                    cred.id = base64urlToUint8Array(cred.id);
                  }
                }

                // 2. Create credential
                const credential = await navigator.credentials.create({ publicKey: options });
                
                // Convert credential to JSON
                const credentialJSON = {
                  id: credential.id,
                  rawId: uint8ArrayToBase64url(new Uint8Array(credential.rawId)),
                  type: credential.type,
                  response: {
                    attestationObject: uint8ArrayToBase64url(new Uint8Array(credential.response.attestationObject)),
                    clientDataJSON: uint8ArrayToBase64url(new Uint8Array(credential.response.clientDataJSON))
                  }
                };

                // 3. Complete registration
                const completeResp = await fetch(`${API_BASE}/users/webauthn/register/complete`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify(credentialJSON)
                });

                if (completeResp.ok) {
                  Swal.fire({icon: 'success', title: 'تم بنجاح!', text: 'تم تسجيل مفتاح المرور الخاص بك.', customClass: { popup: 'swal-dark-popup' }});
                } else {
                  Swal.fire({icon: 'error', title: 'خطأ', text: 'فشل تسجيل مفتاح المرور.', customClass: { popup: 'swal-dark-popup' }});
                }
              } catch (err) {
                console.error(err);
                Swal.fire({icon: 'error', title: 'خطأ', text: 'حدث خطأ أثناء إعداد مفتاح المرور أو تم الإلغاء.', customClass: { popup: 'swal-dark-popup' }});
              }
            });
          }
        }
      });
    } else {
      // Check if it's a ban or soft block to show a more prominent message
      const message = data.message || data.error || "تم رفض الوصول. يرجى المحاولة مرة أخرى.";
      if (message.includes("حظر") || message.includes("تجاوز")) {
        Swal.fire({
          icon: 'error',
          title: 'تنبيه أمني',
          html: message.replace(/\n/g, '<br>'),
          confirmButtonText: 'موافق',
          confirmButtonColor: '#d33',
          customClass: {
            popup: 'swal-dark-popup'
          }
        });
      } else {
        showAlert(message, "danger");
      }
    }
  } catch (error) {
    showAlert("خطأ في الشبكة. يرجى المحاولة مرة أخرى.", "danger");
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

function escapeHTML(str) {
  if (!str) return "";
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function showAlert(message, type) {
  const resultDiv = document.getElementById("result");
  if (resultDiv) {
    resultDiv.innerHTML = `<div class="custom-alert custom-alert-${type}">${message}</div>`;
    // Auto-hide alert after 4 seconds for a clean UX
    setTimeout(() => {
      resultDiv.innerHTML = "";
    }, 4000);
  }
}

function base64urlToUint8Array(base64url) {
  const padding = '='.repeat((4 - base64url.length % 4) % 4);
  const base64 = (base64url + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

function uint8ArrayToBase64url(bytes) {
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
