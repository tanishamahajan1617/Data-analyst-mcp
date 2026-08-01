const form =
    document.getElementById("uploadForm");

const fileInput =
    document.getElementById("fileInput");

const uploadButton =
    document.getElementById("uploadButton");

const loading =
    document.getElementById("loading");

const result =
    document.getElementById("result");

const error =
    document.getElementById("error");

const filename =
    document.getElementById("filename");

const datasetId =
    document.getElementById("datasetId");

const rows =
    document.getElementById("rows");

const columns =
    document.getElementById("columns");

const continueMessage =
    document.getElementById("continueMessage");

const copyButton =
    document.getElementById("copyButton");


function resetUI() {

    loading.hidden = true;

    result.hidden = true;

    error.hidden = true;

    error.textContent = "";

}


function showError(message) {

    error.hidden = false;

    error.textContent = message;

}


form.addEventListener(
    "submit",
    async (event) => {

        event.preventDefault();

        resetUI();

        const file =
            fileInput.files[0];

        if (!file) {

            showError(
                "Please choose a CSV or XLSX file."
            );

            return;
        }

        const formData =
            new FormData();

        formData.append(
            "file",
            file
        );

        loading.hidden = false;

        uploadButton.disabled = true;

        uploadButton.textContent =
            "Uploading...";

        try {

            const response =
                await fetch(
                    "/api/v1/datasets/upload",
                    {
                        method: "POST",
                        body: formData,
                    }
                );

            const data =
                await response.json();

            if (!response.ok) {

                throw new Error(
                    data.detail ??
                    "Upload failed."
                );

            }

            filename.textContent =
                data.filename;

            datasetId.textContent =
                data.dataset_id;

            rows.textContent =
                data.rows;

            columns.textContent =
                data.columns;

            continueMessage.value =
`My dataset has been uploaded successfully.

Dataset ID: ${data.dataset_id}

Please analyze this dataset, automatically clean it if appropriate, generate insights, and build a Power BI dashboard.`;

            loading.hidden = true;

            result.hidden = false;

        }

        catch (err) {

            loading.hidden = true;

            showError(
                err.message ??
                "Unexpected error."
            );

        }

        finally {

            uploadButton.disabled = false;

            uploadButton.textContent =
                "Upload Dataset";

        }

    }
);


copyButton.addEventListener(
    "click",
    async () => {

        try {

            await navigator.clipboard.writeText(
                continueMessage.value
            );

            const original =
                copyButton.textContent;

            copyButton.textContent =
                "✓ Message Copied";

            setTimeout(
                () => {

                    copyButton.textContent =
                        original;

                },
                2000
            );

        }

        catch {

            alert(
                "Unable to copy message."
            );

        }

    }
);