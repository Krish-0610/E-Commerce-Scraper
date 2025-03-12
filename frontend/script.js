document.addEventListener("DOMContentLoaded", function () {
    async function searchProducts() {
        const query = document.getElementById("searchQuery").value.trim();
        const platform = document.getElementById("platform").value;
        const resultsTable = document.getElementById("resultsTable").getElementsByTagName("tbody")[0];

        if (!query) {
            alert("Please enter a product name.");
            return;
        }

        // Clear previous results
        resultsTable.innerHTML = "<tr><td colspan='3'>Loading...</td></tr>";

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
                resultsTable.innerHTML = "<tr><td colspan='3'>No results found.</td></tr>";
                return;
            }

            // Populate table with results
            data.forEach(product => {
                const row = resultsTable.insertRow();
                row.innerHTML = `
                    <td>${product.title || "N/A"}</td>
                    <td>${product.price || "N/A"}</td>
                    <td>${product.rating || "N/A"}</td>
                `;
            });
        } catch (error) {
            console.error("Error:", error);
            resultsTable.innerHTML = `<tr><td colspan='3' style="color: red;">Error: ${error.message}</td></tr>`;
        }
    }

    function downloadData(format) {
        const timestamp = new Date().getTime(); // Prevent browser caching
        window.location.href = `http://127.0.0.1:5000/download?format=${format}&t=${timestamp}`;
    }
    document.getElementById("csvDownload")?.addEventListener("click", () => downloadData("csv"));
    document.getElementById("jsonDownload")?.addEventListener("click", () => downloadData("json"));
    // document.getElementById("xlsxDownload")?.addEventListener("click", () => downloadData("xlsx"));

    // Expose function to global scope
    window.searchProducts = searchProducts;
});

