function serializeObject(form) {
    let obj = {}
    for (let kv of form.serializeArray()) {
        obj[kv["name"]] = kv["value"]
    }
    return obj
}

hljs.listLanguages().forEach(lang => {
    $("#language-dropdown").append(`<option value="${lang}">${lang}</option>`)
})

function renderPreview(title, code, desc, lang) {
    if (!title) title = "I am bad with titles"
    if (lang != "auto") {
        lang = "language-" + lang
    } else {
        lang = ""
    }
    if (desc) desc = `<p class="description">${desc}</p>`
    $("#submit-container").append(`
        <div id="snippet-preview">
            <div class="post">
                <p class="title">${title}</p>
                <div class="snippet">
                    <pre><code class="snippet-container ${lang}">
                    </code></pre>
                    <div class="description-outer">
                        <div class="description-inner">
                            ${desc}
                        </div>
                    </div>
                </div>
            </div>  
        </div>`)
    $(".snippet-container").text(code)
    hljs.highlightAll();
}

$("#preview-button").on("click", e => {
    if ($(e.currentTarget).text() == "Preview") {
        let data = serializeObject($("#editor-form"))

        let selectedLanguage = $("#language-dropdown").find(":selected").val()
        renderPreview(data.title, data.snippet, data.description, selectedLanguage)

        $("#snippet-editor").addClass("hide")
        $("#language-dropdown").addClass("hide")

        $(e.currentTarget).text("Edit")
    } else {
        $("#snippet-preview").remove()

        $("#snippet-editor").removeClass("hide")
        $("#language-dropdown").removeClass("hide")

        $(e.currentTarget).text("Preview")
    }
})

$("#post-button").on("click", e => {
    $("#editor-form").trigger("submit")
})

// $("#editor-form").on("submit", e => {
    
// })