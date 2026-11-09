/* GitHub Pages build config — points the static site at the live AWS API.
   Login is OTP + JWT (POST /auth/login, then /auth/verify-otp). */
window.HMS_CONFIG = {
  apiBase: 'https://7vh8ixexjf.execute-api.us-east-1.amazonaws.com/prod',
  demoMode: false,
  devMock: false
};
