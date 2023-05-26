function applyStyle(selector, hljs_class) {
    let e = $(selector)
    e.removeClass((index, className) => {
        return (className.match(/((^|\s)hljs-\S+)|(\S+_($|\s))/g) || []).join(" ");
    });
    e.addClass(hljs_class)
    // if (e.is("[class^='hljs'] [class$='_']")) {

    // }
    // if (e.hasClass())
}

$("head").addClass("hljs")
$("button").addClass("hljs")
$("select").addClass("hljs")
$("input").addClass("hljs")
$("textarea").addClass("hljs")


$("a").addClass("hljs-title function_")

$("[data-feather]").addClass("hljs-keyword")
applyStyle(".icon-anchor", "hljs-keyword")
// $(".icon-anchor").addClass("hljs-keyword")
$("h1").addClass("hljs-keyword")

$(".publisher-name").addClass("hljs-number")
applyStyle(".voted", "hljs-number")

$(".button2").addClass("hljs-title function_")

