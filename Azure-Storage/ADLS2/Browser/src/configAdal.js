import { AuthenticationContext, adalFetch, withAdalLogin } from 'react-adal';

import Config from './config.js';
 
export const adalConfig = {
  tenant: Config.tenantId,
  clientId: Config.clientId,
  endpoints: {
    api: 'https://storage.azure.com', // https://storage.azure.com, https://graph.windows.net
  },
  cacheLocation: 'localStorage',
};
 
export const authContext = new AuthenticationContext(adalConfig);
 
export const adalApiFetch = (fetch, url, options) =>
  adalFetch(authContext, adalConfig.endpoints.api, fetch, url, options);
 
export const withAdalLoginApi = withAdalLogin(authContext, adalConfig.endpoints.api);
