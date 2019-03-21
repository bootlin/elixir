/* Tags menu filter */

var versions = document.querySelector('.versions')
var dropdown = document.querySelector('.select-projects')

var div = document.createElement('div')
var button = document.createElement('button')
var a = document.createElement('a')
var span = document.createElement('span')
var input = document.createElement('input')
a.title = 'Close Menu'
a.className = 'close-menu icon-cross'
// a.innerText = 'Close Menu'
div.className = 'filter'
span.className = 'screenreader'
button.className = 'icon-filter'
input.placeholder = 'Filter tags'
span.innerText = 'Filter tags'

// As filtering happen on typing
// the filter button is just for decoration
button.tabIndex = -1

button.appendChild(span)
div.appendChild(input)
div.appendChild(button)
div.appendChild(a)
var sidebar = document.querySelector('.sidebar')
var detachDropdown = dropdown.parentElement.removeChild(dropdown)
div.insertBefore(detachDropdown, div.firstChild)
sidebar.insertBefore(div, sidebar.firstChild)


var nav = document.querySelector('.sidebar nav')
var results = document.createElement('div')
results.className = 'filter-results'
nav.appendChild(results)

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

function expandVersion (version) {
  var version = document.querySelector('.versions .active')
  if (version && version.parentNode) {
    var targ = version.parentNode.previousElementSibling
    while (targ && targ.tagName === 'SPAN') {
      targ.classList.add('active')
      targ = targ.parentNode.parentNode
      targ = targ.previousElementSibling
    }
  }
}

// Auto expand menu to display current version
window.setTimeout(expandVersion, 1)

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

// recalculate scroll when page is fully loaded
// in case of slow rendering very long pages.
window.onload = function () {
  window.requestAnimationFrame(offsetAnchor)
}
