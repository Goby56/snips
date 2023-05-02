$("#sign-in-button").on("click", e => {
    window.location = "/login/"
})

$("#sign-up-button").on("click", e => {
    window.location = "/register/"
})

$("#unauth-user-icon").on("click", e => {
    window.location = "/login/"
})

$("#auth-user-icon #auth-user-name").on("click", e => {
    window.location = "/profile/"
})

$("#share-snippets-button").on("click", e => {
    window.location = "/share/"
})

console.log(HLJS_STYLES)

let addStylesToDropdown = async () => {
    await HLJS_STYLES.then(result => {
        result.forEach(style => {
            let styleName = style.split("/").at(-1).slice(0, -8)
            $("#styles-dropdown").append(`<option value='${style}'>${styleName}</option`)
        })
    })
}

addStylesToDropdown()

// const styleRegex = "highlight\.js\/(\d|\.)+\/styles\/.+\.min\.css$";

function setColorThemePreference(theme) {
    window.localStorage.setItem("colorTheme", theme)
}

$("#styles-dropdown").on("change", function() {
    $("link[href*='highlight.js']").attr("disabled", true)
    $(`link[href*='${this.value}']`).attr("disabled", false)
    setColorThemePreference(this.value)
})