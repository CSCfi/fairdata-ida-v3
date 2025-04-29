const appId = 'ida'
const path = require('path')
const webpackConfig = require('@nextcloud/webpack-vue-config')
const ESLintPlugin = require('eslint-webpack-plugin')
const StyleLintPlugin = require('stylelint-webpack-plugin')
const { execSync } = require('child_process')

const buildMode = process.env.NODE_ENV
const isDev = buildMode === 'development'
webpackConfig.devtool = isDev ? 'cheap-source-map' : 'source-map'
// webpackConfig.bail = false

webpackConfig.stats = {
	colors: true,
	modules: false,
}

webpackConfig.entry = {
	main: { import: path.join(__dirname, 'src', 'js', 'main.js'), filename: appId + '-main.js' },
	actions: { import: path.join(__dirname, 'src', 'js', 'actions.js'), filename: appId + '-actions.js' },
	utils: { import: path.join(__dirname, 'src', 'js', 'utils.js'), filename: appId + '-utils.js' },
	constants: { import: path.join(__dirname, 'src', 'js', 'constants.js'), filename: appId + '-constants.js' },
	ui: { import: path.join(__dirname, 'src', 'js', 'ui.js'), filename: appId + '-ui.js' },
	firstrunwizard: { import: path.join(__dirname, 'src', 'js', 'firstrunwizard.js'), filename: appId + '-firstrunwizard.js' },
}

// Add ESLint and StyleLint plugins
webpackConfig.plugins.push(
	new ESLintPlugin({
		extensions: ['js', 'vue'],
		files: 'src',
		failOnError: !isDev,
	})
)
webpackConfig.plugins.push(
	new StyleLintPlugin({
		files: 'src/**/*.{css,scss,vue}',
		failOnError: !isDev,
	}),
)

// Add a custom plugin for translation file generation
webpackConfig.plugins.push({
	apply: (compiler) => {
		compiler.hooks.beforeRun.tap('GenerateTranslationsPlugin', () => {
			try {
                console.log('');
                execSync('node src/l10n/generate-translation-files.js', { stdio: 'inherit' });
			} catch (err) {
				console.error('Error generating translation files:', err.message)
				if (!isDev) {
					// Fail the build if in production mode
					process.exit(1)
				}
			}
		})
	},
})

module.exports = webpackConfig
