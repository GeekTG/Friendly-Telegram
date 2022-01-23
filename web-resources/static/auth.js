var salt = "";

function beginAuthFlow(uid) {
  fetch("/sendCode", {method: "POST", body: uid})
  .then(function(response) {
    if (!response.ok) {
      sendCodeFailed();
    } else {
      response.text().then(function(resp) {
        salt = resp;
        sendCodeSuccess(uid);
      });
    }
  })
  .catch(function(error) {
    console.log(error);
    sendCodeFailed();
  });
}

function sendCodeFailed() {
  document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
      message: "Sending authentication code failed.",
      timeout: 2000});
}

function sendCodeSuccess(uid) {
  window.selectedUid = uid;
  Swal.fire({
    title: 'Enter auth code',
    input: 'text',
    inputAttributes: {
      autocapitalize: 'off'
    },
    showCancelButton: true,
    confirmButtonText: 'Login',
    showLoaderOnConfirm: true,
    preConfirm: (login) => {
      return fetch("/code", {method: "POST", body: login + "\n" + window.selectedUid})
        .then(function(response) {
          if (!response.ok) {
            if (response.status == 401) {
              throw new Error('Code invalid');
            } else if (response.status == 404) {
              beginAuthFlow(window.selectedUid);
              throw new Error('Code expired');
            } else {
              codeError("Server error");
              throw new Error('Server error');
            }
          } else {
            response.text()
            .then(function(secret) {
              document.cookie = "secret=" + secret;
              window.location.replace("/");
            })
            .catch(function(error) {
              console.log(error);
              codeError("Network error");
            });
          }
        })
        .catch(error => {
          Swal.showValidationMessage(
            'Auth failed: ' + error.toString()
          )
        })
    },
    allowOutsideClick: () => !Swal.isLoading()
  }).then((result) => {
    if (result.isConfirmed) {
      Swal.fire({
        'icon': 'success',
        'text': 'Auth successful!',
        'timer': 1000
      })
    }
  })
}

function cancelCodeInput() {
  document.getElementById("codeentry").close();
}

function codeChanged(elem) {
  const errorElem = document.getElementById("codeerror");
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
    scrypt(newCode + window.selectedUid, salt, {
      N: 16384, r: 8, p: 1, dkLen: 64, encoding: "base64"}, function(hashedCode) {
        
      }
    );
  }
}

function codeError(message) {
  Swal.fire({
    'icon': 'error',
    'text': message,
    'timer': 5000
  })
}
