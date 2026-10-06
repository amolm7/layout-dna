declare const __SOLVER_URL__: string;

declare module "https://new.express.adobe.com/static/add-on-sdk/sdk.js" {
  const addOnUISdk: {
    ready: Promise<void>;
    instance: {
      runtime: {
        apiProxy(runtime: string): Promise<unknown>;
      };
    };
  };
  export default addOnUISdk;
}
