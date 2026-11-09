/* GitHub Pages DEMO build config — this file exists ONLY on the gh-pages branch.
   The production build (redesign/premium-v2 / main) does NOT include it:
   there, demo mode and mock data stay OFF unless enabled in Settings.
   Here the demo is enabled by default so visitors can explore the full UI
   with sample data until the real AWS API is connected. */
window.HMS_CONFIG = Object.assign(window.HMS_CONFIG || {}, {
  demoMode: true,
  devMock: true
});
