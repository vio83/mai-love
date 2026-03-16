import React, { useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { bootstrapRuntimeAutopilot } from './runtime/runtimeAutopilot';

function RuntimeBootstrap() {
  useEffect(() => {
    const dispose = bootstrapRuntimeAutopilot();
    return () => dispose?.();
  }, []);

  return <App />;
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <RuntimeBootstrap />
  </React.StrictMode>,
);
