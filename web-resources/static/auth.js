function beginAuthFlow(uid) {
  'use strict';
  fetch("/sendCode", {method: "POST", body: uid})
  .then(function(response) {
    if (!response.ok) {
      sendCodeFailed();
    } else {
      sendCodeSuccess(uid);
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

function sendCodeSuccess(uid) {
  'use strict';
  window.selectedUid = uid;
  document.getElementById("savedmsgslink").href = "tg://user?id=" + uid;
  try {
    document.getElementById("codeentry").showModal();
  } catch(unused) {}
}

function cancelCodeInput() {
  'use strict';
  document.getElementById("codeentry").close();
}

function codeChanged() {
  'use strict';
  const errorElem = document.getElementById("codeerror");
  const elem = document.getElementById("code");
  const newCode = elem.value;
  if (newCode.length > 0) {
    errorElem.style = ""; // Set by MDL
    errorElem.innerText = "Code must be 5 numerical digits";
  }
  if (newCode.length > 5) {
    elem.value = newCode.substring(0, 5);
    return;
  }
  if (newCode.length == 5) {
    elem.disabled = true;
    scrypt(newCode + window.selectedUid, "friendlytgbot", {
      N: 16384, r: 8, p: 1, dkLen: 64, encoding: "base64"}, function(hashedCode) {
        fetch("/code", {method: "POST", body: hashedCode + "\n" + window.selectedUid})
        .then(function(response) {
          if (!response.ok) {
            if (response.status == 401) {
              codeError(elem, errorElem, "Code invalid");
            } else if (response.status == 404) {
              codeError(elem, errorElem, "Code expired");
              beginAuthFlow(window.selectedUid);
            } else {
              codeError(elem, errorElem, "Server error");
            }
          } else {
            response.text()
            .then(function(secret) {
              document.cookie = "secret=" + secret;
              document.getElementById("codeentry").close();
              window.location.replace("/");
            });
          }
        })
        .catch(function(error) {
          console.log(error);
          codeError(elem, errorElem, "Network error");
        });
      }
    );
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
