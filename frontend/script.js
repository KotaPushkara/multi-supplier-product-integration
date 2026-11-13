
const API = "http://127.0.0.1:8000";

const formatNumber = (value) =>
    Number(value || 0).toLocaleString("en-IN");

async function loadMetrics() {
    const response = await fetch(`${API}/metrics`);
    if (!response.ok) throw new Error("Could not load metrics");

    const data = await response.json();

    document.getElementById("products").textContent =
        formatNumber(data.products);

    document.getElementById("sources").textContent =
        formatNumber(data.sources);

    document.getElementById("provenance").textContent =
        formatNumber(data.provenance);

    document.getElementById("rejected").textContent =
        formatNumber(data.rejected);
}

async function loadProducts() {
    const response = await fetch(`${API}/products?limit=10`);
    if (!response.ok) throw new Error("Could not load products");

    const data = await response.json();
    const table = document.getElementById("productsTable");

    table.replaceChildren();

    data.products.forEach(product => {
        const row = document.createElement("tr");

        [
            product.product_id,
            product.name,
            product.brand,
            product.category,
            product.price,
            product.gtin
        ].forEach(value => {
            const cell = document.createElement("td");
            cell.textContent = value ?? "-";
            row.appendChild(cell);
        });

        table.appendChild(row);
    });

    if (data.products.length === 0) {
        table.innerHTML = '<tr><td colspan="6">No products found.</td></tr>';
    }
}

async function loadRuns() {
    const response = await fetch(`${API}/runs?limit=10`);
    if (!response.ok) throw new Error("Could not load pipeline runs");

    const data = await response.json();
    const table = document.getElementById("runsTable");

    table.replaceChildren();

    data.runs.forEach(run => {
        const row = document.createElement("tr");

        const values = [
            run.run_id,
            run.status,
            run.input_rows,
            run.accepted_rows,
            run.rejected_rows,
            run.duplicate_rows,
            run.output_rows
        ];

        values.forEach((value, index) => {
            const cell = document.createElement("td");
            cell.textContent = value ?? "-";

            if (index === 1) {
                cell.className =
                    run.status === "SUCCESS" ? "success" : "failed";
            }

            row.appendChild(cell);
        });

        table.appendChild(row);
    });

    if (data.runs.length === 0) {
        table.innerHTML = '<tr><td colspan="7">No pipeline runs found.</td></tr>';
    }
}

async function loadRejected() {
    const response = await fetch(`${API}/rejected?limit=10`);
    if (!response.ok) throw new Error("Could not load rejected records");

    const data = await response.json();
    const table = document.getElementById("rejectedTable");

    table.replaceChildren();

    data.rejected_records.forEach(record => {
        const row = document.createElement("tr");

        const values = [
            record.reject_id,
            record.run_id,
            record.supplier_name,
            record.source_data,
            record.rejection_reason,
            record.created_at
        ];

        values.forEach(value => {
            const cell = document.createElement("td");
            cell.textContent = value ?? "-";
            row.appendChild(cell);
        });

        table.appendChild(row);
    });

    if (data.rejected_records.length === 0) {
        table.innerHTML =
            '<tr><td colspan="6">No rejected records found.</td></tr>';
    }
}

async function refreshDashboard() {
    const message = document.getElementById("message");

    try {
        await Promise.all([
            loadMetrics(),
            loadProducts(),
            loadRuns(),
            loadRejected()
        ]);

        message.textContent = "Dashboard data loaded successfully.";
    } catch (error) {
        message.textContent =
            "Unable to load dashboard. Check the backend server.";
        console.error(error);
    }
}

document.getElementById("runBtn").addEventListener("click", async () => {
    const button = document.getElementById("runBtn");
    const message = document.getElementById("message");

    button.disabled = true;
    button.textContent = "Running...";
    message.textContent = "Pipeline is processing. Please wait...";

    try {
        const response = await fetch(`${API}/run`, {
            method: "POST"
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "Pipeline execution failed");
        }

        message.textContent =
            `Pipeline ${result.status}. Processed ${formatNumber(result.input_rows)} records.`;

        await refreshDashboard();

    } catch (error) {
        message.textContent = `Error: ${error.message}`;
    } finally {
        button.disabled = false;
        button.textContent = "Run Pipeline";
    }
});

refreshDashboard();
