/* GitHub Pages build config — points the static demo at the live AWS API.
   Login is JWT-only (POST /auth/login); no demo mode, no mock data. */
window.HMS_CONFIG = {
  apiBase: 'https://s5x2pju9d3.execute-api.us-east-1.amazonaws.com/prod',
  demoMode: false,
  devMock: false
};
