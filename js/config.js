/* GitHub Pages build config — this file exists ONLY on the gh-pages branch.
   The AWS backend is live now, so this build talks to the real API:
   login is JWT authentication (POST /auth/login) and all data is real.
   No demo mode, no mock data. */
window.HMS_CONFIG = Object.assign(window.HMS_CONFIG || {}, {
  apiBase: 'https://s5x2pju9d3.execute-api.us-east-1.amazonaws.com/prod',
  demoMode: false,
  devMock: false
});
