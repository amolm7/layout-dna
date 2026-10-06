const path = require("path");
const webpack = require("webpack");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const CopyWebpackPlugin = require("copy-webpack-plugin");

module.exports = (_env, argv) => ({
  mode: argv.mode === "production" ? "production" : "development",
  devtool: "source-map",
  entry: {
    index: "./src/ui/index.tsx",
    code: "./src/documentSandbox/code.ts"
  },
  experiments: { outputModule: true },
  output: {
    path: path.resolve(__dirname, "dist"),
    module: true,
    filename: "[name].js",
    clean: true
  },
  externalsType: "module",
  externalsPresets: { web: true },
  externals: {
    "add-on-sdk-document-sandbox": "add-on-sdk-document-sandbox",
    "express-document-sdk": "express-document-sdk"
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: "src/index.html",
      scriptLoading: "module",
      excludeChunks: ["code"]
    }),
    new CopyWebpackPlugin({ patterns: [{ from: "manifest.json", to: "manifest.json" }] }),
    new webpack.DefinePlugin({
      __SOLVER_URL__: JSON.stringify(process.env.LAYOUT_DNA_SOLVER_URL || "http://127.0.0.1:8000")
    })
  ],
  module: {
    rules: [
      { test: /\.tsx?$/, use: "ts-loader", exclude: /node_modules/ },
      { test: /\.css$/, use: ["style-loader", "css-loader"] }
    ]
  },
  resolve: { extensions: [".tsx", ".ts", ".js", ".css"] },
  devServer: {
    host: "127.0.0.1",
    port: 5241,
    hot: true,
    headers: { "Access-Control-Allow-Origin": "*" },
    static: { directory: path.join(__dirname, "dist") }
  }
});
