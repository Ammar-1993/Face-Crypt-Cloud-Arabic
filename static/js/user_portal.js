const API_BASE = "";

const preview = document.getElementById("preview");
const captureButton = document.getElementById("captureButton");
const btnOpenCamera = document.getElementById("btnOpenCamera");
const stopCameraButton = document.getElementById("stopCameraButton");
const sendButton = document.getElementById("sendButton");
const retakeButton = document.getElementById("retakeButton");
const btnCancelCamera = document.getElementById("btnCancelCamera");
const cameraStream = document.getElementById("cameraStream");
const overlayCanvas = document.getElementById("overlayCanvas");
const openCameraWrapper = document.getElementById("openCameraWrapper");
const securityDisclaimer = document.getElementById("securityDisclaimer");

let stream = null;
let faceLandmarker = null;
let lastVideoTime = -1;
let animationFrameId = null;
let activeChallenge = null;
let challengeInitialState = null;

// MediaPipe Initialization
async function initializeMediaPipe() {
  const { FaceLandmarker, FilesetResolver } = window.Vision || window;
  if (!FaceLandmarker) return;
  
  try {
    const vision = await FilesetResolver.forVisionTasks("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@1.0.1/wasm");
    faceLandmarker = await FaceLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath: `https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task`,
        delegate: "GPU"
      },
      outputFaceBlendshapes: true,
      runningMode: "VIDEO",
      numFaces: 1
    });
  } catch (err) {
    console.error("Failed to initialize MediaPipe:", err);
  }
}

// Call init on load
initializeMediaPipe();

function startFaceDetection() {
  if (!faceLandmarker) return;
  overlayCanvas.width = cameraStream.videoWidth;
  overlayCanvas.height = cameraStream.videoHeight;
  const ctx = overlayCanvas.getContext("2d");

  function predict() {
    if (!cameraStream.videoWidth) {
      animationFrameId = requestAnimationFrame(predict);
      return;
    }
    
    if (cameraStream.currentTime !== lastVideoTime) {
      lastVideoTime = cameraStream.currentTime;
      const results = faceLandmarker.detectForVideo(cameraStream, performance.now());
      
      ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
      
      if (results.faceLandmarks && results.faceLandmarks.length > 0) {
        // Draw basic mesh
        const landmarks = results.faceLandmarks[0];
        
        ctx.fillStyle = "rgba(0, 255, 0, 0.5)";
        for (let pt of landmarks) {
          ctx.beginPath();
          ctx.arc(pt.x * overlayCanvas.width, pt.y * overlayCanvas.height, 1, 0, 2 * Math.PI);
          ctx.fill();
        }

        // Active Challenge Logic
        if (activeChallenge) {
          checkChallenge(results);
        }
      }
    }
    animationFrameId = requestAnimationFrame(predict);
  }
  predict();
}

function checkChallenge(results) {
  if (!results.faceBlendshapes || results.faceBlendshapes.length === 0) return;
  const blendshapes = results.faceBlendshapes[0].categories;
  
  // Find specific blendshapes
  const getScore = (name) => {
    const shape = blendshapes.find(b => b.categoryName === name);
    return shape ? shape.score : 0;
  };

  if (activeChallenge === "smile") {
    const smileLeft = getScore("mouthSmileLeft");
    const smileRight = getScore("mouthSmileRight");
    if (smileLeft > 0.5 && smileRight > 0.5) {
      completeChallenge();
    }
  } else if (activeChallenge === "turn_right") {
    const lookRight = getScore("eyeLookInLeft"); // If left eye looks in, head is turning right relative to camera
    const turnRight = getScore("headTurnRight") || lookRight; // Sometimes blendshapes might lack direct head pose, relying on eyes
    // A better approach for turn is using geometric landmarks, but blendshapes are easier.
    // Let's use simple nose vs eye geometry for turn:
    const landmarks = results.faceLandmarks[0];
    const nose = landmarks[1]; // tip of nose
    const leftEye = landmarks[33];
    const rightEye = landmarks[263];
    // If nose is closer to right eye (user's left) -> turning right
    const distToRightEye = Math.abs(nose.x - rightEye.x);
    const distToLeftEye = Math.abs(nose.x - leftEye.x);
    
    if (distToRightEye < distToLeftEye * 0.4) {
      completeChallenge();
    }
  } else if (activeChallenge === "raise_eyebrows") {
    const browInnerUp = getScore("browInnerUp");
    if (browInnerUp > 0.4) {
      completeChallenge();
    }
  }
}

function completeChallenge() {
  activeChallenge = null;
  Swal.close();
  Swal.fire({
    icon: 'success',
    title: 'تم اجتياز الفحص!',
    text: 'جاري التحضير...',
    timer: 1000,
    showConfirmButton: false
  });
  
  setTimeout(() => {
    captureFinalImage();
  }, 1000);
}

