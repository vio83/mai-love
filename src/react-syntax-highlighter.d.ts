import type { ComponentType } from 'react';

declare module 'react-syntax-highlighter' {
  export const Prism: ComponentType<Record<string, unknown>>;
  export const PrismLight: ComponentType<Record<string, unknown>>;
}

declare module 'react-syntax-highlighter/dist/esm/styles/prism' {
  export const vscDarkPlus: Record<string, unknown>;
}

declare module 'react-syntax-highlighter/dist/esm/languages/prism/*' {
  const languageModule: unknown;
  export default languageModule;
}
