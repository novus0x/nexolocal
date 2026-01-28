/*************** Create Params ***************/
export function create_params(obj) {
    const params = new URLSearchParams();

    Object.entries(obj).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
            if (Array.isArray(value)) {
                value.forEach(v => params.append(key, v));
            } else {
                params.append(key, value.toString());
            }
        }
    });

    return `?${params.toString()}`;
}
