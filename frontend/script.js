// Add authentication token to all API calls
function getAuthHeader() {
    const token = localStorage.getItem('token');
    console.log("Using token:", token);
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// Handle unauthorized responses
function handleUnauthorized() {
    console.log("Unauthorized access detected, redirecting to login");
    localStorage.removeItem('token');  // Clear invalid token
    localStorage.removeItem('user');   // Clear user data
    window.location.href = 'login.html';
}

// Check if user is authenticated
function isAuthenticated() {
    const token = localStorage.getItem('token');
    return token !== null && token !== undefined;
}

// Validate response for 401 errors
async function handleApiResponse(response) {
    if (response.status === 401) {
        handleUnauthorized();
        throw new Error("Unauthorized access");
    }
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.error || `Server error: ${response.status}`;
        throw new Error(errorMessage);
    }
    return response.json();
}

async function searchProducts() {
    console.log("searching products....")
    const query = document.getElementById("searchQuery").value.trim();
    const platform = document.getElementById("platform").value;
    const resultsTable = document.getElementById("resultsTable").getElementsByTagName("tbody")[0];

    if (!query) {
        alert("Please enter a product name.");
        return;
    }

    // Clear previous results
    resultsTable.innerHTML = "<tr><td colspan='4'>Loading...</td></tr>";

    // Prepare request payload
    const requestData = {
        platform: platform,
        query: query
    };

    console.log("Sending request with data:", requestData);

    try {
        // Send POST request to the API
        const response = await fetch("http://127.0.0.1:5000/scrape", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...getAuthHeader()
            },
            body: JSON.stringify(requestData)
        });

        console.log("Received response:", response);

        const data = await handleApiResponse(response);
        console.log("Received data:", data);

        // Clear loading text
        resultsTable.innerHTML = "";

        if (data.length === 0) {
            resultsTable.innerHTML = "<tr><td colspan='4'>No results found.</td></tr>";
            return;
        }

        // Update the table header to include a Track column if it doesn't exist
        const tableHeader = document.getElementById("resultsTable").getElementsByTagName("thead")[0];
        if (tableHeader.rows[0].cells.length === 3) {
            const headerCell = tableHeader.rows[0].insertCell(3);
            headerCell.textContent = "Actions";
        }

        // Populate table with results
        data.forEach(product => {
            const row = resultsTable.insertRow();
            row.innerHTML = `
                <td>${product.title || "N/A"}</td>
                <td>${product.price || "N/A"}</td>
                <td>${product.rating || "N/A"}</td>
                <td>
                    <button class="track-btn" data-url="${product.url || ''}" >
                        Track
                    </button>
                </td>
            `;
        });

        // Add event listeners to all track buttons
        document.querySelectorAll('.track-btn').forEach(button => {
            button.addEventListener('click', function () {
                const productUrl = this.getAttribute('data-url');
                // Auto-fill the tracking form
                document.getElementById("trackProductUrl").value = productUrl;
                // Scroll to the tracking form
                document.getElementById("trackProductUrl").scrollIntoView({ behavior: "smooth" });
            });
        });
    } catch (error) {
        console.error("Error:", error);
        resultsTable.innerHTML = `<tr><td colspan='4' style="color: red;">Error: ${error.message}</td></tr>`;
    }
}

function downloadData(format) {
    const timestamp = new Date().getTime();
    
    // Create an invisible anchor element
    const link = document.createElement('a');
    link.href = `http://127.0.0.1:5000/download?format=${format}&t=${timestamp}`;
    
    // Add authorization header
    link.setAttribute('download', '');
    
    // Append to document, click it, and remove it
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

async function trackProduct() {
    console.log("Tracking products...")
    const productUrl = document.getElementById("trackProductUrl").value.trim();
    const priceThreshold = document.getElementById("priceThreshold").value || null;
    const statusElement = document.getElementById("trackingStatus") ||  document.createElement("div")

    statusElement.id = "trackingStatus";
    statusElement.className = "tracking-status";
    statusElement.textContent = "Tracking product... Please wait";

    const formElement = document.getElementById("trackProductForm");
    if (formElement && !document.getElementById("trackingStatus")) {
        formElement.parentNode.insertBefore(statusElement, formElement.nextSibling);
    }

    if (!productUrl) {
        alert("Please enter product name and URL.");
        return;
    }

    const requestData = {
        product_url: productUrl,
        price_threshold: priceThreshold
    };

    try {
        const response = await fetch("http://127.0.0.1:5000/track", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...getAuthHeader()
            },
            body: JSON.stringify(requestData)
        });

        const data = await handleApiResponse(response);
        statusElement.textContent = (data.message || "Product added successfully!");

        fetchTrackedProducts(); // Refresh list

        // Clear the form fields after successful tracking
        document.getElementById("trackProductUrl").value = "";
        document.getElementById("priceThreshold").value = "";
    } catch (error) {
        console.error("Error tracking product:", error);
        statusElement.textContent = "Error tracking product"
    }
}

