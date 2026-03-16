declare module 'react-syntax-highlighter' {
  export const Prism: any;
  export const PrismLight: any;
}

declare module 'react-syntax-highlighter/dist/esm/styles/prism' {
  export const vscDarkPlus: any;
}

declare module 'react-syntax-highlighter/dist/esm/languages/prism/*' {
  const languageModule: any;
  export default languageModule;
}
