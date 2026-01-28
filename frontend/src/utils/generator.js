/*************** Modules ***************/
import qr_code from 'qrcode'
import barcode from 'bwip-js';

import settings from '../settings.js';

/********************** SVG Generator **********************/
export async function svg_generator(value, type = "qrcode") {

    if (type == "qrcode") {
        const svg = await qr_code.toString(value, {
            type: "svg"
        });

        return svg;
    }

    if (type == "barcode") {
        const svg = await barcode.toSVG({
            bcid: "code128",
            text: value,
            scale: 2,
            height: 8,
            includetext: false,
            textxalign: "center",
        });

        return svg; 
    }

    return false;
};
