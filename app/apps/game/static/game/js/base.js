function setFavicon() {
    const favicon = document.querySelector("#favicon");
    favicon.href = window.matchMedia("(prefers-color-scheme: dark)").matches ? "/static/blog/images/icons/fav/favicon-96x96.png" : "/static/blog/images/icons/fav/favicon-96x96-black.png";

    const faviconSVG = document.querySelector("#favicon-svg");
    faviconSVG.href = window.matchMedia("(prefers-color-scheme: dark)").matches ? "/static/blog/images/icons/fav/icon.svg" : "/static/blog/images/icons/fav/icon-black.svg";

    const faviconAndroid = document.querySelector("#favicon-android");
    faviconAndroid.href = window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "/static/blog/images/icons/fav/android-icon-192x192.png"
        : "/static/blog/images/icons/fav/android-icon-192x192-black.png";

    const faviconApple = document.querySelector('link[rel="apple-touch-icon"]');
    faviconApple.href = window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "/static/blog/images/icons/fav/apple-icon-180x180.png"
        : "/static/blog/images/icons/fav/apple-icon-180x180-black.png";
    faviconApple.type = "image/svg+xml";
}

document.addEventListener("DOMContentLoaded", () => {
    setFavicon();
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", setFavicon);
});
