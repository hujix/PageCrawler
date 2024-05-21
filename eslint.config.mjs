import antfu from "@antfu/eslint-config";

export default antfu(
  {
    stylistic: {
      semi: true,
      indent: 2,
      quotes: "double",
    },
    typescript: true, // enable TypeScript support
  },
  {
    rules: {
      curly: ["error", "all"],
    },
  },
);