function captureFinalImage() {
  const canvas = document.createElement("canvas");
  canvas.width = cameraStream.videoWidth;
  canvas.height = cameraStream.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(cameraStream, 0, 0);

  preview.src = canvas.toDataURL("image/jpeg", 0.85);
  
  // UI Transitions
  preview.style.display = "block";
  cameraStream.style.display = "none";
  overlayCanvas.style.display = "none";
  captureButton.style.display = "none";
  stopCameraButton.style.display = "none";
  
  sendButton.style.display = "inline-block";
  retakeButton.style.display = "inline-block";
  btnCancelCamera.style.display = "inline-block";

  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
  }
  if (animationFrameId) cancelAnimationFrame(animationFrameId);
}

/**
 * State 1: Start Camera
 */
btnOpenCamera.addEventListener("click", async () => {
  try {
    if (!faceLandmarker) {
      btnOpenCamera.innerHTML = `<span class="fc-spinner"></span> جاري تحميل نموذج الذكاء الاصطناعي...`;
      await initializeMediaPipe();
    }

    stream = await navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 640 }, height: { ideal: 480 } } });
    cameraStream.srcObject = stream;
    
    // UI Transitions
    cameraStream.style.display = "block";
    overlayCanvas.style.display = "block";
    preview.style.display = "none";
    openCameraWrapper.classList.add("d-none");
    securityDisclaimer.classList.add("d-none");
    
    captureButton.style.display = "inline-block";
    stopCameraButton.style.display = "inline-block";
    
    sendButton.style.display = "none";
    retakeButton.style.display = "none";
    btnCancelCamera.style.display = "none";

    // Wait for video to be ready before starting detection
    cameraStream.onloadeddata = () => {
        startFaceDetection();
    };
  } catch (error) {
    showAlert("فشل في الوصول إلى الكاميرا أو تحميل النموذج. يرجى التأكد من الأذونات والاتصال.", "danger");
  } finally {
    // Reset button text
    btnOpenCamera.innerHTML = `<div class="btn-cta-icon" aria-hidden="true">📷</div>
            <div class="btn-cta-text">
              <span class="main-text">بدء التحقق من الوجه</span>
              <span class="sub-text">افتح الكاميرا لتسجيل دخول آمن</span>
            </div>`;
  }
});

/**
 * State 2: Capture Photo (Start Active Challenge)
 */
captureButton.addEventListener("click", () => {
  if (!faceLandmarker) {
      captureFinalImage(); // fallback if models fail
      return;
  }

  const challenges = [
    { code: "smile", text: "الرجاء الابتسام بوضوح" },
    { code: "turn_right", text: "أدر رأسك يمينًا قليلاً" },
    { code: "raise_eyebrows", text: "الرجاء رفع حاجبيك" }
  ];
  const randomChallenge = challenges[Math.floor(Math.random() * challenges.length)];
  
  activeChallenge = randomChallenge.code;

  Swal.fire({
    title: 'فحص الحيوية',
    text: randomChallenge.text,
    icon: 'info',
    showConfirmButton: false,
    allowOutsideClick: false
  });
});

/**
 * State 3: Retake Photo
 */
retakeButton.addEventListener("click", () => {
  preview.style.display = "none";
  sendButton.style.display = "none";
  retakeButton.style.display = "none";
  btnCancelCamera.style.display = "none";
  activeChallenge = null;
  
  btnOpenCamera.click(); 
});

/**
 * State 4: Cancel Camera/Preview
 */
btnCancelCamera.addEventListener("click", () => {
  if (stream) stream.getTracks().forEach((track) => track.stop());
  if (animationFrameId) cancelAnimationFrame(animationFrameId);
  
  cameraStream.style.display = "none";
  overlayCanvas.style.display = "none";
  preview.style.display = "none";
  activeChallenge = null;
  
  sendButton.style.display = "none";
  retakeButton.style.display = "none";
  btnCancelCamera.style.display = "none";
  
  openCameraWrapper.classList.remove("d-none");
  securityDisclaimer.classList.remove("d-none");
  preview.src = "#";
});

