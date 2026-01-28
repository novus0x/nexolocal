/*************** Modules ***************/
import multer from 'multer';

/*************** Upload ***************/
const upload = multer({
    storage: multer.memoryStorage(),
    limits: {

    }
});

/*************** Export ***************/
export default upload;
