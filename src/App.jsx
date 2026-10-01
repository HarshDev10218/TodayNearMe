import React from 'react';
import HomePage from './pages/HomePage';
import { LocationProvider } from './hooks/useLocation';

/**
 * Root App Component
 * Wraps the application with the central LocationProvider
 * so any component/page can consume the location layer.
 */
function App() {
  return (
    <LocationProvider>
      <HomePage />
    </LocationProvider>
  );
}

export default App;
