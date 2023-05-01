const requestHLJSstyles = async () => {
    const response = await fetch("https://api.cdnjs.com/libraries/highlight.js?fields=assets");
    
    return await response.json().then(result => {
        return {
            "version": result.assets[0].version,
            "styles": result.assets[0].files.filter(fname => fname.split(".").at(-1) == "css")
        }
    })
}

const HLJS_STYLES = requestHLJSstyles().then(result => {
    let version = result.version;
    result.styles.forEach(style => {
        $("head").append(`<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/${version}/${style}" disabled>`);
    })
    return result.styles;
})


