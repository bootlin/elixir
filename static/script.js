/* Tags menu filter */

var versions = document.querySelector('.versions')
var dropdown = document.querySelector('.select-projects')
var input = document.querySelector('.filter-input')
var sidebar = document.querySelector('.sidebar')
var nav = document.querySelector('.sidebar nav')
var results = document.querySelector('.filter-results')

var tags = {}
function getTags () {
  var list = document.querySelectorAll('.versions a')
  for (var i = 0, l = list.length; i < l; i++) {
    tags[list[i].innerText] = list[i].href
  }
}
getTags()

function displayFilter (filter) {
  var filtered = document.createDocumentFragment()
  var reg = new RegExp(filter, 'i')
  for (var key in tags) {
    if (tags.hasOwnProperty(key)) {
      var ok = false
      var h = key.replace(reg, function (_) {
        if (_) ok = true
        return '<strong>' + _ + '</strong>'
      })

      if (ok) {
        var a = document.createElement('a')
        a.href = tags[key]
        a.innerHTML = h
        filtered.appendChild(a)
      }
    }
  }
  results.innerHTML = ''
  results.appendChild(filtered)
}

input.oninput = function () {
  if (this.value === '') {
    versions.classList.remove('hide')
    results.innerHTML = ''
  } else {
    versions.classList.add('hide')
    displayFilter(this.value)
  }
}

// prevent chrome auto-scrolling to element
var arr = []
arr.forEach.call(document.querySelectorAll('input'), function(el) {
  el.onkeydown = function (e) {
    var before = wrapper.scrollTop
    function reset() {
      wrapper.scrollTop = before
    }
    window.requestAnimationFrame(reset)
    setTimeout(reset, 0)
  }
})


/* Tags menu tree */

// Expand/Collapse tree
versions.onclick = function (e) {
  if (e.target && e.target.nodeName == 'SPAN') {
    e.target.classList.toggle('active')
  }
}

var tag = document.querySelector('.version em')
var openMenu = document.querySelector('.open-menu')
var wrapper = document.querySelector('.wrapper')
openMenu.onclick = tag.onclick = function (e) {
  e.preventDefault()
  wrapper.classList.toggle('show-menu')
}
sidebar.onclick = function (e) {
  if (e.target === this || e.target.classList.contains('close-menu')) {
    wrapper.classList.remove('show-menu')
  }
}


/* Linenumbers navigation */
document.querySelector('.go-top').onclick = function() {
  wrapper.scrollTop = 0
  wrapper.scrollLeft = 0
}

// When using linenumbers's anchor
// it jump the line a the top of the page
// and it's hidden under the fixed topbar element.
// To prevent this let's jump to a few lines behind the top

// This will capture hash changes while on the page
function offsetAnchor(e) {
  if (e && e.preventDefault) e.preventDefault()
  if (location.hash.length !== 0) {
    var el = document.querySelector(location.hash)
    if (el) {
      var offsetTop = el.offsetTop
      wrapper.scrollTop = offsetTop < 100 ? 200 : offsetTop + 100
    }
  }
}
window.onhashchange = offsetAnchor

// This is here so that when you enter the page with a hash,
// it can provide the offset in that case too.
window.requestAnimationFrame(offsetAnchor)

// Parses URL hash (anchor) in format La-Lb where a and b are line numbers,
// highlights line numbers, scrolls to first line number in range
function handleLineRange(hashStr) {
  const hash = hashStr.substring(1).split("-");
  if (hash.length != 2) {
    return;
  }

  const firstLineElement = document.getElementById(hash[0]);
  const lastLineElement = document.getElementById(hash[1]);
  if (firstLineElement === undefined || lastLineElement === undefined) {
    return;
  }

  highlightFromTo(firstLineElement, lastLineElement);
  firstLineElement.scrollIntoView();
}

// Highlights line number elements from firstLineElement to lastLineElement
function highlightFromTo(firstLineElement, lastLineElement) {
  let line = firstLineElement.parentNode;
  const afterLastLineElement = lastLineElement.parentNode.nextElementSibling;
  while (line !== null && line != afterLastLineElement) {
    line.firstChild.classList.add("line-highlight");
    line = line.nextElementSibling;
  }
  return true;
}

