module.exports = {
    globals: {
        appVersion: true
    },
    parserOptions: {
        requireConfigFile: false
    },
    extends: [
        '@nextcloud'
    ],
    rules: {
        'jsdoc/require-jsdoc': 'off',
        'jsdoc/tag-lines': 'off',
        'vue/first-attribute-linebreak': 'off',
        'vue/no-lone-template': 'off',
        'vue/singleline-html-element-content-newline': 'off',
        'vue/order-in-components': 'off',
        'vue/attributes-order': 'off',
        'vue/html-indent': 'off',
        'vue/max-attributes-per-line': 'off',
        'import/extensions': 'off',
        'semi': 'off',
        'indent': 'off',
        'no-console': 'off',
        //'no-undef': 'off',
        'no-unused-vars': 'off',
        'no-multi-spaces': 'off',
        'object-shorthand': 'off',
        'no-extraneous-import': 'off',
    },
}
