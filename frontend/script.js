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
                "Content-Type": "application/json"
            },
            body: JSON.stringify(requestData)
        });

        console.log("Received response:", response);

        if (!response.ok) {
            throw new Error("Failed to fetch data. Please try again.");
        }

        const data = await response.json();
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
    const timestamp = new Date().getTime(); // Prevent browser caching
    window.location.href = `http://127.0.0.1:5000/download?format=${format}&t=${timestamp}`;
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
                "Content-Type": "application/json"
            },
            body: JSON.stringify(requestData)
        });

        const data = await response.json();
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

async function fetchTrackedProducts() {
    console.log("Fetching tracked products....")
    try {
        const response = await fetch("http://127.0.0.1:5000/tracked_products");
        const products = await response.json();

        const tableBody = document.getElementById("trackedProductsTable").getElementsByTagName("tbody")[0];
        tableBody.innerHTML = "";

        products.forEach(product => {
            const row = tableBody.insertRow();
            row.innerHTML = `
                <td>${product.product_name}</td>
                <td>${product.platform}</td>
                <td>${product.current_price || "N/A"}</td>
                <td>${product.previous_price || "N/A"}</td>
                <td>${new Date(product.last_updated).toLocaleString()}</td>
                <td><a href="${product.product_url}" target="_blank">View</a></td>
            `;
        });
    } catch (error) {
        console.error("Error fetching tracked products:", error);
    }
}

// Call fetchTrackedProducts() on page load
document.addEventListener("DOMContentLoaded", () => {
    fetchTrackedProducts();
    // Note: searchProducts was removed from here as it shouldn't run automatically
});

document.getElementById("csvDownload")?.addEventListener("click", () => downloadData("csv"));
document.getElementById("jsonDownload")?.addEventListener("click", () => downloadData("json"));

async function updatePrices() {
    console.log("Updating price....")
    try {
        const response = await fetch("http://127.0.0.1:5000/update_prices", {
            method: "POST"
        });

        const data = await response.json();
        alert(data.message);
        fetchTrackedProducts(); // Refresh list after update
    } catch (error) {
        console.error("Error updating prices:", error);
    }
}