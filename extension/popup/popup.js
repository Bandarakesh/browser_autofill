const API_URL = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', () => {
    const uploadBtn = document.getElementById('upload-btn');
    const autofillBtn = document.getElementById('autofill-btn');
    const recordBtn = document.getElementById('record-btn');
    const submitAnswerBtn = document.getElementById('submit-answer-btn');
    
    // Resume Upload
    uploadBtn.addEventListener('click', async () => {
        const fileInput = document.getElementById('resume-upload');
        const statusDiv = document.getElementById('upload-status');
        
        if (!fileInput.files.length) {
            statusDiv.textContent = 'Please select a file first.';
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        statusDiv.textContent = 'Uploading and parsing...';
        try {
            const response = await fetch(`${API_URL}/upload_resume`, {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            statusDiv.textContent = result.message;
        } catch (e) {
            statusDiv.textContent = 'Error: ' + e.message;
        }
    });

    // Autofill Trigger
    autofillBtn.addEventListener('click', () => {
        const statusDiv = document.getElementById('autofill-status');
        statusDiv.textContent = 'Processing page...';
        document.getElementById('question-section').classList.add('hidden');
        
        // Send message to background script to start the process
        chrome.runtime.sendMessage({ action: "START_AUTOFILL" }, (response) => {
            if (chrome.runtime.lastError) {
                statusDiv.textContent = 'Extension Error: ' + chrome.runtime.lastError.message;
                return;
            }
            if (!response) {
                statusDiv.textContent = 'Error: No response from background script.';
                return;
            }
            if (response.status === 'ask') {
                statusDiv.textContent = 'Agent needs input.';
                showQuestion(response.question);
            } else if (response.status === 'fill') {
                statusDiv.textContent = 'Autofill complete.';
            } else if (response.error) {
                statusDiv.textContent = 'Error: ' + response.error;
            }
        });
    });

    // Submit Answer to Agent
    submitAnswerBtn.addEventListener('click', () => {
        const answer = document.getElementById('user-answer').value;
        const statusDiv = document.getElementById('autofill-status');
        if (!answer) return;
        
        statusDiv.textContent = 'Sending answer...';
        document.getElementById('question-section').classList.add('hidden');
        document.getElementById('user-answer').value = '';

        chrome.runtime.sendMessage({ action: "SUBMIT_ANSWER", answer: answer }, (response) => {
            if (chrome.runtime.lastError) {
                statusDiv.textContent = 'Extension Error: ' + chrome.runtime.lastError.message;
                return;
            }
            if (!response) {
                statusDiv.textContent = 'Error: No response from background script.';
                return;
            }
            if (response.status === 'ask') {
                showQuestion(response.question);
            } else if (response.status === 'fill') {
                statusDiv.textContent = 'Autofill complete.';
            } else if (response.error) {
                statusDiv.textContent = 'Error: ' + response.error;
            } else {
                statusDiv.textContent = 'Done.';
            }
        });
    });

    function showQuestion(questionText) {
        document.getElementById('question-section').classList.remove('hidden');
        document.getElementById('agent-question').textContent = questionText;
    }

    // Voice Recording using WebKit Speech API
    let recognition;
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = function() {
            document.getElementById('voice-status').textContent = 'Listening...';
            recordBtn.textContent = '🛑 Stop';
        };

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            document.getElementById('user-answer').value = transcript;
            document.getElementById('voice-status').textContent = 'Done listening.';
            recordBtn.textContent = '🎤 Voice';
        };

        recognition.onerror = function(event) {
            document.getElementById('voice-status').textContent = 'Error: ' + event.error;
            recordBtn.textContent = '🎤 Voice';
        };

        recognition.onend = function() {
            recordBtn.textContent = '🎤 Voice';
        };
    }

    recordBtn.addEventListener('click', () => {
        if (recordBtn.textContent.includes('Stop')) {
            recognition.stop();
        } else {
            if (recognition) {
                recognition.start();
            } else {
                document.getElementById('voice-status').textContent = 'Speech API not supported.';
            }
        }
    });

    /* 
    // ALTERNATIVE: Uploading audio file to backend model
    // Commented out as requested by user.
    let mediaRecorder;
    let audioChunks = [];
    
    recordBtn.addEventListener('click', async () => {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            recordBtn.textContent = '🎤 Voice';
            return;
        }
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };
            
            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const formData = new FormData();
                formData.append('file', audioBlob, 'voice.webm');
                
                document.getElementById('voice-status').textContent = 'Sending audio to backend...';
                
                // Example API call to backend to transcribe audio
                // const res = await fetch(`${API_URL}/transcribe`, { method: 'POST', body: formData });
                // const data = await res.json();
                // document.getElementById('user-answer').value = data.text;
                
                document.getElementById('voice-status').textContent = 'Audio processed.';
            };
            
            mediaRecorder.start();
            recordBtn.textContent = '🛑 Stop';
            document.getElementById('voice-status').textContent = 'Recording...';
        } catch (err) {
             document.getElementById('voice-status').textContent = 'Mic access denied.';
        }
    });
    */
});
