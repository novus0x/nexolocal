/********************** Converter **********************/
export function num_to_string(num, query_selector_identifier) {
    const Unidades = (n) => {
        const u = ["", "UN", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE"];
        return u[n];
    };

    const Decenas = (n) => {
        if (n < 10) return Unidades(n);
        if (n >= 10 && n < 20) {
            const especiales = ["DIEZ", "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE", "DIECISEIS", "DIECISIETE", "DIECIOCHO", "DIECINUEVE"];
            return especiales[n - 10];
        }
        if (n >= 20 && n < 30) {
            return n === 20 ? "VEINTE" : "VEINTI" + Unidades(n % 20);
        }

        const d = ["", "", "", "TREINTA", "CUARENTA", "CINCUENTA", "SESENTA", "SETENTA", "OCHENTA", "NOVENTA"];
        const unidad = Unidades(n % 10);
        return unidad ? d[Math.floor(n / 10)] + " Y " + unidad : d[Math.floor(n / 10)];
    };

    const Centenas = (n) => {
        if (n === 100) return "CIEN";
        if (n < 100) return Decenas(n);
        const c = ["", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS", "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"];
        const resto = n % 100;
        return resto ? c[Math.floor(n / 100)] + " " + Decenas(resto) : c[Math.floor(n / 100)];
    };

    const Procesar_Seccion = (n, divisor, palabraSingular, palabraPlural) => {
        const cientos = Math.floor(n / divisor);
        const resto = n % divisor;
        let resultado = "";

        if (cientos > 0) {
            if (cientos === 1) resultado = palabraSingular;
            else resultado = Centenas(cientos) + " " + palabraPlural;
        }

        if (resto > 0) {
            resultado += (resultado ? " " : "") + Centenas(resto);
        }
        return resultado;
    };

    const Miles = (n) => {
        const miles = Math.floor(n / 1000);
        const resto = n % 1000;
        let resultado = "";

        if (miles === 1) resultado = "MIL";
        else if (miles > 1) resultado = Centenas(miles) + " MIL";

        const parteBaja = Centenas(resto);
        if (parteBaja) resultado += (resultado ? " " : "") + parteBaja;

        return resultado;
    };

    const Millones = (n) => {
        const millones = Math.floor(n / 1000000);
        const resto = n % 1000000;
        let resultado = "";

        if (millones === 1) resultado = "UN MILLON";
        else if (millones > 1) resultado = Centenas(millones) + " MILLONES";

        const parteBaja = Miles(resto);
        if (parteBaja) resultado += (resultado ? " " : "") + parteBaja;

        return resultado;
    };

    // --- Lógica Final ---
    const enteros = Math.floor(num);
    const centavos = Math.round((num - enteros) * 100);
    const strCentavos = centavos.toString().padStart(2, '0') + "/100 SOLES";

    if (enteros === 0) return `SON: CERO CON ${strCentavos}`;

    let letras = Millones(enteros);
    return `SON: ${letras} CON ${strCentavos}`;
}
