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

function setApi(elem) {
  'use strict';
  if (elem.classList.contains("is-invalid")) {
    return;
  }
  fetch("/setApi", {method: "PUT", body: elem.value + document.getElementById("api_id").value, credentials: "include"})
  .then(function(response) {
    if (!response.ok) {
      console.log(response);
      setApiFailed(elem);
    } else {
      setApiDone(elem);
    }
  })
  .catch(function(response) {
    console.log(response);
    setApiFailed(elem);
  });
}

function setApiFailed(elem) {
  'use strict';
      document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
      message: "Setting API configuration failed",
      timeout: 2000});
}

function setApiDone(elem) {
  'use strict';
  document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
      message: "API configuration set",
      timeout: 2000});
}







function sendCode(elem) {
  'use strict';
  fetch("/sendTgCode", {method: "POST", body: elem.value})
  .then(function(response) {
    if (!response.ok) {
      console.log(response);
      sendCodeFailed();
    } else {
      sendCodeSuccess(elem);
    }
  })
  .catch(function(error) {
    console.log(error);
    sendCodeFailed();
  });
}

function sendCodeFailed() {
  'use strict';
  document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
      message: "Sending authentication code failed.",
      timeout: 2000});
}

function sendCodeSuccess(elem) {
  'use strict';
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

function codeChanged() {
  'use strict';
  const errorElem = document.getElementById("codeerror");
  const elem = document.getElementById("code")
  const newCode = elem.value;
  const password = document.getElementById("password").value;
  if (newCode.length > 0) {
    errorElem.style = ""; // Set by MDL
    errorElem.innerText = "Code must be 5 numerical digits";
  }
  if (newCode.length > 5) {
    elem.value = newCode.substring(0, 5);
    return;
  }
  if (newCode.length == 5 || password.length > 0) {
    elem.disabled = true;
    fetch("/tgCode", {method: "POST", body: elem.value + "\n" + document.getElementById("phone").value + "\n" + password})
    .then(function(response) {
      if (!response.ok) {
        console.log(response);
        if (response.status == 403) {
          codeError(elem, errorElem, "Code invalid");
        } else if (response.status == 401) {
          // Code correct, 2FA required
          cancelCodeInput();
          startPasswordInput();
        } else if (response.status == 404) {
          // Code expired, must re-send code request. Close dialog and wait for user action.
          cancelCodeInput();
          cancelPasswordInput();
        } else {
          codeError(elem, errorElem, "Server error");
        }
      } else {
        response.text()
        .then(function(secret) {
          document.cookie = "secret=" + secret;
          cancelCodeInput();
          cancelPasswordInput();
        })
        .catch(function(error) {
          console.log(error);
          codeError(elem, errorElem, "Network error");
        });
      }
    })
    .catch(function(error) {
      console.log(error);
      codeError(elem, errorElem, "Network error");
    });
  }
}

function codeError(elem, errorElem, message) {
  'use strict';
  elem.innerText = "";
  errorElem.innerText = message;
  errorElem.style.visibility = "visible";
  elem.disabled = false;
  elem.style.color = "inherit";
}

function finishLogin() {
  'use strict';
  fetch("/finishLogin", {method: "POST"})
  .then(function(response) {
    if (!response.ok) {
      finishLoginFailed();
    } else {
      window.location.reload(true);
    }
  })
  .catch(function(response) {
    console.log(response);
    finishLoginFailed();
  });
}

function finishLoginFailed() {
  'use strict';
  document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
    message: "Failed to complete login",
    timeout: 2000});
}
