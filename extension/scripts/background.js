const API_URL = 'http://localhost:8000';

let currentState = null; // Store the state returned by the backend

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "START_AUTOFILL") {
        handleAutofill(null, sendResponse);
        return true; // Indicates async response
    } else if (request.action === "SUBMIT_ANSWER") {
        handleAutofill(request.answer, sendResponse);
        return true;
    }
});

async function handleAutofill(userAnswer, sendResponse) {
    try {
        // 1. Get active tab
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        console.log("[AutofillAgent] Step 1 - Active tab:", tab.id, tab.url);
        
        // 2. Capture screenshot as a data URL (e.g. "data:image/jpeg;base64,ABC...")
        //    We split on ',' to strip the prefix and keep only the raw base64 string (e.g. "ABC...")
        //    The backend will re-attach the prefix before sending to GPT-4o.
        const dataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, { format: 'jpeg', quality: 50 });
        const base64Screenshot = dataUrl.split(',')[1];
        console.log("[AutofillAgent] Step 2 - Screenshot captured. Base64 length:", base64Screenshot.length);
        
        // 3. Get DOM from content script
        console.log("[AutofillAgent] Step 3 - Requesting DOM from content script...");
        const domResponse = await chrome.tabs.sendMessage(tab.id, { action: "GET_DOM" });
        const pageDom = domResponse.dom;
        console.log("[AutofillAgent] Step 3 - DOM received. Length:", pageDom.length);

        // 4. Call Backend API
        console.log("[AutofillAgent] Step 4 - Sending to backend:", `${API_URL}/process_page`);
        const payload = {
            page_dom: pageDom,
            page_screenshot: base64Screenshot, // Pure base64 string (no data:image/jpeg prefix)
            user_response: userAnswer || null,
            state_override: currentState
        };

        const response = await fetch(`${API_URL}/process_page`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errText = await response.text();
            throw new Error(`Backend returned ${response.status}: ${errText}`);
        }

        const result = await response.json();
        console.log("[AutofillAgent] Step 4 - Backend response:", result.status, result);

        // Save state for next interaction
        currentState = result.current_state;

        // 5. Execute actions if returned
        if (result.status === 'fill' && result.actions && result.actions.length > 0) {
            console.log("[AutofillAgent] Step 5 - Executing", result.actions.length, "actions...");
            await chrome.tabs.sendMessage(tab.id, { action: "EXECUTE_ACTIONS", actions: result.actions });
        } else if (result.status === 'ask') {
            console.log("[AutofillAgent] Step 5 - Agent is asking:", result.question);
        }

        sendResponse(result);

    } catch (error) {
        console.error("[AutofillAgent] Error:", error);
        sendResponse({ error: error.message });
    }
}
