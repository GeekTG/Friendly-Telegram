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

