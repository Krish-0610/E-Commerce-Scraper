document.getElementById("searchForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    let query = document.getElementById("searchInput").value;
    let resultsDiv = document.getElementById("results");
    let loading = document.getElementById("loading");

    resultsDiv.innerHTML = ""; // Clear previous results
    loading.style.display = "block"; // Show loading message

    try {
        let response = await fetch(`http://127.0.0.1:5000/scrape?query=${query}`);
        let data = await response.json();

        loading.style.display = "none"; // Hide loading

        if (data.results.length === 0) {
            resultsDiv.innerHTML = "<p>No results found.</p>";
            return;
        }

        data.results.forEach(product => {
            resultsDiv.innerHTML += `
                <div class="product">
                    <h3>${product.title}</h3>
                    <p><strong>Price:</strong> ₹${product.price}</p>
                    <p><strong>Rating:</strong> ${product.rating}</p>
                    <a href="${product.link}" target="_blank">View on Amazon</a>
                </div>
            `;
        });
    } catch (error) {
        loading.style.display = "none";
        resultsDiv.innerHTML = "<p>Error fetching data.</p>";
    }
});



