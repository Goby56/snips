const requestHLJSstyles = async () => {
    const response = await fetch("https://api.cdnjs.com/libraries/highlight.js?fields=assets");
    
    return await response.json().then(result => {
        return {
            "version": result.assets[0].version,
            "styles": result.assets[0].files.filter(fname => fname.split(".").at(-1) == "css")
        }
    })
}

function setColorThemePreference(theme) {
    window.localStorage.setItem("colorTheme", theme);
}

function getColorThemePreference() {
    return window.localStorage.getItem("colorTheme")
}

const HLJS_STYLES = requestHLJSstyles().then(result => {
    let version = result.version;
    let colorTheme = getColorThemePreference()
    if (!colorTheme) {
        setColorThemePreference(result.styles[0])
        colorTheme = result.styles[0]
    } 
    result.styles.forEach((style) => {
        let disabledAttr = colorTheme == style ? "" : "disabled"
        $("head").append(`
        <link rel="stylesheet" 
              href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/${version}/${style}" 
              ${disabledAttr}>`
        );
    })
    return result.styles;
})