// Sets up listeners element that contains line numbers to handle
// shift-clicks for range highlighting
function setupLineRangeHandlers() {
  // Check if page contains the element with line numbers
  // If not, then likely script is not executed in context of the source page
  const linenodiv = document.querySelector(".linenodiv");
  if (linenodiv === null) {
    return;
  }

  let rangeStart, rangeEnd;
  linenodiv.addEventListener("click", ev => {
    if (ev.ctrlKey || ev.metaKey) {
      return;
    }
    ev.preventDefault();

    // Handler is set on the element that contains all line numbers, check if the
    // event is directed at an actual line number element
    const el = ev.target;
    if (typeof(el.id) !== "string" || el.id[0] !== "L" || el.tagName !== "A") {
      return;
    }

    // Remove range highlight
    const highlightElements = Array.from(document.getElementsByClassName("line-highlight"));
    for (let el of highlightElements) {
      el.classList.remove("line-highlight");
    }

    if (rangeStart === undefined || !ev.shiftKey) {
      rangeStart = el;
      rangeStart.classList.add("line-highlight");
      rangeEnd = undefined;
      window.location.hash = rangeStart.id;
    } else if(ev.shiftKey) {
      if (rangeEnd === undefined) {
        rangeEnd = el;
        highlightFromTo(rangeStart, rangeEnd);
        window.location.hash = `${rangeStart.id}-${rangeEnd.id}`;
      } else {
        let rangeStartNumber = parseInt(rangeStart.id.substring(1));
        let rangeEndNumber = parseInt(rangeEnd.id.substring(1));
        const elNumber = parseInt(el.id.substring(1));
        console.assert(!isNaN(rangeStartNumber) && !isNaN(rangeEndNumber) && !isNaN(elNumber),
          "Elements to highlight have invalid numbers in ids");

        // Swap range elements if rangeStartNumber < rangeEndNumber
        if (rangeStartNumber > rangeEndNumber) {
          const rangeTmp = rangeStart;
          rangeStart = rangeEnd;
          rangeEnd = rangeTmp;

          const numberTmp = rangeStartNumber;
          rangeStartNumber = rangeEndNumber;
          rangeEndNumber = numberTmp;
        }

        if (elNumber < rangeStartNumber) {
          // Expand if element above range
          rangeStart = el;
        } else if (elNumber > rangeEndNumber) {
          // Expand if element below range
          rangeEnd = el;
        } else {
          // Shrink moving the edge that's closest to the selection.
          // Move end if center was selected.
          const distanceFromStart = Math.abs(rangeStartNumber-elNumber);
          const distanceFromEnd = Math.abs(rangeEndNumber-elNumber);
          if (distanceFromStart < distanceFromEnd) {
            rangeStart = el;
          } else if (distanceFromStart > distanceFromEnd) {
            rangeEnd = el;
          } else {
            rangeEnd = el;
          }
        }

        highlightFromTo(rangeStart, rangeEnd);
        window.location.hash = `${rangeStart.id}-${rangeEnd.id}`;
      }
    }
  });
}

// recalculate scroll when page is fully loaded
// in case of slow rendering very long pages.
window.onload = function () {
  window.requestAnimationFrame(offsetAnchor)

  handleLineRange(window.location.hash);
  setupLineRangeHandlers();

  // fix incorrectly issued 301 redirect
  // https://developer.mozilla.org/en-US/docs/Web/API/Request/cache
  // https://developer.mozilla.org/en-US/docs/Web/API/Request/redirect
  // TODO: remove after 10.2024
  let path = location.pathname.split('/');
  if (path.length == 4) {
    path[2] = 'latest';
    let newPath = path.join('/');
    fetch(newPath, {
        cache: 'reload',
        redirect: 'manual',
        // this is to make sure that varnish will cache the response,
        // by default fetch sends no-cache in both headers if cache='reload'
        headers: {'Cache-Control': 'max-age=86400', 'Pragma': ''}
    })
      .then(console.log)
      .catch(console.error);
  }
}
