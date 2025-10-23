const scanBtn = document.getElementById("scan");
const status = document.getElementById("status");
const result = document.getElementById("result");

scanBtn.addEventListener("click", async () => {
  status.textContent = "Requesting cart from page...";
  result.textContent = "";

  try {
    const [tab] = await chrome.tabs.query({
      active: true,
      currentWindow: true,
    });
    const response = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => window.__FLINTpro_cart || null,
    });

    const cart = (response && response[0] && response[0].result) || null;
    if (!cart) {
      status.textContent = "No cart found on this page. Try a checkout page.";
      return;
    }

    status.textContent = "Sending cart to FLINTpro API...";
    const apiUrl = "http://localhost:5000/v1/assess_cart";
    const res = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cart }),
    });
    const data = await res.json();
    status.textContent = "Assessment complete";
    result.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    status.textContent = "Error: " + err.message;
    result.textContent = err.stack;
  }
});
