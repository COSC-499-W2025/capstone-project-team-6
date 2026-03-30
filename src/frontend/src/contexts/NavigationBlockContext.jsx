import React, { createContext, useContext, useState, useCallback } from 'react';

const NavigationBlockContext = createContext({
  isNavigationBlocked: false,
  setNavigationBlocked: () => {},
});

export const NavigationBlockProvider = ({ children }) => {
  const [isNavigationBlocked, setBlocked] = useState(false);

  const setNavigationBlocked = useCallback((blocked) => {
    setBlocked(blocked);
  }, []);

  return (
    <NavigationBlockContext.Provider value={{ isNavigationBlocked, setNavigationBlocked }}>
      {children}
    </NavigationBlockContext.Provider>
  );
};

export const useNavigationBlock = () => useContext(NavigationBlockContext);
