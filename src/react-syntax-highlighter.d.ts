declare module 'react-syntax-highlighter' {
  import type { ComponentType } from 'react';
  export const Prism: ComponentType<Record<string, unknown>>;
  export const PrismLight: ComponentType<Record<string, unknown>> & {
    registerLanguage(name: string, language: unknown): void;
  };
}

declare module 'react-syntax-highlighter/dist/esm/styles/prism' {
  export const vscDarkPlus: Record<string, unknown>;
}

declare module 'react-syntax-highlighter/dist/esm/languages/prism/bash' {
  const lang: unknown;
  export default lang;
}

declare module 'react-syntax-highlighter/dist/esm/languages/prism/javascript' {
  const lang: unknown;
  export default lang;
}

declare module 'react-syntax-highlighter/dist/esm/languages/prism/json' {
  const lang: unknown;
  export default lang;
}

declare module 'react-syntax-highlighter/dist/esm/languages/prism/python' {
  const lang: unknown;
  export default lang;
}

declare module 'react-syntax-highlighter/dist/esm/languages/prism/typescript' {
  const lang: unknown;
  export default lang;
}
