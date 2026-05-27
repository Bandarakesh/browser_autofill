chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "GET_DOM") {
        sendResponse({ dom: extractFormDOM() });
    } else if (request.action === "EXECUTE_ACTIONS") {
        executeActions(request.actions);
        sendResponse({ status: "success" });
    }
});

function extractFormDOM() {
    // A simplified DOM extractor to send to the LLM.
    // It captures forms, inputs, buttons, and labels.
    const forms = document.querySelectorAll('form, input, select, textarea, button');
    let domString = "";
    
    // We can just clone the body and strip out non-form elements for simplicity,
    // or manually build a representation. Manual representation is smaller.
    
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        const id = input.id || input.name || '';
        const type = input.type || input.tagName.toLowerCase();
        let labelText = '';
        
        if (input.labels && input.labels.length > 0) {
            labelText = input.labels[0].innerText;
        } else if (input.placeholder) {
            labelText = input.placeholder;
        } else if (input.id) {
            const label = document.querySelector(`label[for="${input.id}"]`);
            if (label) labelText = label.innerText;
        }
        
        domString += `<input id="${id}" name="${input.name}" type="${type}" label="${labelText}">\n`;
    });
    
    const buttons = document.querySelectorAll('button, input[type="submit"]');
    buttons.forEach(btn => {
         const text = btn.innerText || btn.value;
         const id = btn.id || btn.name || '';
         domString += `<button id="${id}">${text}</button>\n`;
    });

    return domString;
}

function executeActions(actions) {
    actions.forEach(actionObj => {
        const { action, selector, value } = actionObj;
        const el = document.querySelector(selector);
        if (!el) {
            console.warn(`Element not found for selector: ${selector}`);
            return;
        }

        if (action === "type") {
            el.focus();
            el.value = value;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            el.blur();
        } else if (action === "click") {
            el.click();
        } else if (action === "select") {
             el.value = value;
             el.dispatchEvent(new Event('change', { bubbles: true }));
        }
        // Could handle file uploads here if the agent provides a file path or instructs the user
    });
}
