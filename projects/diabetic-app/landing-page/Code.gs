/**
 * GLP1Companion Email Waitlist - Google Apps Script
 * 
 * Instructions:
 * 1. Go to https://script.google.com
 * 2. Create a new project
 * 3. Paste this code
 * 4. Create a Google Sheet and copy its ID from the URL
 * 5. Update the SHEET_ID below
 * 6. Deploy as Web App (Execute as: Me, Anyone can access)
 * 7. Copy the URL and update your landing page
 */

// TODO: Replace with your actual Google Sheet ID
// The sheet should have headers in row 1: Timestamp, Email, Source
const SHEET_ID = '1-yU8wED1z37Vp2_TN7YtQe0kzzeUHyLUg0TPprLxdSo';

function doPost(e) {
  try {
    const sheet = SpreadsheetApp.openById(SHEET_ID).getActiveSheet();
    
    // Get form data
    const email = e.parameter.email || '';
    const timestamp = new Date();
    const source = e.parameter.source || 'unknown';
    
    if (!email) {
      return createResultHtml(false, 'Email is required');
    }
    
    // Append to sheet
    sheet.appendRow([timestamp, email, source]);
    
    return createResultHtml(true, 'Email submitted successfully!');
    
  } catch (error) {
    return createResultHtml(false, 'Error: ' + error.message);
  }
}

function doGet() {
  return HtmlService.createHtmlOutput(
    JSON.stringify({ status: 'active', message: 'GLP1Companion Email API is running' })
  ).setMimeType(HtmlService.MimeType.JSON);
}

/**
 * Create HTML result that communicates back to the parent page
 * This avoids CORS by not making a cross-origin JSON request
 */
function createResultHtml(success, message) {
  const result = JSON.stringify({ success: success, message: message });
  
  // HTML that posts message to parent and shows result
  const html = HtmlService.createHtmlOutput(`
<!DOCTYPE html>
<html>
<head>
  <base target="_top">
  <script>
    // Send result to parent window (for iframe scenarios)
    if (window.parent !== window) {
      try {
        window.parent.postMessage({
          type: 'glp1-form-result',
          success: ${success},
          message: '${message.replace(/'/g, "\\'")}'
        }, '*');
      } catch(e) {}
    }
    
    // Store result in sessionStorage for the original page to retrieve
    try {
      sessionStorage.setItem('glp1-form-result', '${result.replace(/'/g, "\\'")}');
    } catch(e) {}
    
    // Also store in localStorage as backup
    try {
      localStorage.setItem('glp1-form-result', '${result.replace(/'/g, "\\'")}');
    } catch(e) {}
  </script>
  <style>
    body { 
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      padding: 40px; 
      text-align: center;
      background: #0a0a0a;
      color: white;
    }
    .result { 
      padding: 20px; 
      border-radius: 12px;
      max-width: 400px;
      margin: 0 auto;
    }
    .success { 
      background: rgba(48, 209, 88, 0.15); 
      border: 1px solid #30d158;
      color: #30d158;
    }
    .error { 
      background: rgba(255, 59, 48, 0.15); 
      border: 1px solid #ff375f;
      color: #ff375f;
    }
    h2 { margin: 0 0 10px 0; }
    p { margin: 0; opacity: 0.8; }
    .redirect-note {
      margin-top: 20px;
      font-size: 12px;
      opacity: 0.5;
    }
  </style>
</head>
<body>
  <div class="result ${success ? 'success' : 'error'}">
    <h2>${success ? '✓ Success!' : '✗ Error'}</h2>
    <p>${message}</p>
  </div>
  <p class="redirect-note">
    You can close this window and return to the app.
  </p>
</body>
</html>`).setTitle('GLP1Companion - Result');
  
  return html;
}
