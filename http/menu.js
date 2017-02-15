var color1 = '#565F68';
var color2 = '#88AA88';

function closeMenus()
{
    var elems = document.getElementsByClassName("menuitem");
    var i;
    for (i = 0; i < elems.length; i++)
    {
        elems[i].style.overflow = 'hidden';
        var mel = elems[i].getElementsByClassName("mel")[0];
        mel.style.background = color1;
    }
}

function closeSubMenus()
{
    var elems = document.getElementsByClassName("subsubmenu");
    var i;
    for (i = 0; i < elems.length; i++)
    {
        elems[i].style.display = 'none';
    }

    elems = document.getElementsByClassName("mel2");
    for (i = 0; i < elems.length; i++)
    {
        elems[i].style.background = color2;
    }
}

function menuCloser (event)
{
    if (!event.target.matches('.mel') && !event.target.matches('.mel2'))
    {
        closeMenus();
        closeSubMenus();
    }
}

function mf1 (elem)
{
    closeMenus();
    elem.style.overflow = 'visible';
    var child = elem.getElementsByClassName("mel")[0];
    child.style.background = 'black';
}

function mf2 (elem)
{
    closeSubMenus();
    var child = elem.getElementsByClassName("subsubmenu")[0];
    child.style.display = 'block';
    var child = elem.getElementsByClassName("mel2")[0];
    child.style.background = 'black';
}

window.onclick = menuCloser;
