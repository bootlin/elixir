"use strict";

function identUrl(project, ident, version, family) {
  return `/api/ident/${project}/${ident}?version=${version}&family=${family}`;
}

/*
  "definitions": [
    {
      "path": "arch/x86_64/kstat.h",
      "line": 1,
      "type": "struct"
    }
  ],
  "references": [
    {
      "path": "src/stat/fstatat.c",
      "line": "78,142",
      "type": null
    }
  ],
  "documentations": [
    {
      "path": "Documentation/devicetree/bindings/arm/arm,cci-400.yaml",
      "line": "15,17,18",
      "type": null
    }
  ]
*/

function generateSymbolDefinitionsHTML(symbolDefinitions, peeks, project, version) {
  let result = "";
  let typesCount = {};
  let previous_type = "";

  if(symbolDefinitions.length == 0) {
    return '<h2>No definitions found in the database</h2>';
  }

  for(let symbolDefinition of symbolDefinitions) {
    if (symbolDefinition.type in typesCount) {
      typesCount[symbolDefinition.type] += 1;
    } else {
      typesCount[symbolDefinition.type] = 1;
    }
  }

  for (let sd of symbolDefinitions) {
    if (sd.type != previous_type) {
      if (previous_type != '') {
        result += '</ul>';
      }
      result += '<h2>Defined in ' + typesCount[sd.type].toString() + ' files as a ' + sd.type + ':</h2>';
      result += '<ul>';
      previous_type = sd.type;
    }
    let ln = sd.line.toString().split(',');
    if (ln.length == 1 && !peeks) {
      let n = ln[0];
      result += `<li><a href="/${project}/${version}/source/${sd.path}#L${n}"><strong>${sd.path}</strong>, line ${n} <em>(as a ${sd.type})</em></a>`;
    } else {
      if (symbolDefinitions.length > 100) {
        let n = ln.length;
        result += `<li><a href="/${project}/${version}/source/${sd.path}#L${ln[0]}"><strong>${sd.path}</strong>, <em>${n} times</em> <em>(as a ${sd.type})</em></a>`;
      } else {
        result += `<li><a href="/${project}/${version}/source/${sd.path}#L${ln[0]}"><strong>${sd.path}</strong> <em>(as a ${sd.type})</em></a>`;
        result += '<ul>';
        for(let n of ln) {
          result += `<li><a href="/${project}/${version}/source/${sd.path}#L${n}"><span>line ${n}</span>`;
          let srcLine = peeks?.[sd.path]?.[n];
          if(srcLine) {
            let tag = document.createElement("pre");
            tag.textContent = srcLine;
            result += tag.outerHTML;
          }
          result += '</a></li>'
        }
        result += '</ul>';
      }
    }
  }
  result += '</ul>';

  return result;
}

function generateSymbolReferencesHTML(symbolReferences, peeks, project, version) {
  let result = "";

  if(symbolReferences.length == 0) {
    return '<h2>No references found in the database</h2>';
  }

  result += '<h2>Referenced in ' + symbolReferences.length.toString() + ' files:</h2>';
  result += '<ul>';
  for (let sr of symbolReferences) {
    let ln = sr.line.split(',');
    if (ln.length == 1 && !peeks) {
      let n = ln[0];
      result += `<li><a href="/${project}/${version}/source/${sr.path}#L${n}"><strong>${sr.path}</strong>, line ${n}</a>`;
    } else {
      if(symbolReferences.length > 100) {
        let n = ln.length;
        result += `<li><a href="/${project}/${version}/source/${sr.path}#L${ln[0]}"><strong>${sr.path}</strong>, <em>${n} times</em></a>`;
      } else {
        result += `<li><a href="/${project}/${version}/source/${sr.path}#L${ln[0]}"><strong>${sr.path}</strong></a>`;
        result += '<ul>'
        for(let n of ln) {
          result += `<li><a href="/${project}/${version}/source/${sr.path}#L${n}"><span>line ${n}</span>`
          let srcLine = peeks?.[sr.path]?.[n];
          if (srcLine) {
            let tag = document.createElement("pre");
            tag.textContent = srcLine;
            result += tag.outerHTML;
          }
          result += '</a></li>'
        }
        result += '</ul>'
      }
    }
  }
  result += '</ul>'
  return result;
}

