/*************** Get Scopes ***************/
export function get_scopes(permissions) {
    // Variables
    const scopes = {
        platform: false,
        company: false,
        user: false
    }

    // If permissions
    if (permissions) {
        scopes.platform = permissions.some(p => p.startsWith("platform.")),
        scopes.company = permissions.some(p => p.startsWith("company.")),
        scopes.user = permissions.some(p => p.startsWith("user."))
    }

    return scopes;
}
