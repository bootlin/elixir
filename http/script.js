function throttle(fn, threshhold) {
  threshhold || (threshhold = 150)
  var last, deferTimer
  return function () {
    var now = +new Date
    if (last && now < last + threshhold) {
      clearTimeout(deferTimer)
      deferTimer = setTimeout(function () {
        last = now
        fn()
      }, threshhold)
    } else {
      last = now
      fn()
    }
  };
}

/* Fixed topbar and tag menu when header is hidden by scroll */

// Cross browser scrollTop position
var getScrollTop
if (typeof window.pageYOffset != 'undefined') {
  getScrollTop = function () { return window.pageYOffset }
} else {
  if (document.documentElement.clientHeight)
    getScrollTop = function () { return document.documentElement.scrollTop }
  else getScrollTop = function () { return document.body.scrollTop }
}

var bodyClassName = ''
function checkScroll () {
  var isHiddenHeader = getScrollTop() >= 200 ? 'hidden-header' : ''
  if (isHiddenHeader !== bodyClassName) {
    document.body.className = bodyClassName = isHiddenHeader
  }
}

// If header is present
if (document.querySelector('.header')) {
  window.onscroll = throttle(checkScroll, 10)
  checkScroll()
} else {
  document.body.className = 'hidden-header'
}


/* Tags menu filter */

var versions = document.querySelector('.versions')

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
  console.log(e.target.className)
  if (e.target === this || e.target.classList.contains('close-menu')) {
    wrapper.classList.remove('show-menu')
  }
}


/* Linenumbers navigation */

// When using linenumbers's anchor
// it jump the line a the top of the page
// and it's hidden under the fixed topbar element.
// To prevent this let's make the jump at half the height
// of the screen

var height
var middle

// cross browser height calculation
function getHeight () {
  height = window.innerHeight
    || document.documentElement.clientHeight
    || document.body.clientHeight
  middle = height / 2
}
window.onresize = getHeight
getHeight()

// This will capture hash changes while on the page
function offsetAnchor() {
  if (location.hash.length !== 0) {
    var rect = document.querySelector(location.hash).getBoundingClientRect()
    var elTop = rect.top + window.scrollY
    window.scrollTo(window.scrollX, elTop - middle)
  }
}
window.onhashchange = offsetAnchor

// This is here so that when you enter the page with a hash,
// it can provide the offset in that case too. Having a timeout
// seems necessary to allow the browser to jump to the anchor first.
window.setTimeout(offsetAnchor, 1)

// recalculate scroll when page is fully loaded
// in case of slow rendering very long pages.
window.onload = function () {
  getHeight()
  offsetAnchor()
}