function generateDocCommentsHTML(symbolDocComments, project, version) {
  let result = "";
  if (symbolDocComments.length == 0) {
    return result;
  }
  result += '<h2>Documented in ' + symbolDocComments.length.toString() + ' files:</h2>';
  result += '<ul>';
  for(let sd of symbolDocComments) {
    let ln = sd.line.split(',');
    if(ln.length == 1) {
      let n = ln[0];
      result += `<li><a href="/${project}/${version}/source/${sd.path}#L${n}"><strong>${sd.path}</strong>, line ${n}</a>`;
    } else {
      if(symbolDocComments.length > 100) {
        let n = ln.length;
        result += `<li><a href="/${project}/${version}/source/${sd.path}#L${ln[0]}"><strong>${sd.path}</strong>, <em>${n} times</em></a>`;
      } else {
        result += `<li><a href="/${project}/${version}/source/${sd.path}#L${ln[0]}"><strong>${sd.path}</strong></a>`;
        result += '<ul>';
        for(let n of ln) {
          result += `<li><a href="/${project}/${version}/source/${sd.path}#L${n}">line ${n}</a>`;
        }
        result += '</ul>';
      }
    }
  }
  result += '</ul>';
  return result;
}

function generateReferencesHTML(data, project, version) {
  let symbolDefinitions = data["definitions"];
  let symbolReferences = data["references"];
  let symbolDocumentations = data["documentations"];
  let peeks = data["peeks"];
  return '<div class="lxrident">' +
    generateDocCommentsHTML(symbolDocumentations, project, version) +
    generateSymbolDefinitionsHTML(symbolDefinitions, peeks, project, version) +
    generateSymbolReferencesHTML(symbolReferences, peeks, project, version) +
    '</div>';
}

function showPopup(referencePopup, target) {
  let targetRect = target.getBoundingClientRect();
  let x = target.offsetLeft;
  let y = target.offsetTop + targetRect.height;

  referencePopup.style.visibility = "visible";
  referencePopup.style.display = "block";
  referencePopup.style.left = `${x}px`;
  referencePopup.style.top = `${y}px`;
  referencePopup.scrollTop = 0;
  referencePopup.scrollLeft = 0;

  let referenceRect = referencePopup.getBoundingClientRect();

  if((referenceRect.top + referenceRect.height) > window.innerHeight) {
    referencePopup.style.top = `${target.offsetTop - referenceRect.height}px`;
  }

  if((referenceRect.left + referenceRect.width) > window.innerWidth) {
    x -= ((referenceRect.left + referenceRect.width) - window.innerWidth);
    referencePopup.style.left = `${x}px`;
  }
}

function hidePopup(referencePopup) {
  referencePopup.style.visibility = "hidden";
  referencePopup.style.display = "none";
}

document.addEventListener("DOMContentLoaded", _ => {
  let referencePopup = document.getElementById("reference-popup");
  let loadingPopup = document.getElementById("loading-popup");
  var loadingTimer;
  var popupId = 0;
  var abortController;

  document.body.querySelectorAll(".ident").forEach(el => {
    el.addEventListener("click", async ev => {
      if (ev.ctrlKey || ev.metaKey || ev.shiftKey) {
        return;
      }
      ev.preventDefault();

      let splitPath = ev.target.pathname.split("/");
      let [_, project, version, family, _i, ident] = splitPath;

      let currentPopupId = ++popupId;

      if(abortController !== undefined)
        abortController.abort();
      abortController = new AbortController();

      hidePopup(loadingPopup);
      clearTimeout(loadingTimer);
      loadingTimer = setTimeout(() => {
        showPopup(loadingPopup, ev.target);
      }, 200);

      function cancelLoadingPopup() {
        if (currentPopupId == popupId) {
          hidePopup(loadingPopup);
          clearTimeout(loadingTimer);
        }
      }

      try {
        let result = await fetch(identUrl(project, ident, version, family),
          { signal: abortController.signal })
          .then(r => r.json());

        if(currentPopupId == popupId) {
          referencePopup.innerHTML = generateReferencesHTML(result, project, version);
          showPopup(referencePopup, ev.target);
        }
      } catch(e) {
        if(e.name !== "AbortError") {
          cancelLoadingPopup();
          throw e;
        }
      }

      cancelLoadingPopup();
    });
  });

  referencePopup.addEventListener("click", ev => ev.stopPropagation());

  document.body.addEventListener("click", _ => hidePopup(referencePopup));

  document.body.addEventListener("keydown", ev => {
    if (ev.key === "Escape") {
      hidePopup(referencePopup);
    }
  });
});
