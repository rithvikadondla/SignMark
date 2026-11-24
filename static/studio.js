document.addEventListener("DOMContentLoaded", function () {

    // ==========================================
    // ELEMENTS
    // ==========================================

    const imageInput = document.getElementById("imageInput");
    const imagePreview = document.getElementById("imagePreview");

    const recognizeBtn = document.getElementById("recognizeBtn");
    const removeImageBtn = document.getElementById("removeImageBtn");
    const resetStudioBtn = document.getElementById("resetStudioBtn");

    const startCameraBtn = document.getElementById("startCamera");
    const stopCameraBtn = document.getElementById("stopCamera");

    const cameraPreview = document.getElementById("cameraPreview");
    const cameraStatus = document.getElementById("cameraStatus");

    const prediction = document.getElementById("prediction");
    const confidence = document.getElementById("confidence");
    const resultMessage = document.getElementById("resultMessage");
    const confidenceBar = document.getElementById("confidenceBar");

    const recognitionFeedback = document.getElementById("recognitionFeedback");
    const feedbackIcon = document.getElementById("feedbackIcon");
    const feedbackText = document.getElementById("feedbackText");

    const processingIndicator =
        document.getElementById("processingIndicator");


    // ==========================================
    // CONFIGURATION
    // ==========================================

    const API_IMAGE = "/api/predict/image";
    const API_FRAME = "/api/predict/frame";

    // Backend-supported modes
    const CURRENT_MODE = "alphabet";

    let cameraStream = null;
    let cameraTimer = null;
    let cameraBusy = false;


    // ==========================================
    // INITIAL STATE
    // ==========================================

    if (startCameraBtn) startCameraBtn.disabled = false;
    if (stopCameraBtn) stopCameraBtn.disabled = true;

    if (recognizeBtn) recognizeBtn.style.display = "none";

    if (processingIndicator) {
        processingIndicator.style.display = "none";
    }

    if (imagePreview) {
        imagePreview.style.display = "none";
    }


    // ==========================================
    // PROCESSING INDICATOR
    // ==========================================

    function showProcessing(message = "Processing Sign...") {

        if (processingIndicator) {
            processingIndicator.style.display = "block";

            const processingText =
                processingIndicator.querySelector("p");

            if (processingText) {
                processingText.textContent = message;
            }
        }
    }


    function hideProcessing() {

        if (processingIndicator) {
            processingIndicator.style.display = "none";
        }
    }


    // ==========================================
    // FEEDBACK
    // ==========================================

    function setFeedback(type, icon, message) {

        if (recognitionFeedback) {
            recognitionFeedback.className =
                "recognition-feedback " + type;
        }

        if (feedbackIcon) {
            feedbackIcon.textContent = icon;
        }

        if (feedbackText) {
            feedbackText.textContent = message;
        }
    }


    // ==========================================
    // CAMERA STATUS
    // ==========================================

    function setCameraStatus(message, background, color) {

        if (!cameraStatus) return;

        cameraStatus.textContent = message;
        cameraStatus.style.background = background;
        cameraStatus.style.color = color;
    }


    // ==========================================
    // RESET RECOGNITION
    // ==========================================

    function resetRecognition(
        message = "Upload an image and click Recognize Sign."
    ) {

        hideProcessing();

        if (prediction) {
            prediction.textContent = "--";
        }

        if (confidence) {
            confidence.textContent = "--";
        }

        if (resultMessage) {
            resultMessage.textContent = message;
        }

        if (confidenceBar) {
            confidenceBar.style.width = "0%";
        }

        setFeedback("ready", "✨", "Ready for recognition");
    }


    // ==========================================
    // DISPLAY PREDICTION
    // ==========================================

    function displayPrediction(data) {

        const label = data.label || "Unknown";

        let score = Number(data.confidence || 0);

        // Convert decimal confidence into percentage
        if (score <= 1) {
            score = score * 100;
        }

        score = Math.max(0, Math.min(100, score));

        if (prediction) {
            prediction.textContent = label;
        }

        if (confidence) {
            confidence.textContent = score.toFixed(2) + "%";
        }

        if (confidenceBar) {
            confidenceBar.style.width = score + "%";
        }

        if (data.status === "confident") {

            setFeedback(
                "success",
                "✅",
                "Sign recognized successfully!"
            );

            if (resultMessage) {
                resultMessage.textContent =
                    data.message || "Recognition completed successfully.";
            }

        } else {

            setFeedback(
                "ready",
                "⚠️",
                "Low confidence prediction"
            );

            if (resultMessage) {
                resultMessage.textContent =
                    data.message ||
                    "The sign was detected but confidence is low. Try again with better lighting.";
            }

        }

    }


    // ==========================================
    // API ERROR HANDLING
    // ==========================================

    async function readApiResponse(response) {

        let data;

        try {
            data = await response.json();
        } catch (error) {
            throw new Error("Server returned an invalid response.");
        }

        if (!response.ok || data.success === false) {

            let message =
                data.message ||
                data.error ||
                "Prediction request failed.";

            if (response.status === 401) {
                message = "Please login again to use sign recognition.";
            }

            if (response.status === 503) {
                message =
                    "AI model is currently unavailable. Check whether the model is loaded.";
            }

            throw new Error(message);
        }

        return data;
    }


    // ==========================================
    // IMAGE RECOGNITION
    // ==========================================

    async function recognizeUploadedImage() {

        const file = imageInput?.files?.[0];

        if (!file) {

            alert("Please upload an image first.");

            return;
        }

        if (recognizeBtn) {
            recognizeBtn.disabled = true;
        }

        showProcessing("AI is recognizing your sign...");

        setFeedback(
            "ready",
            "🤖",
            "AI is analyzing your image..."
        );

        if (resultMessage) {
            resultMessage.textContent =
                "Please wait while AI processes your image.";
        }

        try {

            const formData = new FormData();

            formData.append("file", file);
            formData.append("mode", CURRENT_MODE);

            const response = await fetch(API_IMAGE, {
                method: "POST",
                body: formData
            });

            const data = await readApiResponse(response);

            displayPrediction(data);

        } catch (error) {

            console.error("Image recognition error:", error);

            setFeedback(
                "ready",
                "❌",
                "Recognition failed"
            );

            if (resultMessage) {
                resultMessage.textContent = error.message;
            }

        } finally {

            hideProcessing();

            if (recognizeBtn) {
                recognizeBtn.disabled = false;
            }

        }

    }


    // ==========================================
    // RECOGNIZE BUTTON
    // ==========================================

    if (recognizeBtn) {

        recognizeBtn.addEventListener(
            "click",
            recognizeUploadedImage
        );

    }


    // ==========================================
    // STOP CAMERA
    // ==========================================

    function stopCamera() {

        if (cameraTimer) {
            clearInterval(cameraTimer);
            cameraTimer = null;
        }

        cameraBusy = false;

        if (cameraStream) {

            cameraStream.getTracks().forEach(function (track) {
                track.stop();
            });

            cameraStream = null;
        }

        if (cameraPreview) {
            cameraPreview.srcObject = null;
            cameraPreview.style.display = "none";
        }

        setCameraStatus(
            "⚪ Camera is inactive",
            "#f4f0ff",
            "#6c4ab6"
        );

        if (startCameraBtn) {
            startCameraBtn.disabled = false;
        }

        if (stopCameraBtn) {
            stopCameraBtn.disabled = true;
        }

    }


    // ==========================================
    // CAMERA FRAME CAPTURE
    // ==========================================

    async function sendCameraFrame() {

        if (
            !cameraPreview ||
            !cameraPreview.videoWidth ||
            !cameraPreview.videoHeight ||
            cameraBusy
        ) {
            return;
        }

        cameraBusy = true;

        try {

            const canvas = document.createElement("canvas");

            canvas.width = cameraPreview.videoWidth;
            canvas.height = cameraPreview.videoHeight;

            const context = canvas.getContext("2d");

            context.drawImage(
                cameraPreview,
                0,
                0,
                canvas.width,
                canvas.height
            );

            const imageData =
                canvas.toDataURL("image/jpeg", 0.75);

            const response = await fetch(API_FRAME, {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    mode: CURRENT_MODE,
                    image: imageData
                })

            });

            const data = await readApiResponse(response);

            displayPrediction(data);

        } catch (error) {

            console.error("Camera recognition error:", error);

            if (resultMessage) {
                resultMessage.textContent =
                    "Camera recognition error: " + error.message;
            }

        } finally {

            cameraBusy = false;

        }

    }


    // ==========================================
    // START CAMERA
    // ==========================================

    if (startCameraBtn) {

        startCameraBtn.addEventListener(
            "click",
            async function () {

                if (cameraStream) return;

                clearUploadedImage();

                resetRecognition("Starting camera...");

                showProcessing("Starting camera...");

                startCameraBtn.disabled = true;

                try {

                    cameraStream =
                        await navigator.mediaDevices.getUserMedia({
                            video: {
                                facingMode: "user"
                            },
                            audio: false
                        });

                    if (cameraPreview) {

                        cameraPreview.srcObject = cameraStream;
                        cameraPreview.style.display = "block";

                        await cameraPreview.play();

                    }

                    if (stopCameraBtn) {
                        stopCameraBtn.disabled = false;
                    }

                    setCameraStatus(
                        "🟢 Camera is active — AI recognition running",
                        "#e8f8ee",
                        "#218838"
                    );

                    hideProcessing();

                    if (resultMessage) {
                        resultMessage.textContent =
                            "Camera active. Show an ASL sign to the camera.";
                    }

                    setFeedback(
                        "ready",
                        "🤖",
                        "Waiting for hand sign..."
                    );

                    // AI checks camera frame periodically
                    cameraTimer = setInterval(
                        sendCameraFrame,
                        1500
                    );

                } catch (error) {

                    console.error("Camera start error:", error);

                    hideProcessing();

                    if (error.name === "NotAllowedError") {

                        setCameraStatus(
                            "🔴 Camera permission denied.",
                            "#fdeaea",
                            "#dc3545"
                        );

                    } else if (error.name === "NotFoundError") {

                        setCameraStatus(
                            "🔴 No camera found.",
                            "#fdeaea",
                            "#dc3545"
                        );

                    } else {

                        setCameraStatus(
                            "🔴 Unable to start camera.",
                            "#fdeaea",
                            "#dc3545"
                        );

                    }

                    startCameraBtn.disabled = false;

                    if (stopCameraBtn) {
                        stopCameraBtn.disabled = true;
                    }

                    if (resultMessage) {
                        resultMessage.textContent =
                            "Camera could not start. Check permissions and try again.";
                    }

                }

            }
        );

    }


    // ==========================================
    // STOP CAMERA BUTTON
    // ==========================================

    if (stopCameraBtn) {

        stopCameraBtn.addEventListener(
            "click",
            function () {

                stopCamera();

                resetRecognition(
                    "Camera stopped. Start it again when ready."
                );

            }
        );

    }


    // ==========================================
    // CLEAR IMAGE
    // ==========================================

    function clearUploadedImage() {

        if (imageInput) {
            imageInput.value = "";
        }

        if (imagePreview) {
            imagePreview.src = "";
            imagePreview.style.display = "none";
        }

        if (recognizeBtn) {
            recognizeBtn.style.display = "none";
            recognizeBtn.disabled = false;
        }

    }


    // ==========================================
    // IMAGE UPLOAD
    // ==========================================

    if (imageInput) {

        imageInput.addEventListener(
            "change",
            function () {

                const file = this.files[0];

                if (!file) return;

                // Validate file type
                if (
                    file.type !== "image/jpeg" &&
                    file.type !== "image/png"
                ) {

                    alert("Please upload a JPG or PNG image.");

                    clearUploadedImage();

                    resetRecognition(
                        "Please choose a JPG or PNG image."
                    );

                    return;
                }

                // Validate file size
                if (file.size > 5 * 1024 * 1024) {

                    alert("Image must be smaller than 5 MB.");

                    clearUploadedImage();

                    resetRecognition(
                        "Image is too large. Maximum size is 5 MB."
                    );

                    return;
                }

                // Stop camera if active
                stopCamera();

                resetRecognition(
                    "Image uploaded. Click Recognize Sign."
                );

                showProcessing("Loading image preview...");

                const reader = new FileReader();

                reader.onload = function (event) {

                    if (imagePreview) {

                        imagePreview.src = event.target.result;
                        imagePreview.style.display = "block";

                    }

                    if (recognizeBtn) {
                        recognizeBtn.style.display = "inline-block";
                        recognizeBtn.disabled = false;
                    }

                    hideProcessing();

                    if (resultMessage) {
                        resultMessage.textContent =
                            "Image ready. Click Recognize Sign to start AI.";
                    }

                };

                reader.onerror = function () {

                    hideProcessing();

                    clearUploadedImage();

                    resetRecognition(
                        "Unable to read image. Try another image."
                    );

                };

                reader.readAsDataURL(file);

            }
        );

    }


    // ==========================================
    // REMOVE IMAGE BUTTON
    // ==========================================

    if (removeImageBtn) {

        removeImageBtn.addEventListener(
            "click",
            function () {

                clearUploadedImage();

                resetRecognition(
                    "Image removed. Upload another image to continue."
                );

            }
        );

    }


    // ==========================================
    // RESET STUDIO BUTTON
    // ==========================================

    if (resetStudioBtn) {

        resetStudioBtn.addEventListener(
            "click",
            function () {

                clearUploadedImage();

                stopCamera();

                resetRecognition(
                    "Studio reset. Upload an image or start the camera."
                );

            }
        );

    }


});


// ==========================================
// CONFIDENCE METER
// ==========================================

function updateConfidenceMeter(value) {

    const confidenceBar =
        document.getElementById("confidenceBar");

    const confidenceText =
        document.getElementById("confidence");

    if (!confidenceBar) return;

    let percentage = parseFloat(value);

    if (isNaN(percentage)) {
        percentage = 0;
    }

    percentage = Math.max(
        0,
        Math.min(100, percentage)
    );

    confidenceBar.style.width = percentage + "%";

    if (confidenceText) {
        confidenceText.textContent =
            percentage.toFixed(2) + "%";
    }

}