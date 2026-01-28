/*************** Validate CSV File ***************/
export function is_csv(file) {
    if (!file) return false;

    const valid_mime = new Set([
        "text/csv",
        "application/vnd.ms-excel"
    ]);

    const name_ok = typeof file.originalname === "string" && file.originalname.toLowerCase().endsWith(".csv");

    const mime_ok = typeof file.mimetype === "string" && valid_mime.has(file.mimetype);

    if (name_ok && mime_ok) return true;

    return false;
}

