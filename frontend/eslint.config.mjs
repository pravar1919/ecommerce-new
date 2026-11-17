import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    // jsx-a11y ships with eslint-config-next; raise its recommended rules to errors.
    rules: {
      "jsx-a11y/alt-text": "error",
      "jsx-a11y/anchor-is-valid": "error",
      "jsx-a11y/aria-props": "error",
      "jsx-a11y/aria-role": "error",
      "jsx-a11y/role-has-required-aria-props": "error",
      "jsx-a11y/label-has-associated-control": [
        "error",
        { assert: "either", controlComponents: ["Input", "Checkbox"] },
      ],
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }],
    },
  },
  {
    // Vendored React Bits sources stay untouched (wrapped in components/motion).
    files: ["src/components/vendor/**"],
    rules: {
      "react-hooks/exhaustive-deps": "off",
      "@typescript-eslint/no-explicit-any": "off",
      "react-hooks/refs": "off",
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/immutability": "off",
      "react-hooks/purity": "off",
    },
  },
  {
    files: ["tests/**"],
    rules: { "@next/next/no-img-element": "off", "jsx-a11y/alt-text": "off" },
  },
  globalIgnores([
    ".next/**",
    ".next-lighthouse/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    "src/lib/api/schema.d.ts",
    "src/lib/cn-tables.ts",
    "playwright-report/**",
    "test-results/**",
    "lighthouse/**",
  ]),
]);

export default eslintConfig;
