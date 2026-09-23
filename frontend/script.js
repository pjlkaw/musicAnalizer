async function fetchData() {
    try {
        const response = await fetch("/stats", {
            headers: { Accept: "application/json" },
        });

        let data;
        try {
            data = await response.json();
        } catch {
            throw new Error("The server returned an invalid response.");
        }

        if (!response.ok) {
            throw new Error(data.error || `Request failed (${response.status}).`);
        }

        return data;
    } catch (error) {
        console.error("Could not load music stats:", error);
        return null;
    }
}

async function main() {
    const data = await fetchData();
    if (data) {
        console.log(data);
    }
}

main();
