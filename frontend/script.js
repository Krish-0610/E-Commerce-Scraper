
/* Demo Script */

document.getElementById('start-btn').addEventListener('click', () => {
    const url = document.getElementById('url-input').value;
    const parameter = document.getElementById('parameters').value;

    if (!url) {
        alert('Please enter a valid URL.');
        return;
    }

    document.getElementById('status-text').textContent = 'Scraping in progress...';

    let progress = 0;
    const progressInterval = setInterval(() => {
        if (progress >= 100) {
            clearInterval(progressInterval);
            document.getElementById('status-text').textContent = 'Scraping completed!';
            populateResults();
        } else {
            progress += 20;
            document.getElementById('progress').style.width = progress + '%';
        }
    }, 500);
});

function populateResults() {
    const resultsTable = document.getElementById('results-table');
    resultsTable.innerHTML = `
        <tr>
            <td>Example Product 1</td>
            <td>$100</td>
            <td>4.5</td>
            <td>150</td>
            <td>In Stock</td>
        </tr>
        <tr>
            <td>Example Product 2</td>
            <td>$200</td>
            <td>4.0</td>
            <td>200</td>
            <td>Out of Stock</td>
        </tr>
    `;
}
document.addEventListener('DOMContentLoaded', () => {
    const historyData = [
        { date: '2025-01-01', website: 'example.com', products: 10 },
        { date: '2025-01-02', website: 'example2.com', products: 15 },
    ];

    const historyTable = document.getElementById('history-table');
    historyData.forEach(entry => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${entry.date}</td>
            <td>${entry.website}</td>
            <td>${entry.products}</td>
            <td><button class="view-btn">View</button></td>
        `;
        historyTable.appendChild(row);
    });
});
document.addEventListener('click', (event) => {
    if (event.target.classList.contains('view-btn')) {
        const row = event.target.closest('tr');
        const date = row.children[0].textContent;
        const website = row.children[1].textContent;
        const products = row.children[2].textContent;

        const resultsTable = document.getElementById('results-table');
        resultsTable.innerHTML = `
            <tr>
                <td>Example Product from ${website}</td>
                <td>$100</td>
                <td>4.5</td>
                <td>150</td>
                <td>In Stock</td>
            </tr>
            <tr>
                <td>Example Product from ${website}</td>
                <td>$200</td>
                <td>4.0</td>
                <td>200</td>
                <td>Out of Stock</td>
            </tr>
        `;

        document.getElementById('status-text').textContent = `Viewing data from ${website} scraped on ${date}`;
    }
});
document.getElementById('export-btn').addEventListener('click', () => {
    const filename = document.getElementById('filename').value;
    const format = document.getElementById('file-format').value;

    if (!filename) {
        alert('Please enter a valid filename.');
        return;
    }

    document.getElementById('export-status').innerHTML = '<p>Exporting data as ' + format.toUpperCase() + '...</p>';

    setTimeout(() => {
        document.getElementById('export-status').innerHTML = '<p>Export completed! Your file "' + filename + '" has been downloaded.</p>';
    }, 2000);
});