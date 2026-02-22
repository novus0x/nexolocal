/*************** Safe Return Path ***************/
export function get_safe_return_path(req, fallback = "/dashboard") {
    const referer = req.get("referer");

    if (!referer) return fallback;

    try {
        const url = new URL(referer);
        if (!url.pathname.startsWith("/")) return fallback;
        if (url.pathname.startsWith("/auth/verify-account")) return fallback;

        const path_with_query = `${url.pathname}${url.search || ""}`;
        return path_with_query || fallback;
    } catch {
        return fallback;
    }
}
