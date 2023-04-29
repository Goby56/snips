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