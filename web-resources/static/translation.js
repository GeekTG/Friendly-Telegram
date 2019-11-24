//    Friendly Telegram (telegram userbot)
//    Copyright (C) 2018-2019 The Authors

//    This program is free software: you can redistribute it and/or modify
//    it under the terms of the GNU Affero General Public License as published by
//    the Free Software Foundation, either version 3 of the License, or
//    (at your option) any later version.

//    This program is distributed in the hope that it will be useful,
//    but WITHOUT ANY WARRANTY; without even the implied warranty of
//    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//    GNU Affero General Public License for more details.

//    You should have received a copy of the GNU Affero General Public License
//    along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
  reader.onload = function() {
    try {
      const data = JSON.parse(reader.result);
      modifiedElements = data;
      Array.from(document.getElementsByClassName("translation-input")).forEach(function(input) {
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
  reader.onerror = function() {
    console.log(reader.error);
    
  };
  reader.readAsText(file);
}

function importStringsFailed() {
  'use strict';
  document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
      message: "Import failed",
      timeout: 2000});
}

function importStringsSuccessful() {
  'use strict';
  document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
      message: "Import successful",
      timeout: 2000});
}

function exportStringsFailed() {
  'use strict';
  document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
      message: "Export failed",
      timeout: 2000});
}

