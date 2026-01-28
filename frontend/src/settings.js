/*************** Modules ***************/
import dotenv from 'dotenv';

/*************** Initializations ***************/
dotenv.config();

/*************** settings ***************/
const settings = {
    port: process.env.PORT || 3000,
    token_name: process.env.TOKEN_NAME || "default_app_token_name",
    api_url: process.env.API_URL
}

/*************** Export ***************/
export default settings;
