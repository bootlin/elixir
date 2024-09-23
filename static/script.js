/* Tags menu filter */

// Get a dictionary of tag name -> tag link from HTML
function getTags() {
  const tags = {};
  const list = document.querySelectorAll('.versions a');
  for (const el of list) {
    tags[el.innerText.trim()] = el.href;
  }
  return tags;
}

// Generate tag search results based on input
// filter: current filter input text
// tags: dictionary of tag name -> tag link
function generateResults(filter, tags) {
  const searchResults = document.createDocumentFragment();
  const filterRegex = new RegExp(filter, 'i');

  for (let key in tags) {
    if (tags.hasOwnProperty(key)) {
      let tagFound = false;
      const tagHighlight = key.replace(filterRegex, result => {
        if (result) tagFound = true;
        return '<strong>' + result + '</strong>';
      })

      if (tagFound) {
        const tagLink = document.createElement('a');
        tagLink.href = tags[key];
        tagLink.innerHTML = tagHighlight;
        searchResults.appendChild(tagLink);
      }
    }
  }

  return searchResults;
}

// Setup tags filter input
function setupVersionsFilter() {
  const input = document.querySelector('.filter-input');
  const results = document.querySelector('.filter-results');
  const versions = document.querySelector('.versions');
  const tags = getTags();

  input.addEventListener('input', e => {
    if (e.target.value === '') {
      versions.classList.remove('hide');
      results.innerHTML = '';
    } else {
      versions.classList.add('hide');
      results.innerHTML = '';
      results.appendChild(generateResults(e.target.value, tags));
    }
  });
}

// Setup expanding/collapsing versions tree on click
function setupVersionsTree() {
  const versions = document.querySelector('.versions');
  versions.addEventListener('click', e => {
    if (e.target && e.target.nodeName == 'SPAN') {
      e.target.classList.toggle('active')
    }
  });
}

function isWidescreen() {
  return getComputedStyle(document.documentElement).getPropertyValue('--is-widescreen') === 'true';
}

// Toggles sidebar visibility, handles widescreen and mobile layouts
function toggleMenu() {
  const isWidescreen = getComputedStyle(document.documentElement).getPropertyValue('--is-widescreen') === 'true';
  if(isWidescreen) {
    const hasShowMenu = document.documentElement.classList.contains('show-menu');
    window.localStorage.setItem('show-sidebar', !hasShowMenu);
    document.documentElement.classList.toggle('show-menu');
  } else {
    document.documentElement.classList.toggle('show-menu-mobile');
  }
}

// Setup sidebar hamburger menu button, close button and mobile sidebar backdrop events
function setupSidebarSwitch() {
  const tag = document.querySelector('.version em');
  const openMenu = document.querySelector('.open-menu');
  const sidebar = document.querySelector('.sidebar');

  // toggle on hamburger menu click
  openMenu.addEventListener('click', e => {
    e.preventDefault();
    toggleMenu();
  });

  // toggle on footer tag icon click
  tag.addEventListener('click', e => {
    e.preventDefault();
    toggleMenu();
  });

  // close on close-menu/backdrop click
  sidebar.addEventListener('click', e => {
    if (e.target === sidebar && isWidescreen()) {
      document.documentElement.classList.remove('show-menu');
      window.localStorage.setItem('show-sidebar', false);
    } else if (e.target === sidebar || e.target.classList.contains('close-menu')) {
      document.documentElement.classList.remove('show-menu-mobile');
    }
  });
}

// Parses URL hash (anchor) in format La-Lb where a and b are line numbers,
// highlights range between (and including) line numbers, scrolls to the
// first line number in range.
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
  let firstLine = parseInt(firstLineElement.id.substring(1));
  let lastLine = parseInt(lastLineElement.id.substring(1));
  console.assert(!isNaN(firstLine) && !isNaN(lastLine),
    "Elements to highlight have invalid numbers in ids");

  console.assert(firstLine < lastLine, "first highlight line is after last highlight line");

  const firstCodeLine = document.getElementById(`codeline-${ firstLine }`);
  const lastCodeLine = document.getElementById(`codeline-${ lastLine }`);

  addClassToRangeOfElements(firstLineElement.parentNode, lastLineElement.parentNode, "line-highlight");
  addClassToRangeOfElements(firstCodeLine, lastCodeLine, "line-highlight");
}

function addClassToRangeOfElements(first, last, class_name) {
  let element = first;
  const elementAfterLast = last !== null ? last.nextElementSibling : null;
  while (element !== null && element != elementAfterLast) {
    element.classList.add(class_name);
    element = element.nextElementSibling;
  }
}

// Sets up listeners on element that contains line numbers to handle
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
      }

      let rangeStartNumber = parseInt(rangeStart.id.substring(1));
      let rangeEndNumber = parseInt(rangeEnd.id.substring(1));
      const elNumber = parseInt(el.id.substring(1));
      console.assert(!isNaN(rangeStartNumber) && !isNaN(rangeEndNumber) && !isNaN(elNumber),
        "Elements to highlight have invalid numbers in ids");

      // Swap range elements to support "#L2-L1" format. Postel's law.
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
  });
}

/* Other fixes */

// prevent chrome from auto-scrolling to input elements
function setupAutoscrollingPrevention() {
  const wrapper = document.querySelector('.wrapper');
  Array.prototype.forEach.call(document.querySelectorAll('input'), el => {
    el.addEventListener('keydown', _ => {
      const before = wrapper.scrollTop;
      const reset = () => wrapper.scrollTop = before;
      window.requestAnimationFrame(reset);
      setTimeout(reset, 0);
    });
  });
}

// Scrolls the page after each anchor change to prevent selected line from
// hiding under the topbar after a line number click.
function setupAnchorOffsetHandler() {
  const wrapper = document.querySelector('.wrapper');

  const anchorChangeHandler = e => {
    if (e && e.preventDefault) e.preventDefault();
    if (location.hash.length !== 0) {
      const el = document.querySelector(location.hash);
      if (el) {
        const offsetTop = el.offsetTop;
        wrapper.scrollTop = offsetTop < 100 ? 200 : offsetTop + 100;
      }
    }
  };

  window.requestAnimationFrame(anchorChangeHandler);
  window.addEventListener('hashchange', anchorChangeHandler);
}

function setupGoToTop() {
  const wrapper = document.querySelector('.wrapper');
  const goToTop = document.querySelector('.go-top');

  goToTop.addEventListener('click', e => {
    wrapper.scrollTop = 0;
    wrapper.scrollLeft = 0;
  });
}

// fix incorrectly issued 301 redirect
// https://developer.mozilla.org/en-US/docs/Web/API/Request/cache
// https://developer.mozilla.org/en-US/docs/Web/API/Request/redirect
// TODO: remove after 10.2024
function fix301() {
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

document.addEventListener('DOMContentLoaded', _ => {
  setupVersionsFilter();
  setupVersionsTree();
  setupSidebarSwitch();

  handleLineRange(window.location.hash);
  setupLineRangeHandlers();

  setupAutoscrollingPrevention();
  setupAnchorOffsetHandler();
  setupGoToTop();
  fix301();
});
