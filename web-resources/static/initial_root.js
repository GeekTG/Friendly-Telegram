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


//    Friendly Telegram Userbot
//    by GeekTG Team

function setApi() {
	'use strict';
	const elem = document.getElementById("api_hash");
	if (elem.classList.contains("is-invalid")) {
		return;
	}
	fetch("/setApi", {
		method: "PUT",
		body: elem.value + document.getElementById("api_id").value,
		credentials: "include"
	})
		.then(function (response) {
			if (!response.ok) {
				console.log(response);
				setApiFailed(elem);
			} else {
				setApiDone(elem);
			}
		})
		.catch(function (response) {
			console.log(response);
			setApiFailed(elem);
		});
}

function setApiFailed(elem) {
	'use strict';
	document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
		message: "Setting API configuration failed",
		timeout: 2000
	});
}

function setApiDone(elem) {
	'use strict';
	document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
		message: "API configuration set",
		timeout: 2000
	});
}


function sendCode(elem) {
	'use strict';
	fetch("/sendTgCode", {method: "POST", body: elem.value, credentials: "include"})
		.then(function (response) {
			if (!response.ok) {
				console.log(response);
				sendCodeFailed();
			} else {
				sendCodeSuccess(elem);
			}
		})
		.catch(function (error) {
			console.log(error);
			sendCodeFailed();
		});
}

function sendCodeFailed() {
	'use strict';
	document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
		message: "Sending authentication code failed.",
		timeout: 2000
	});
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
	const elem = document.getElementById("code")
	const errorElem = document.getElementById("codeerror")
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
		fetch("/tgCode", {
			method: "POST",
			body: elem.value + "\n" + document.getElementById("phone").value + "\n" + password,
			credentials: "include"
		})
			.then(function (response) {
				if (!response.ok) {
					console.log(response);
					if (response.status == 403) {
						codeError(elem, "Code invalid");
					} else if (response.status == 401) {
						// Code correct, 2FA required
						cancelCodeInput();
						startPasswordInput();
					} else if (response.status == 404) {
						// Code expired, must re-send code request. Close dialog and wait for user action.
						cancelCodeInput();
						cancelPasswordInput();
					} else {
						codeError(elem, "Server error");
					}
				} else {
					response.text()
						.then(function (secret) {
							document.cookie = "secret=" + secret;
							cancelCodeInput();
							cancelPasswordInput();
							codeError(elem, "Logged In")
						})
						.catch(function (error) {
							console.log(error);
							codeError(elem, "Network error");
						});
				}
			})
			.catch(function (error) {
				console.log(error);
				codeError(elem, "Network error");
			});
	}
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

function finishLogin() {
	'use strict';
	const elem = document.getElementById("heroku");
	document.getElementById("heroku_progress").style.display = "block";
	fetch("/finishLogin", {method: "POST", body: elem.value, credentials: "include"})
		.then(function (response) {
			if (!response.ok) {
				finishLoginFailed();
			} else {
				window.location.reload(true);
			}
		})
		.catch(function (response) {
			console.log(response);
			finishLoginFailed();
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