async function removeProduct(productId) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/remove_tracked_product/${productId}`, {
            method: "DELETE",
            headers: getAuthHeader()
        });

        const data = await handleApiResponse(response);
        alert(data.message);
        fetchTrackedProducts(); // Refresh list after removal
    } catch (error) {
        console.error("Error removing product:", error);
        alert("Failed to remove product. Please try again.");
    }
}

async function fetchTrackedProducts() {
    console.log("Fetching tracked products....");
    
    // Debug: Check if token exists and print headers that will be sent
    const token = localStorage.getItem('token');
    console.log("Token in localStorage:", token);
    console.log("Auth headers being sent:", getAuthHeader());
    
    try {
        const response = await fetch("http://127.0.0.1:5000/tracked_products", {
            method: "GET",
            headers: getAuthHeader()
        });
        
        console.log("Response status:", response.status);
        
        const data = await handleApiResponse(response);
        console.log("Tracked products data:", data);

        const tableBody = document.getElementById("trackedProductsTable").getElementsByTagName("tbody")[0];
        tableBody.innerHTML = "";

        if (data.length === 0) {
            tableBody.innerHTML = "<tr><td colspan='7'>No products tracked yet.</td></tr>";
            return;
        }

        data.forEach(product => {
            const row = tableBody.insertRow();
            row.innerHTML = `
                <td>${product.product_name}</td>
                <td>${product.platform}</td>
                <td>${product.current_price || "N/A"}</td>
                <td>${product.previous_price || "N/A"}</td>
                <td>${new Date(product.last_updated).toLocaleString()}</td>
                <td><a href="${product.product_url}" target="_blank">View</a></td>
                <td><button class="remove-btn" onclick="removeProduct(${product.id})">Remove</button></td>
            `;
        });
    } catch (error) {
        console.error("Error fetching tracked products:", error);
        const tableBody = document.getElementById("trackedProductsTable").getElementsByTagName("tbody")[0];
        tableBody.innerHTML = `<tr><td colspan="7" style="color: red;">Error: ${error.message}</td></tr>`;
    }
}

// Check authentication on page load
document.addEventListener("DOMContentLoaded", () => {
    console.log("DOM loaded, checking authentication...");
    if (!isAuthenticated()) {
        console.log("No token found, redirecting to login");
        window.location.href = 'login.html';
        return;
    }
    
    // Test authentication is working
    console.log("Token found, testing authentication...");
    fetch("http://127.0.0.1:5000/check-auth", {
        headers: getAuthHeader()
    })
    .then(response => {
        console.log("Auth check response:", response.status);
        return handleApiResponse(response);
    })
    .then(data => {
        console.log("Authentication successful:", data);
        fetchTrackedProducts();
    })
    .catch(error => {
        console.error("Authentication error:", error);
        if (error.message.includes("Unauthorized")) {
            handleUnauthorized();
        }
    });
});

document.getElementById("csvDownload")?.addEventListener("click", () => downloadData("csv"));
document.getElementById("jsonDownload")?.addEventListener("click", () => downloadData("json"));

async function updatePrices() {
    console.log("Updating price....")
    try {
        const response = await fetch("http://127.0.0.1:5000/update_prices", {
            method: "POST",
            headers: getAuthHeader()
        });

        const data = await handleApiResponse(response);
        alert(data.message);
        fetchTrackedProducts(); // Refresh list after update
    } catch (error) {
        console.error("Error updating prices:", error);
    }
}