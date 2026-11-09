/* GitHub Pages build config — points the static site at the live AWS API.
   Login is JWT-only (POST /auth/login); no demo mode, no mock data. */
window.HMS_CONFIG = {
  apiBase: 'https://7vh8ixexjf.execute-api.us-east-1.amazonaws.com/prod',
  demoMode: false,
  devMock: false
};
