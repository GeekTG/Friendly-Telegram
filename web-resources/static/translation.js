//    Friendly Telegram Userbot
//    by GeekTG Team
var modifiedElements = {language: "en", data: {}};

function setString(elem) {
    'use strict';
    const stringKey = elem.dataset.module + "." + elem.dataset.stringkey;
    const data = modifiedElements.data;
    if (elem.value === "") {
        delete data[stringKey]
    } else {
        data[stringKey] = elem.value
    }
    const exporter = document.getElementById("export");
    URL.revokeObjectURL(exporter.href);
    exporter.href = URL.createObjectURL(new Blob([JSON.stringify(modifiedElements)], {type: "application/json"}));
}

function setLanguage(elem) {
    'use strict';
    modifiedElements.language = elem.value;
}

function loadTranslations(file) {
    'use strict';
    const reader = new FileReader();
    reader.onload = function () {
        try {
            const data = JSON.parse(reader.result);
            modifiedElements = data;
            Array.from(document.getElementsByClassName("translation-input")).forEach(function (input) {
                if (input.dataset.module + "." + input.dataset.stringkey in modifiedElements.data) {
                    input.value = modifiedElements.data[input.dataset.module + "." + input.dataset.stringkey];
                }
            });
            if (modifiedElements.language) {
                document.getElementById("lang-code").value = modifiedElements.language;
                document.getElementById("lang-code").parentElement.className += " is-dirty";
            }
        } catch (error) {
            console.log(error);

        }
    };
    reader.onerror = function () {
        console.log(reader.error);

    };
    reader.readAsText(file);
}

function importStringsFailed() {
    'use strict';
    document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
        message: "Import failed",
        timeout: 2000
    });
}

function importStringsSuccessful() {
    'use strict';
    document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
        message: "Import successful",
        timeout: 2000
    });
}

function exportStringsFailed() {
    'use strict';
    document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
        message: "Export failed",
        timeout: 2000
    });
}

