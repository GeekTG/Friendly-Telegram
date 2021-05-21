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

var salt = "";

function beginAuthFlow(uid) {
	'use strict';
	fetch("/sendCode", {method: "POST", body: uid})
		.then(function (response) {
			if (!response.ok) {
				sendCodeFailed();
			} else {
				response.text().then(function (resp) {
					salt = resp;
					sendCodeSuccess(uid);
				});
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

function sendCodeSuccess(uid) {
	'use strict';
	window.selectedUid = uid;
	document.getElementById("codeentry").showModal();
}

function cancelCodeInput() {
	'use strict';
	document.getElementById("codeentry").close();
}

function codeChanged(elem) {
	'use strict';
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
				N: 16384, r: 8, p: 1, dkLen: 64, encoding: "base64"
			}, function (hashedCode) {
				fetch("/code", {method: "POST", body: hashedCode + "\n" + window.selectedUid})
					.then(function (response) {
						if (!response.ok) {
							if (response.status == 401) {
								codeError(elem, "Code invalid");
							} else if (response.status == 404) {
								codeError(elem, "Code expired");
								beginAuthFlow(window.selectedUid);
							} else {
								codeError(elem, "Server error");
							}
						} else {
							response.text()
								.then(function (secret) {
									document.cookie = "secret=" + secret;
									document.getElementById("codeentry").close();
									window.location.replace("/");
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
		);
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
