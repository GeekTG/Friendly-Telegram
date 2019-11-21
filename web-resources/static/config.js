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

function setConfig(elem) {
  'use strict';
  const moduleNumber = elem.dataset.modulenum - 1;
  const configKey = elem.dataset.configkey;
  fetch("/setConfig", {method: "PUT", body: JSON.stringify({mid: moduleNumber, key: configKey,
    value: elem.value}), credentials: "include"})
  .then(function(response) {
    if (!response.ok) {
      console.log(response);
      setConfigFailed(elem);
    } else {
      setConfigDone(elem);
    }
  })
  .catch(function(response) {
    console.log(response);
    setConfigFailed(elem);
  });
}

function setConfigFailed(elem) {
  'use strict';
  elem.value = elem.dataset.currentvalue;
  document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
      message: "Setting configuration value failed",
      timeout: 2000});
}

function setConfigDone(elem) {
  'use strict';
  if (elem.value === "") {
    elem.value = elem.dataset.defaultvalue;
    elem.parentElement.className += " is-dirty";
  }
  elem.dataset.currentvalue = elem.value;
  document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
      message: "Configuration value set",
      timeout: 2000});
}

