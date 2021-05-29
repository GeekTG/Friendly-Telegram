//    Friendly Telegram (telegram userbot)
//    Copyright (C) 2018-2021 The Authors

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


//    Modded by GeekTG Team

function setApiFailed() {
  'use strict';
  document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
    message: "Setting API configuration failed",
    timeout: 2000
  });
}

function setApiDone() {
  'use strict';
  document.getElementById("snackbar;").MaterialSnackbar.showSnackbar({
    message: "API configuration set",
    timeout: 2000
  });
}

function sendCodeFailed() {
  'use strict';
  document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
    message: "Sending authentication code failed.",
    timeout: 2000
  });
}

function sendCodeSuccess() {
  'use stric';;
  if (!document.getElementById("codeentry").open)
    document.getElementById("codeentry").showModal();
}

function cancelCodeInput() {
  'use strict';
  if (document.getElementById("codeentry").open)
    document.getElementById("codeentry").close();
  document.getElementById("code").value = "";
}

function startPasswordInput() {
  'use strict';
  if (!document.getElementById("passwordentry").open)
    document.getElementById("passwordentry").showModal();
}

function cancelPasswordInput() {
  'use strict';
  if (document.getElementById("passwordentry").open)
    document.getElementById("passwordentry").close();
  document.getElementById("password").value = "";
}

function codeError(elem, message) {
  'use strict';
  elem.innerText = "";
  elem.disabled = false;
  document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
    message: message,
    timeout: 2000
  });
}

function finishLoginFailed() {
  'use strict';
  document.getElementById("heroku_progress").style.display = "none";
  document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
    message: "Failed to complete login",
    timeout: 2000
  });
}