stopCameraButton.addEventListener("click", () => {
  if (stream) stream.getTracks().forEach((track) => track.stop());
  if (animationFrameId) cancelAnimationFrame(animationFrameId);
  
  cameraStream.style.display = "none";
  overlayCanvas.style.display = "none";
  captureButton.style.display = "none";
  stopCameraButton.style.display = "none";
  openCameraWrapper.classList.remove("d-none");
  securityDisclaimer.classList.remove("d-none");
  activeChallenge = null;
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

  sendButton.disabled = true;
  retakeButton.disabled = true;
  const originalBtnContent = sendButton.innerHTML;
  sendButton.innerHTML = `<span class="fc-spinner" role="status" aria-hidden="true"></span> جاري التحقق...`;

  try {
    const blob = dataURLtoBlob(imageData);
    if (blob.size === 0) throw new Error("❌ فشل في إنشاء بيانات الصورة.");

    const formData = new FormData();
    formData.append("image", blob, "capture.jpg");
    // Notice: We NO LONGER send image2 or challenge, because Liveness is verified on frontend!

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
                const beginResp = await fetch(`${API_BASE}/users/webauthn/register/begin`, { method: 'POST' });
                if (!beginResp.ok) throw new Error("Failed to start WebAuthn");
                const options = await beginResp.json();
                
                options.challenge = base64urlToUint8Array(options.challenge);
                options.user.id = base64urlToUint8Array(options.user.id);
                if (options.excludeCredentials) {
                  for (let cred of options.excludeCredentials) {
                    cred.id = base64urlToUint8Array(cred.id);
                  }
                }

                const credential = await navigator.credentials.create({ publicKey: options });
                
                const credentialJSON = {
                  id: credential.id,
                  rawId: uint8ArrayToBase64url(new Uint8Array(credential.rawId)),
                  type: credential.type,
                  response: {
                    attestationObject: uint8ArrayToBase64url(new Uint8Array(credential.response.attestationObject)),
                    clientDataJSON: uint8ArrayToBase64url(new Uint8Array(credential.response.clientDataJSON))
                  }
                };

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
      const message = data.message || data.error || "تم رفض الوصول. يرجى المحاولة مرة أخرى.";
      if (message.includes("حظر") || message.includes("تجاوز")) {
        Swal.fire({
          icon: 'error',
          title: 'تنبيه أمني',
          html: message.replace(/\n/g, '<br>'),
          confirmButtonText: 'موافق',
          confirmButtonColor: '#d33',
          customClass: { popup: 'swal-dark-popup' }
        });
      } else {
        showAlert(message, "danger");
      }
    }
  } catch (error) {
    showAlert("خطأ في الشبكة. يرجى المحاولة مرة أخرى.", "danger");
  } finally {
    sendButton.disabled = false;
    retakeButton.disabled = false;
    sendButton.innerHTML = originalBtnContent;
  }
});

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
    setTimeout(() => resultDiv.innerHTML = "", 4000);
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

/**
 * WebAuthn (Passkey) Login Flow
 */
const btnPasskeyLogin = document.getElementById("btnPasskeyLogin");
if (btnPasskeyLogin) {
  btnPasskeyLogin.addEventListener("click", async () => {
    btnPasskeyLogin.disabled = true;
    const originalContent = btnPasskeyLogin.innerHTML;
    btnPasskeyLogin.innerHTML = `<span class="fc-spinner" role="status" aria-hidden="true" style="margin-left:8px;"></span> جاري الإعداد...`;

    try {
      const beginResp = await fetch(`${API_BASE}/users/webauthn/login/begin`, { method: 'POST' });
      if (!beginResp.ok) throw new Error("Failed to start WebAuthn login");
      const options = await beginResp.json();

      options.challenge = base64urlToUint8Array(options.challenge);
      if (options.allowCredentials) {
        for (let cred of options.allowCredentials) {
          cred.id = base64urlToUint8Array(cred.id);
        }
      }

      btnPasskeyLogin.innerHTML = `<span class="fc-spinner" role="status" aria-hidden="true" style="margin-left:8px;"></span> في انتظار البصمة...`;
      const assertion = await navigator.credentials.get({ publicKey: options });

      const assertionJSON = {
        id: assertion.id,
        rawId: uint8ArrayToBase64url(new Uint8Array(assertion.rawId)),
        type: assertion.type,
        response: {
          authenticatorData: uint8ArrayToBase64url(new Uint8Array(assertion.response.authenticatorData)),
          clientDataJSON: uint8ArrayToBase64url(new Uint8Array(assertion.response.clientDataJSON)),
          signature: uint8ArrayToBase64url(new Uint8Array(assertion.response.signature)),
          userHandle: assertion.response.userHandle ? uint8ArrayToBase64url(new Uint8Array(assertion.response.userHandle)) : null
        }
      };

      btnPasskeyLogin.innerHTML = `<span class="fc-spinner" role="status" aria-hidden="true" style="margin-left:8px;"></span> جاري التحقق...`;
      const completeResp = await fetch(`${API_BASE}/users/webauthn/login/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(assertionJSON)
      });

      const data = await completeResp.json();

      if (completeResp.ok) {
        Swal.fire({
          icon: 'success',
          title: 'نجاح',
          html: `تم تسجيل الدخول بنجاح. أهلاً بك، <strong>${escapeHTML(data.user.name)}</strong>`,
          showConfirmButton: true,
          confirmButtonText: 'إغلاق',
          customClass: { popup: 'swal-dark-popup' }
        });
      } else {
        const message = data.message || data.error || "تم رفض الوصول. يرجى المحاولة مرة أخرى.";
        if (message.includes("حظر") || message.includes("تجاوز")) {
            Swal.fire({
                icon: 'error',
                title: 'تنبيه أمني',
                html: message.replace(/\n/g, '<br>'),
                confirmButtonText: 'موافق',
                confirmButtonColor: '#d33',
                customClass: { popup: 'swal-dark-popup' }
            });
        } else {
            showAlert(message, "danger");
        }
      }

    } catch (err) {
      console.error(err);
      showAlert("تم الإلغاء أو فشل تسجيل الدخول بمفتاح المرور.", "danger");
    } finally {
      btnPasskeyLogin.disabled = false;
      btnPasskeyLogin.innerHTML = originalContent;
    }
  });
}
