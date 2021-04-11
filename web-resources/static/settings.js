//    Friendly Telegram Userbot
//    by GeekTG Team
function updatePermissionSwitch(elem) {
	'use strict';
	setTimeout(function () {
		elem.disabled = true;
	}, 0);
	const bit = elem.id.substring(7, elem.id.indexOf("_")).replace(/-/g, "_").toUpperCase();
	fetch("/setPermissionSet", {
		method: "PATCH",
		body: JSON.stringify({bit: bit, state: elem.checked, mid: elem.dataset.mid - 1, func: elem.dataset.func}),
		credentials: "include"
	})
		.then(function (response) {
			if (!response.ok) {
				console.log(response);
				setConfigFailed(elem);
			} else {
				setConfigDone(elem);
			}
		})
		.catch(function (response) {
			console.log(response);
			setConfigFailed(elem);
		});
}

function setGroup(elem, group) {
	'use strict';
	fetch("/setGroup", {method: "PUT", body: JSON.stringify({group: group, users: elem.value}), credentials: "include"})
		.then(function (response) {
			if (!response.ok) {
				console.log(response);
				setConfigFailed(elem);
			} else {
				setConfigDone(elem);
			}
		})
		.catch(function (response) {
			console.log(response);
			setConfigFailed(elem);
		});
}

function setConfigFailed(elem) {
	'use strict';
	elem.value = elem.dataset.currentvalue;
	elem.checked = !elem.checked;
	elem.disabled = false;
	document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
		message: "Setting configuration value failed",
		timeout: 2000
	});
}

function setConfigDone(elem) {
	'use strict';
	if (elem.value === "" && elem.type == "text") {
		elem.value = elem.dataset.defaultvalue;
		if (elem.value !== "") {
			elem.parentElement.classname += " is-dirty";
		}
	}
	elem.disabled = false;
	elem.dataset.currentvalue = elem.value;
	document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
		message: "Configuration value set",
		timeout: 2000
	});
}

